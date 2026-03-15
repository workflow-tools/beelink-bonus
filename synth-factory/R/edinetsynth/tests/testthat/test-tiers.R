# ==========================================================================
# Tests for compare_tiers()
# ==========================================================================

library(jsonlite)

make_tiered_jsonl <- function(n = 100) {
  tmp <- tempfile(fileext = ".jsonl")
  tiers <- c("perfect", "near", "moderate", "severe")
  error_rates <- c(0.0, 0.03, 0.12, 0.30)

  lines <- vapply(seq_len(n), function(i) {
    tier_idx <- sample(seq_along(tiers), 1,
                       prob = c(0.8, 0.1, 0.08, 0.02))
    doc <- list(
      document_id = sprintf("DOC-%06d", i),
      quality_tier = tiers[tier_idx],
      error_rate = error_rates[tier_idx],
      seg_company_overview = paste(rep("概況内容", sample(10:30, 1)),
                                   collapse = ""),
      seg_business_risks = paste(rep("リスク内容", sample(10:20, 1)),
                                 collapse = "")
    )
    toJSON(doc, auto_unbox = TRUE)
  }, character(1))

  writeLines(lines, tmp)
  tmp
}


test_that("compare_tiers returns tier statistics", {
  path <- make_tiered_jsonl(200)
  on.exit(unlink(path))

  data <- load_securities_report(path)
  tiers <- compare_tiers(data)

  expect_s3_class(tiers, "tbl_df")
  expect_true(nrow(tiers) >= 1)
  expect_true(all(c("quality_tier", "n", "pct", "expected_pct",
                     "deviation") %in% names(tiers)))
})

test_that("compare_tiers percentages sum to 100", {
  path <- make_tiered_jsonl(200)
  on.exit(unlink(path))

  data <- load_securities_report(path)
  tiers <- compare_tiers(data)

  expect_equal(sum(tiers$n), 200)
  expect_equal(sum(tiers$pct), 100, tolerance = 0.01)
})

test_that("compare_tiers has expected_pct from defaults", {
  path <- make_tiered_jsonl(500)
  on.exit(unlink(path))

  data <- load_securities_report(path)
  tiers <- compare_tiers(data)

  perfect_row <- tiers[tiers$quality_tier == "perfect", ]
  if (nrow(perfect_row) > 0) {
    expect_equal(perfect_row$expected_pct, 80.0)
  }
})

test_that("compare_tiers returns empty for non-tiered data", {
  tmp <- tempfile(fileext = ".jsonl")
  on.exit(unlink(tmp))

  doc <- list(
    document_id = "DOC-1",
    seg_company_overview = "Some content"
  )
  writeLines(toJSON(doc, auto_unbox = TRUE), tmp)

  data <- load_securities_report(tmp)
  result <- compare_tiers(data)

  expect_equal(nrow(result), 0)
})

test_that("compare_tiers includes error_rate averages", {
  path <- make_tiered_jsonl(100)
  on.exit(unlink(path))

  data <- load_securities_report(path)
  tiers <- compare_tiers(data)

  expect_true("mean_error_rate" %in% names(tiers))
  perfect_row <- tiers[tiers$quality_tier == "perfect", ]
  if (nrow(perfect_row) > 0) {
    expect_equal(perfect_row$mean_error_rate, 0.0)
  }
})
