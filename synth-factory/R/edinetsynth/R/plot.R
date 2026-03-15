#' Generate a Quality Report Visualization Suite
#'
#' Creates a set of publication-quality ggplot2 visualizations suitable
#' for marketplace listings (JDEX, Datarade) or academic presentations.
#'
#' Produces up to 4 plots depending on available data:
#' 1. Segment length violin plot
#' 2. Tier distribution bar chart (if quality_tier present)
#' 3. Flaw type frequency chart (if flaws detected)
#' 4. Segment emptiness heatmap
#'
#' @param data A tibble returned by [load_securities_report()].
#' @param output_dir Character. Directory to save PNG files.
#'   Created if it does not exist.
#' @param taxonomy_path Optional character. Path to flaw_taxonomy.json
#'   for richer flaw analysis.
#' @param width Numeric. Plot width in inches. Default 10.
#' @param height Numeric. Plot height in inches. Default 6.
#' @param dpi Numeric. Resolution. Default 150.
#'
#' @return Invisibly, a named list of file paths to generated PNGs.
#'
#' @examples
#' \dontrun{
#' reports <- load_securities_report("reports.jsonl")
#' paths <- plot_quality_report(reports, output_dir = "plots/")
#' names(paths)
#' }
#'
#' @importFrom ggplot2 ggplot aes geom_violin geom_boxplot geom_col labs theme_minimal ggsave
#' @importFrom tidyr pivot_longer
#' @importFrom dplyr mutate group_by summarise count
#' @importFrom rlang .data
#' @export
plot_quality_report <- function(data, output_dir = "quality_plots",
                                taxonomy_path = NULL,
                                width = 10, height = 6, dpi = 150) {
  if (!dir.exists(output_dir)) {
    dir.create(output_dir, recursive = TRUE)
  }

  seg_cols <- grep("^seg_", names(data), value = TRUE)
  paths <- list()

  # ── VilseckKI theme ──
  vilseckki_theme <- ggplot2::theme_minimal() +
    ggplot2::theme(
      plot.title = ggplot2::element_text(size = 14, face = "bold"),
      plot.subtitle = ggplot2::element_text(size = 10, color = "grey40"),
      axis.text = ggplot2::element_text(size = 9),
      legend.position = "bottom"
    )

  # ── 1. Segment length violin plot ──
  if (length(seg_cols) > 0) {
    long <- tidyr::pivot_longer(
      data, cols = dplyr::all_of(seg_cols),
      names_to = "segment", values_to = "text"
    )
    long <- dplyr::mutate(
      long,
      segment = gsub("^seg_", "", .data$segment),
      char_count = nchar(as.character(.data$text))
    )

    p1 <- ggplot2::ggplot(long, ggplot2::aes(
      x = .data$segment, y = .data$char_count, fill = .data$segment
    )) +
      ggplot2::geom_violin(alpha = 0.7, show.legend = FALSE) +
      ggplot2::geom_boxplot(width = 0.15, alpha = 0.3, show.legend = FALSE) +
      ggplot2::labs(
        title = "Segment Length Distribution",
        subtitle = paste0("n = ", nrow(data), " documents"),
        x = "Segment", y = "Character Count"
      ) +
      vilseckki_theme

    path1 <- file.path(output_dir, "segment_lengths.png")
    ggplot2::ggsave(path1, p1, width = width, height = height, dpi = dpi)
    paths$segment_lengths <- path1
  }

  # ── 2. Tier distribution bar chart ──
  if ("quality_tier" %in% names(data)) {
    tier_order <- c("perfect", "near", "moderate", "severe")
    tier_counts <- dplyr::count(data, .data$quality_tier)
    tier_counts <- dplyr::mutate(
      tier_counts,
      quality_tier = factor(.data$quality_tier, levels = tier_order),
      pct = .data$n / sum(.data$n) * 100
    )

    # Expected line data
    expected_df <- data.frame(
      quality_tier = factor(tier_order, levels = tier_order),
      expected_pct = c(80, 10, 8, 2)
    )

    p2 <- ggplot2::ggplot(tier_counts, ggplot2::aes(
      x = .data$quality_tier, y = .data$pct, fill = .data$quality_tier
    )) +
      ggplot2::geom_col(alpha = 0.8, show.legend = FALSE) +
      ggplot2::geom_point(
        data = expected_df,
        ggplot2::aes(x = .data$quality_tier, y = .data$expected_pct),
        shape = 4, size = 4, colour = "red", inherit.aes = FALSE
      ) +
      ggplot2::labs(
        title = "Quality Tier Distribution",
        subtitle = "Bars = observed, red X = expected (80/10/8/2)",
        x = "Quality Tier", y = "Percentage (%)"
      ) +
      vilseckki_theme

    path2 <- file.path(output_dir, "tier_distribution.png")
    ggplot2::ggsave(path2, p2, width = width, height = height, dpi = dpi)
    paths$tier_distribution <- path2
  }

  # ── 3. Flaw frequency chart ──
  flaws <- detect_flaws(data, taxonomy_path = taxonomy_path)
  if (nrow(flaws) > 0) {
    flaw_counts <- dplyr::count(flaws, .data$flaw_type, .data$severity)

    p3 <- ggplot2::ggplot(flaw_counts, ggplot2::aes(
      x = stats::reorder(.data$flaw_type, .data$n),
      y = .data$n, fill = .data$severity
    )) +
      ggplot2::geom_col() +
      ggplot2::coord_flip() +
      ggplot2::labs(
        title = "Detected Flaw Types",
        subtitle = paste0(nrow(flaws), " total flaws across ",
                          length(unique(flaws$document_id)), " documents"),
        x = "Flaw Type", y = "Count", fill = "Severity"
      ) +
      vilseckki_theme

    path3 <- file.path(output_dir, "flaw_frequency.png")
    ggplot2::ggsave(path3, p3, width = width, height = height, dpi = dpi)
    paths$flaw_frequency <- path3
  }

  # ── 4. Segment emptiness summary ──
  if (length(seg_cols) > 0) {
    empty_summary <- segment_summary(data)
    if (nrow(empty_summary) > 0 && any(empty_summary$pct_empty > 0)) {
      p4 <- ggplot2::ggplot(empty_summary, ggplot2::aes(
        x = stats::reorder(.data$segment, .data$pct_empty),
        y = .data$pct_empty
      )) +
        ggplot2::geom_col(fill = "#e74c3c", alpha = 0.8) +
        ggplot2::coord_flip() +
        ggplot2::labs(
          title = "Segment Emptiness Rate",
          subtitle = "Percentage of documents with empty segment",
          x = "Segment", y = "Empty (%)"
        ) +
        vilseckki_theme

      path4 <- file.path(output_dir, "emptiness_rate.png")
      ggplot2::ggsave(path4, p4, width = width, height = height, dpi = dpi)
      paths$emptiness_rate <- path4
    }
  }

  message("Generated ", length(paths), " plot(s) in: ", output_dir)
  invisible(paths)
}
