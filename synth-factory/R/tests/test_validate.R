# ==========================================================================
# Tests for validate_dataset.R
# ==========================================================================
#
# Run with: Rscript -e "testthat::test_file('R/tests/test_validate.R')"
#
# These tests use temporary JSONL files to verify all core functions
# without requiring real EDINET data or an Ollama-generated dataset.
# ==========================================================================

library(testthat)
library(jsonlite)

# Source the validation functions (skip the main() execution)
# We source individual functions by reading the file and evaluating
# everything except the main() call and the interactive guard.
source_validation <- function() {
  code <- readLines("R/validate_dataset.R")
  # Remove the interactive guard and main() call at the bottom
  guard_line <- grep("^if \\(!interactive\\(\\)\\)", code)
  if (length(guard_line) > 0) {
    code <- code[1:(guard_line[1] - 1)]
  }
  # Remove the main function definition to avoid arg parsing on source
  main_start <- grep("^main <- function", code)
  if (length(main_start) > 0) {
    # Find matching closing brace
    brace_depth <- 0
    main_end <- main_start
    for (i in main_start:length(code)) {
      brace_depth <- brace_depth +
        nchar(gsub("[^{]", "", code[i])) -
        nchar(gsub("[^}]", "", code[i]))
      if (brace_depth == 0 && i > main_start) {
        main_end <- i
        break
      }
    }
    code <- code[-(main_start:main_end)]
  }
  # Also skip parse_args
  pa_start <- grep("^parse_args <- function", code)
  if (length(pa_start) > 0) {
    brace_depth <- 0
    pa_end <- pa_start
    for (i in pa_start:length(code)) {
      brace_depth <- brace_depth +
        nchar(gsub("[^{]", "", code[i])) -
        nchar(gsub("[^}]", "", code[i]))
      if (brace_depth == 0 && i > pa_start) {
        pa_end <- i
        break
      }
    }
    code <- code[-(pa_start:pa_end)]
  }
  eval(parse(text = paste(code, collapse = "\n")), envir = globalenv())
}

source_validation()


# ── Test fixtures ────────────────────────────────────────────────

make_test_jsonl <- function(n = 10, has_tiers = FALSE) {
  tmp <- tempfile(fileext = ".jsonl")
  tiers <- c("perfect", "near", "moderate", "severe")

  lines <- vapply(seq_len(n), function(i) {
    doc <- list(
      document_id = sprintf("DOC-%06d", i),
      document_content = paste("Full document content for", i),
      seg_company_overview = paste(rep("企業概況テスト", sample(5:20, 1)), collapse = ""),
      seg_business_status = paste(rep("事業状況テスト", sample(5:15, 1)), collapse = ""),
      seg_business_risks = paste(rep("リスクテスト内容", sample(3:12, 1)), collapse = ""),
      seg_md_and_a = paste(rep("経営分析テスト", sample(8:25, 1)), collapse = "")
    )
    if (has_tiers) {
      tier <- sample(tiers, 1, prob = c(0.8, 0.1, 0.08, 0.02))
      doc$quality_tier <- tier
      doc$error_rate <- switch(tier,
        perfect = 0, near = 0.03, moderate = 0.12, severe = 0.3)
    }
    toJSON(doc, auto_unbox = TRUE)
  }, character(1))

  writeLines(lines, tmp)
  tmp
}

make_empty_doc_jsonl <- function() {
  tmp <- tempfile(fileext = ".jsonl")
  doc <- list(
    document_id = "DOC-000001",
    document_content = "",
    seg_company_overview = "",
    seg_business_status = "Some content",
    seg_business_risks = "",
    seg_md_and_a = ""
  )
  writeLines(toJSON(doc, auto_unbox = TRUE), tmp)
  tmp
}

make_taxonomy_json <- function() {
  tmp <- tempfile(fileext = ".json")
  taxonomy <- list(
    source_name = "edinet",
    document_type = "securities_report_jp",
    total_documents_analyzed = 50,
    last_updated = "2026-03-15T00:00:00+00:00",
    categories = data.frame(
      flaw_type = c("structural", "formatting", "disclosure"),
      flaw_subtype = c("empty_section", "garbled_symbols", "generic_language"),
      description = c("Empty section", "Garbled", "Generic"),
      segment = c("business_risks", "", "business_risks"),
      count = c(10, 5, 15),
      frequency = c(0.20, 0.10, 0.30),
      severity = c("low", "high", "medium"),
      stringsAsFactors = FALSE
    )
  )
  write_json(taxonomy, tmp, auto_unbox = TRUE)
  tmp
}


# ── Tests ────────────────────────────────────────────────────────

test_that("load_dataset reads JSONL correctly", {
  path <- make_test_jsonl(5)
  on.exit(unlink(path))

  data <- load_dataset(path)
  expect_equal(nrow(data), 5)
  expect_true("document_id" %in% names(data))
  expect_true("seg_company_overview" %in% names(data))
})

test_that("load_dataset errors on missing file", {
  expect_error(load_dataset("/nonexistent/path.jsonl"), "not found")
})

test_that("load_dataset errors on empty file", {
  tmp <- tempfile(fileext = ".jsonl")
  writeLines("", tmp)
  on.exit(unlink(tmp))

  expect_error(load_dataset(tmp), "empty")
})

test_that("pivot_segments creates long format", {
  path <- make_test_jsonl(3)
  on.exit(unlink(path))

  data <- load_dataset(path)
  segments <- pivot_segments(data)

  expect_true("segment_name" %in% names(segments))
  expect_true("char_count" %in% names(segments))
  # 3 documents × 4 segment types = 12 rows
  expect_equal(nrow(segments), 12)
  expect_true(all(segments$char_count >= 0))
})

test_that("pivot_segments handles no segment columns", {
  data <- tibble(document_id = c("DOC-1", "DOC-2"), other_col = c("a", "b"))
  segments <- pivot_segments(data)
  expect_equal(nrow(segments), 0)
})

test_that("segment_length_stats computes correctly", {
  path <- make_test_jsonl(20)
  on.exit(unlink(path))

  data <- load_dataset(path)
  segments <- pivot_segments(data)
  stats <- segment_length_stats(segments)

  expect_true(all(c("segment_name", "n", "mean_chars", "sd_chars") %in% names(stats)))
  expect_equal(nrow(stats), 4)  # 4 segment types
  expect_true(all(stats$n == 20))  # 20 docs each
  expect_true(all(stats$mean_chars > 0))
})

test_that("segment_length_stats reports empty segments", {
  path <- make_empty_doc_jsonl()
  on.exit(unlink(path))

  data <- load_dataset(path)
  segments <- pivot_segments(data)
  stats <- segment_length_stats(segments)

  # 3 of 4 segments are empty
  empty_rows <- stats %>% filter(pct_empty > 0)
  expect_true(nrow(empty_rows) >= 3)
})

test_that("compare_distributions runs KS test", {
  syn_path <- make_test_jsonl(30)
  ref_path <- make_test_jsonl(30)
  on.exit({ unlink(syn_path); unlink(ref_path) })

  syn_data <- load_dataset(syn_path)
  ref_data <- load_dataset(ref_path)
  syn_segs <- pivot_segments(syn_data)
  ref_segs <- pivot_segments(ref_data)

  comparison <- compare_distributions(syn_segs, ref_segs)

  expect_true(nrow(comparison) > 0)
  expect_true("ks_pvalue" %in% names(comparison))
  expect_true("match_quality" %in% names(comparison))
  expect_true(all(comparison$match_quality %in%
    c("good", "acceptable", "marginal", "poor", "insufficient_data", "error")))
})

test_that("verify_flaw_distribution works with tiers", {
  path <- make_test_jsonl(100, has_tiers = TRUE)
  on.exit(unlink(path))

  data <- load_dataset(path)
  tier_dist <- verify_flaw_distribution(data)

  expect_true("quality_tier" %in% names(tier_dist))
  expect_true("observed_pct" %in% names(tier_dist))
  expect_equal(sum(tier_dist$n), 100)
})

test_that("verify_flaw_distribution handles single-tier data", {
  path <- make_test_jsonl(10, has_tiers = FALSE)
  on.exit(unlink(path))

  data <- load_dataset(path)
  result <- verify_flaw_distribution(data)

  expect_true("message" %in% names(result))
})

test_that("theme_vilseckki returns valid theme", {
  th <- theme_vilseckki()
  expect_s3_class(th, "theme")
})

test_that("plot_segment_lengths creates PNG", {
  path <- make_test_jsonl(20)
  on.exit(unlink(path))
  out_path <- tempfile(fileext = ".png")
  on.exit(unlink(out_path), add = TRUE)

  data <- load_dataset(path)
  segments <- pivot_segments(data)
  plot_segment_lengths(segments, out_path)

  expect_true(file.exists(out_path))
  expect_true(file.size(out_path) > 0)
})

test_that("plot_tier_distribution creates PNG for mixed data", {
  path <- make_test_jsonl(50, has_tiers = TRUE)
  on.exit(unlink(path))
  out_path <- tempfile(fileext = ".png")
  on.exit(unlink(out_path), add = TRUE)

  data <- load_dataset(path)
  plot_tier_distribution(data, out_path)

  expect_true(file.exists(out_path))
})

test_that("plot_flaw_taxonomy creates PNG", {
  tax_path <- make_taxonomy_json()
  on.exit(unlink(tax_path))
  out_path <- tempfile(fileext = ".png")
  on.exit(unlink(out_path), add = TRUE)

  plot_flaw_taxonomy(tax_path, out_path)

  expect_true(file.exists(out_path))
})

test_that("build_validation_summary produces complete structure", {
  path <- make_test_jsonl(10)
  on.exit(unlink(path))

  data <- load_dataset(path)
  segments <- pivot_segments(data)
  stats <- segment_length_stats(segments)

  summary <- build_validation_summary(
    data, segments, stats,
    dist_comparison = NULL,
    tier_dist = verify_flaw_distribution(data),
    dist_fits = NULL
  )

  expect_true(all(c("metadata", "dataset", "segment_statistics",
                     "overall_quality") %in% names(summary)))
  expect_equal(summary$dataset$total_documents, 10)
  expect_true(is.logical(summary$overall_quality$validation_passed))
})
