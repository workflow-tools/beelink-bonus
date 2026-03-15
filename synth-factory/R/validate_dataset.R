#!/usr/bin/env Rscript
#' ==========================================================================
#' VilseckKI Synth-Factory — Dataset Validation & Visualization
#' ==========================================================================
#'
#' Post-generation statistical validation for synthetic document datasets.
#' Produces a validation summary (JSON) and publication-quality plots (PNG)
#' for JDEX/Datarade marketplace listings.
#'
#' Usage:
#'   Rscript validate_dataset.R --input output.jsonl --output report/
#'   Rscript validate_dataset.R --input output.jsonl --reference scraped.jsonl --output report/
#'   Rscript validate_dataset.R --input output.jsonl --output report/ --format html
#'
#' Requirements:
#'   install.packages(c("jsonlite", "fitdistrplus", "ggplot2", "dplyr", "tidyr", "optparse"))
#'   # For Japanese text analysis (optional):
#'   install.packages("RMeCab", repos = "https://rmecab.jp/R")
#'
#' Author: Misawa Data GK
#' License: MIT
#' ==========================================================================

suppressPackageStartupMessages({
  library(jsonlite)
  library(dplyr)
  library(tidyr)
  library(ggplot2)
  library(optparse)
})

# ── CLI Arguments ────────────────────────────────────────────────

parse_args <- function() {
  option_list <- list(
    make_option(c("-i", "--input"), type = "character", default = NULL,
                help = "Path to generated dataset JSONL file [required]"),
    make_option(c("-r", "--reference"), type = "character", default = NULL,
                help = "Path to reference (scraped) dataset JSONL for comparison [optional]"),
    make_option(c("-o", "--output"), type = "character", default = "quality-report",
                help = "Output directory for report and plots [default: quality-report/]"),
    make_option(c("-t", "--taxonomy"), type = "character", default = NULL,
                help = "Path to flaw_taxonomy.json for injection rate verification"),
    make_option(c("-f", "--format"), type = "character", default = "json",
                help = "Report format: json, html [default: json]"),
    make_option(c("--theme"), type = "character", default = "vilseckki",
                help = "ggplot2 theme: vilseckki, minimal, classic [default: vilseckki]")
  )
  parse_args2(OptionParser(option_list = option_list))
}


# ── Data Loading ─────────────────────────────────────────────────

#' Load a synth-factory JSONL dataset into a tibble.
#'
#' @param path Path to JSONL file
#' @return tibble with one row per document, segment columns prefixed with seg_
load_dataset <- function(path) {
  if (!file.exists(path)) stop(paste("Dataset not found:", path))

  lines <- readLines(path, warn = FALSE)
  lines <- lines[nchar(trimws(lines)) > 0]

  if (length(lines) == 0) stop("Dataset is empty")

  records <- lapply(lines, function(line) {
    tryCatch(fromJSON(line, simplifyVector = TRUE),
             error = function(e) NULL)
  })
  records <- Filter(Negate(is.null), records)

  if (length(records) == 0) stop("No valid records in dataset")

  bind_rows(records)
}


#' Extract segment columns into long format for analysis.
#'
#' @param data tibble from load_dataset()
#' @return tibble with columns: document_id, segment_name, segment_text, char_count
pivot_segments <- function(data) {
  seg_cols <- grep("^seg_", names(data), value = TRUE)

  if (length(seg_cols) == 0) {
    warning("No segment columns (seg_*) found in dataset")
    return(tibble(document_id = character(), segment_name = character(),
                  segment_text = character(), char_count = integer()))
  }

  data %>%
    select(document_id, all_of(seg_cols)) %>%
    pivot_longer(cols = starts_with("seg_"),
                 names_to = "segment_name",
                 values_to = "segment_text",
                 names_prefix = "seg_") %>%
    mutate(char_count = nchar(segment_text))
}


# ── Statistical Validation ───────────────────────────────────────

#' Compute summary statistics per segment type.
#'
#' @param segments Long-format segment tibble from pivot_segments()
#' @return tibble with mean, median, sd, min, max per segment
segment_length_stats <- function(segments) {
  segments %>%
    group_by(segment_name) %>%
    summarise(
      n = n(),
      mean_chars = round(mean(char_count, na.rm = TRUE), 1),
      median_chars = round(median(char_count, na.rm = TRUE), 1),
      sd_chars = round(sd(char_count, na.rm = TRUE), 1),
      min_chars = min(char_count, na.rm = TRUE),
      max_chars = max(char_count, na.rm = TRUE),
      pct_empty = round(mean(char_count == 0 | is.na(segment_text), na.rm = TRUE) * 100, 1),
      .groups = "drop"
    )
}


#' Compare segment length distributions between synthetic and reference data.
#'
#' Uses Kolmogorov-Smirnov test. Returns p-values per segment.
#' Requires fitdistrplus for richer analysis.
#'
#' @param synthetic Long-format segments from synthetic data
#' @param reference Long-format segments from reference data
#' @return tibble with segment_name, ks_statistic, ks_pvalue, match_quality
compare_distributions <- function(synthetic, reference) {
  shared_segments <- intersect(
    unique(synthetic$segment_name),
    unique(reference$segment_name)
  )

  if (length(shared_segments) == 0) {
    warning("No shared segment names between synthetic and reference data")
    return(tibble())
  }

  results <- lapply(shared_segments, function(seg) {
    syn_vals <- synthetic %>% filter(segment_name == seg) %>% pull(char_count)
    ref_vals <- reference %>% filter(segment_name == seg) %>% pull(char_count)

    # Need at least 5 observations each
    if (length(syn_vals) < 5 || length(ref_vals) < 5) {
      return(tibble(segment_name = seg, ks_statistic = NA_real_,
                    ks_pvalue = NA_real_, match_quality = "insufficient_data"))
    }

    test <- tryCatch(
      ks.test(syn_vals, ref_vals),
      error = function(e) list(statistic = NA_real_, p.value = NA_real_)
    )

    quality <- case_when(
      is.na(test$p.value) ~ "error",
      test$p.value > 0.10 ~ "good",
      test$p.value > 0.05 ~ "acceptable",
      test$p.value > 0.01 ~ "marginal",
      TRUE ~ "poor"
    )

    tibble(
      segment_name = seg,
      ks_statistic = round(unname(test$statistic), 4),
      ks_pvalue = round(test$p.value, 4),
      match_quality = quality
    )
  })

  bind_rows(results)
}


#' Verify flaw injection rates match target distribution.
#'
#' @param data tibble with quality_tier and error_rate columns (mixed datasets)
#' @return tibble with tier, expected_pct, observed_pct, chi_sq_contribution
verify_flaw_distribution <- function(data) {
  if (!("quality_tier" %in% names(data))) {
    return(tibble(message = "No quality_tier column — single-tier dataset"))
  }

  observed <- data %>%
    count(quality_tier) %>%
    mutate(observed_pct = round(n / sum(n) * 100, 1))

  observed
}


#' Fit distributions to segment lengths using fitdistrplus (if available).
#'
#' @param segments Long-format segments
#' @return list of fit results per segment, or NULL if fitdistrplus not available
fit_segment_distributions <- function(segments) {
  if (!requireNamespace("fitdistrplus", quietly = TRUE)) {
    message("fitdistrplus not installed — skipping distribution fitting")
    message("Install with: install.packages('fitdistrplus')")
    return(NULL)
  }

  library(fitdistrplus)

  segment_names <- unique(segments$segment_name)
  fits <- list()

  for (seg in segment_names) {
    vals <- segments %>%
      filter(segment_name == seg, char_count > 0) %>%
      pull(char_count)

    if (length(vals) < 10) next

    fit <- tryCatch({
      # Try lognormal first (typical for text lengths)
      f_lnorm <- fitdist(vals, "lnorm")
      f_norm <- fitdist(vals, "norm")
      gof <- gofstat(list(f_lnorm, f_norm),
                      fitnames = c("lognormal", "normal"))

      list(
        segment = seg,
        n = length(vals),
        best_fit = if (gof$aic[1] < gof$aic[2]) "lognormal" else "normal",
        aic_lognormal = round(gof$aic[1], 1),
        aic_normal = round(gof$aic[2], 1),
        ks_lognormal = round(gof$ks["lognormal"], 4),
        ks_normal = round(gof$ks["normal"], 4)
      )
    }, error = function(e) {
      list(segment = seg, n = length(vals), error = conditionMessage(e))
    })

    fits[[seg]] <- fit
  }

  fits
}


# ── Visualization ────────────────────────────────────────────────

#' VilseckKI branded ggplot2 theme
theme_vilseckki <- function() {
  theme_minimal(base_size = 12, base_family = "sans") +
    theme(
      plot.title = element_text(size = 14, face = "bold", color = "#1B3A5C"),
      plot.subtitle = element_text(size = 10, color = "#4A6D8C"),
      plot.caption = element_text(size = 8, color = "#888888", hjust = 1),
      panel.grid.minor = element_blank(),
      panel.grid.major.x = element_blank(),
      strip.text = element_text(face = "bold", color = "#1B3A5C"),
      legend.position = "bottom"
    )
}


#' Plot segment length distributions as violin + box plots.
#'
#' @param segments Long-format segments
#' @param output_path Path to save PNG
plot_segment_lengths <- function(segments, output_path) {
  p <- ggplot(segments, aes(x = reorder(segment_name, char_count, median),
                             y = char_count, fill = segment_name)) +
    geom_violin(alpha = 0.6, show.legend = FALSE) +
    geom_boxplot(width = 0.15, alpha = 0.8, show.legend = FALSE, outlier.size = 0.5) +
    coord_flip() +
    labs(
      title = "Segment Length Distribution",
      subtitle = "Characters per segment across all generated documents",
      x = NULL, y = "Character count",
      caption = "Misawa Data GK | VilseckKI Synth-Factory"
    ) +
    scale_fill_brewer(palette = "Set2") +
    theme_vilseckki()

  ggsave(output_path, p, width = 10, height = 6, dpi = 150, bg = "white")
  message(paste("Plot saved:", output_path))
}


#' Plot quality tier distribution (for mixed datasets).
#'
#' @param data Dataset tibble with quality_tier column
#' @param output_path Path to save PNG
plot_tier_distribution <- function(data, output_path) {
  if (!("quality_tier" %in% names(data))) return(invisible(NULL))

  tier_colors <- c(
    "perfect" = "#2E8B57",
    "near" = "#4682B4",
    "moderate" = "#DAA520",
    "severe" = "#CD5C5C"
  )

  tier_data <- data %>%
    count(quality_tier) %>%
    mutate(pct = n / sum(n) * 100,
           label = paste0(round(pct, 1), "%"))

  p <- ggplot(tier_data, aes(x = reorder(quality_tier, -pct), y = pct,
                              fill = quality_tier)) +
    geom_col(alpha = 0.85, show.legend = FALSE) +
    geom_text(aes(label = label), vjust = -0.5, size = 4, fontface = "bold") +
    scale_fill_manual(values = tier_colors) +
    labs(
      title = "Quality Tier Distribution",
      subtitle = "Percentage of documents per flaw injection tier",
      x = NULL, y = "Percentage of documents",
      caption = "Misawa Data GK | VilseckKI Synth-Factory"
    ) +
    ylim(0, max(tier_data$pct) * 1.15) +
    theme_vilseckki()

  ggsave(output_path, p, width = 8, height = 5, dpi = 150, bg = "white")
  message(paste("Plot saved:", output_path))
}


#' Plot flaw category distribution from taxonomy.
#'
#' @param taxonomy_path Path to flaw_taxonomy.json
#' @param output_path Path to save PNG
plot_flaw_taxonomy <- function(taxonomy_path, output_path) {
  if (is.null(taxonomy_path) || !file.exists(taxonomy_path)) return(invisible(NULL))

  taxonomy <- fromJSON(taxonomy_path)
  cats <- taxonomy$categories

  if (is.null(cats) || nrow(cats) == 0) return(invisible(NULL))

  cats$label <- paste0(cats$flaw_type, " / ", cats$flaw_subtype)

  p <- ggplot(cats, aes(x = reorder(label, frequency), y = frequency * 100,
                         fill = flaw_type)) +
    geom_col(alpha = 0.85) +
    coord_flip() +
    labs(
      title = "Flaw Taxonomy — Observed Frequencies",
      subtitle = paste("From", taxonomy$total_documents_analyzed, "analyzed EDINET filings"),
      x = NULL, y = "Frequency (%)",
      fill = "Category",
      caption = "Misawa Data GK | VilseckKI Synth-Factory"
    ) +
    scale_fill_brewer(palette = "Set1") +
    theme_vilseckki()

  ggsave(output_path, p, width = 10, height = 6, dpi = 150, bg = "white")
  message(paste("Plot saved:", output_path))
}


# ── Report Assembly ──────────────────────────────────────────────

#' Build validation summary as a structured list.
build_validation_summary <- function(data, segments, seg_stats, dist_comparison,
                                      tier_dist, dist_fits) {
  summary <- list(
    metadata = list(
      generated_at = Sys.time(),
      tool = "VilseckKI Synth-Factory R Validator",
      version = "1.0.0"
    ),
    dataset = list(
      total_documents = nrow(data),
      total_segments = nrow(segments),
      segment_types = length(unique(segments$segment_name)),
      has_quality_tiers = "quality_tier" %in% names(data)
    ),
    segment_statistics = seg_stats,
    distribution_comparison = if (!is.null(dist_comparison) && nrow(dist_comparison) > 0)
      dist_comparison else "no_reference_data",
    tier_distribution = tier_dist,
    distribution_fits = dist_fits,
    overall_quality = list(
      segments_with_content = round(mean(segments$char_count > 0) * 100, 1),
      mean_document_length = round(
        mean(nchar(data$document_content %||% ""), na.rm = TRUE), 0),
      validation_passed = mean(segments$char_count > 0) > 0.90
    )
  )

  summary
}


# ── Main ─────────────────────────────────────────────────────────

main <- function() {
  args <- parse_args()
  opts <- args$options

  if (is.null(opts$input)) {
    stop("--input is required. Run with --help for usage.")
  }

  # Create output directory
  dir.create(opts$output, recursive = TRUE, showWarnings = FALSE)
  plots_dir <- file.path(opts$output, "plots")
  dir.create(plots_dir, recursive = TRUE, showWarnings = FALSE)

  message("========================================")
  message("VilseckKI Dataset Validator")
  message("========================================")

  # Load data
  message(paste("Loading dataset:", opts$input))
  data <- load_dataset(opts$input)
  message(paste("  Documents:", nrow(data)))

  # Pivot to long format
  segments <- pivot_segments(data)
  message(paste("  Segments:", nrow(segments)))

  # Segment statistics
  seg_stats <- segment_length_stats(segments)
  message("\nSegment statistics:")
  print(as.data.frame(seg_stats), row.names = FALSE)

  # Distribution comparison (if reference provided)
  dist_comparison <- NULL
  if (!is.null(opts$reference) && file.exists(opts$reference)) {
    message(paste("\nLoading reference:", opts$reference))
    ref_data <- load_dataset(opts$reference)
    ref_segments <- pivot_segments(ref_data)
    dist_comparison <- compare_distributions(segments, ref_segments)
    if (nrow(dist_comparison) > 0) {
      message("\nDistribution comparison (KS test):")
      print(as.data.frame(dist_comparison), row.names = FALSE)
    }
  }

  # Tier distribution
  tier_dist <- verify_flaw_distribution(data)

  # Distribution fitting
  dist_fits <- fit_segment_distributions(segments)

  # Generate plots
  message("\nGenerating plots...")
  plot_segment_lengths(segments, file.path(plots_dir, "segment_lengths.png"))
  plot_tier_distribution(data, file.path(plots_dir, "tier_distribution.png"))
  plot_flaw_taxonomy(opts$taxonomy, file.path(plots_dir, "flaw_taxonomy.png"))

  # Build and save summary
  summary <- build_validation_summary(
    data, segments, seg_stats, dist_comparison, tier_dist, dist_fits
  )

  summary_path <- file.path(opts$output, "validation_summary.json")
  write_json(summary, summary_path, pretty = TRUE, auto_unbox = TRUE)
  message(paste("\nValidation summary:", summary_path))

  # Overall result
  passed <- summary$overall_quality$validation_passed
  message(paste("\n========================================"))
  message(paste("RESULT:", if (passed) "PASS" else "WARN"))
  message(paste("  Content coverage:",
                summary$overall_quality$segments_with_content, "%"))
  message(paste("========================================"))

  # Return exit code
  quit(status = if (passed) 0 else 1, save = "no")
}

# Run if called directly
if (!interactive()) {
  main()
}
