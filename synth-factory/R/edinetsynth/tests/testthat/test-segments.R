# ==========================================================================
# Tests for extract_segment() and segment_summary()
# ==========================================================================

library(jsonlite)

# Reuse fixture from test-load.R
make_test_jsonl <- function(n = 5) {
  tmp <- tempfile(fileext = ".jsonl")
  lines <- vapply(seq_len(n), function(i) {
    doc <- list(
      document_id = sprintf("DOC-%06d", i),
      seg_company_overview = paste(rep("概況テスト", sample(5:20, 1)),
                                   collapse = ""),
      seg_business_status = paste(rep("状況テスト", sample(5:15, 1)),
                                  collapse = ""),
      seg_business_risks = paste(rep("リスク内容", sample(3:12, 1)),
                                 collapse = ""),
      seg_md_and_a = paste(rep("分析テスト", sample(8:25, 1)),
                           collapse = "")
    )
    toJSON(doc, auto_unbox = TRUE)
  }, character(1))
  writeLines(lines, tmp)
  tmp
}


# ── extract_segment ─────────────────────────────────────────────

test_that("extract_segment returns tibble with id by default", {
  path <- make_test_jsonl(5)
  on.exit(unlink(path))

  data <- load_securities_report(path)
  result <- extract_segment(data, "company_overview")

  expect_s3_class(result, "tbl_df")
  expect_equal(ncol(result), 2)
  expect_true("document_id" %in% names(result))
  expect_equal(nrow(result), 5)
})

test_that("extract_segment accepts full column name", {
  path <- make_test_jsonl(3)
  on.exit(unlink(path))

  data <- load_securities_report(path)
  result <- extract_segment(data, "seg_business_risks")
  expect_equal(nrow(result), 3)
})

test_that("extract_segment returns character when with_id=FALSE", {
  path <- make_test_jsonl(4)
  on.exit(unlink(path))

  data <- load_securities_report(path)
  result <- extract_segment(data, "md_and_a", with_id = FALSE)
  expect_type(result, "character")
  expect_length(result, 4)
})

test_that("extract_segment errors on unknown segment", {
  path <- make_test_jsonl(3)
  on.exit(unlink(path))

  data <- load_securities_report(path)
  expect_error(
    extract_segment(data, "nonexistent_segment"),
    "not found"
  )
})


# ── segment_summary ─────────────────────────────────────────────

test_that("segment_summary returns one row per segment", {
  path <- make_test_jsonl(10)
  on.exit(unlink(path))

  data <- load_securities_report(path)
  stats <- segment_summary(data)

  expect_s3_class(stats, "tbl_df")
  expect_equal(nrow(stats), 4)  # 4 seg_ columns
  expect_true(all(c("segment", "n", "mean_chars", "pct_empty") %in%
                    names(stats)))
})

test_that("segment_summary computes correct counts", {
  path <- make_test_jsonl(8)
  on.exit(unlink(path))

  data <- load_securities_report(path)
  stats <- segment_summary(data)
  expect_true(all(stats$n == 8))
  expect_true(all(stats$mean_chars > 0))
})

test_that("segment_summary handles data with no seg_ columns", {
  data <- dplyr::tibble(document_id = c("A", "B"), other = c(1, 2))
  stats <- segment_summary(data)
  expect_equal(nrow(stats), 0)
})

test_that("segment_summary computes token estimates", {
  path <- make_test_jsonl(5)
  on.exit(unlink(path))

  data <- load_securities_report(path)
  stats <- segment_summary(data)
  expect_true("est_tokens" %in% names(stats))
  expect_true(all(stats$est_tokens > 0))
})
