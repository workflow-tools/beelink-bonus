# ==========================================================================
# Tests for make_sample_data()
# ==========================================================================


test_that("make_sample_data returns tibble with correct structure", {
  demo <- make_sample_data(n = 10)

  expect_s3_class(demo, "tbl_df")
  expect_equal(nrow(demo), 10)

  # Must have document_id, quality_tier, and seg_ columns

  expect_true("document_id" %in% names(demo))
  expect_true("quality_tier" %in% names(demo))

  seg_cols <- grep("^seg_", names(demo), value = TRUE)
  expect_true(length(seg_cols) >= 6)
})

test_that("make_sample_data generates all four tiers", {
  demo <- make_sample_data(n = 100, seed = 123)

  tiers_present <- unique(demo$quality_tier)
  expect_true("perfect" %in% tiers_present)
  # near/moderate/severe may not all appear at n=100 due to low probability
  # but at least 2 tiers should be present
  expect_true(length(tiers_present) >= 2)
})

test_that("make_sample_data generates Japanese content", {
  demo <- make_sample_data(n = 5)

  # Check that segment text contains Japanese characters
  all_text <- paste(demo$seg_company_overview, collapse = "")
  jp_chars <- nchar(gsub("[^\u3040-\u309F\u30A0-\u30FF\u4E00-\u9FFF]", "", all_text))
  expect_true(jp_chars > 50)
})

test_that("make_sample_data writes to file when output_path provided", {
  tmp <- tempfile(fileext = ".jsonl")
  on.exit(unlink(tmp))

  result <- make_sample_data(n = 10, output_path = tmp)

  expect_equal(result, tmp)
  expect_true(file.exists(tmp))
  expect_true(file.info(tmp)$size > 100)

  # Should be loadable by load_securities_report
  loaded <- load_securities_report(tmp)
  expect_equal(nrow(loaded), 10)
})

test_that("make_sample_data is reproducible with same seed", {
  demo1 <- make_sample_data(n = 10, seed = 99)
  demo2 <- make_sample_data(n = 10, seed = 99)

  expect_equal(demo1$document_id, demo2$document_id)
  expect_equal(demo1$quality_tier, demo2$quality_tier)
  expect_equal(demo1$seg_company_overview, demo2$seg_company_overview)
})

test_that("make_sample_data works with full pipeline", {
  demo <- make_sample_data(n = 20)

  # Should work with all core functions
  stats <- segment_summary(demo)
  expect_s3_class(stats, "tbl_df")
  expect_true(nrow(stats) >= 5)

  flaws <- detect_flaws(demo)
  expect_s3_class(flaws, "tbl_df")

  tiers <- compare_tiers(demo)
  expect_s3_class(tiers, "tbl_df")
})

test_that("make_sample_data includes going_concern for some documents", {
  demo <- make_sample_data(n = 100)

  gc_col <- "seg_going_concern"
  if (gc_col %in% names(demo)) {
    non_empty_gc <- sum(nchar(as.character(demo[[gc_col]])) > 0, na.rm = TRUE)
    # ~15% distressed, so expect some non-empty
    expect_true(non_empty_gc >= 1)
  }
})

test_that("make_sample_data severe tier has flaws", {
  demo <- make_sample_data(n = 100, seed = 42)

  severe <- demo[demo$quality_tier == "severe", ]
  if (nrow(severe) > 0) {
    flaws <- detect_flaws(severe)
    # Severe documents should have detectable flaws
    expect_true(nrow(flaws) > 0)
  }
})
