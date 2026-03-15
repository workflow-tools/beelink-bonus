# ==========================================================================
# Tests for load_securities_report()
# ==========================================================================
#
# Run with:
#   Rscript -e "testthat::test_file('tests/testthat/test-load.R')"
#   (from the edinetsynth package root)
#
# Or via devtools::test() after devtools::load_all()
# ==========================================================================

library(jsonlite)

# ── Fixtures ────────────────────────────────────────────────────

make_test_jsonl <- function(n = 5, with_tiers = FALSE) {
  tmp <- tempfile(fileext = ".jsonl")
  tiers <- c("perfect", "near", "moderate", "severe")
  error_rates <- c(0.0, 0.03, 0.12, 0.30)

  lines <- vapply(seq_len(n), function(i) {
    doc <- list(
      document_id = sprintf("DOC-%06d", i),
      document_content = paste("Full document content for", i),
      seg_company_overview = paste(rep("企業概況テスト", sample(5:20, 1)),
                                   collapse = ""),
      seg_business_status = paste(rep("事業状況テスト", sample(5:15, 1)),
                                  collapse = ""),
      seg_business_risks = paste(rep("リスクテスト内容", sample(3:12, 1)),
                                 collapse = ""),
      seg_md_and_a = paste(rep("経営分析テスト", sample(8:25, 1)),
                           collapse = "")
    )
    if (with_tiers) {
      tier_idx <- sample(seq_along(tiers), 1,
                         prob = c(0.8, 0.1, 0.08, 0.02))
      doc$quality_tier <- tiers[tier_idx]
      doc$error_rate <- error_rates[tier_idx]
    }
    toJSON(doc, auto_unbox = TRUE)
  }, character(1))

  writeLines(lines, tmp)
  tmp
}

make_empty_jsonl <- function() {
  tmp <- tempfile(fileext = ".jsonl")
  writeLines("", tmp)
  tmp
}

make_flawed_jsonl <- function() {
  tmp <- tempfile(fileext = ".jsonl")
  docs <- list(
    list(
      document_id = "DOC-EMPTY",
      seg_company_overview = "",
      seg_business_status = "OK content here with some text",
      seg_business_risks = "",
      seg_md_and_a = "Short"
    ),
    list(
      document_id = "DOC-SENTINEL",
      seg_company_overview = "[GENERATION_FAILED: timeout after 60s]",
      seg_business_status = "Normal content that is fine",
      seg_business_risks = "Normal content as well",
      seg_md_and_a = "Also fine"
    ),
    list(
      document_id = "DOC-REPEAT",
      seg_company_overview = paste(rep("hello world test", 10), collapse = " "),
      seg_business_status = "Fine",
      seg_business_risks = "Fine",
      seg_md_and_a = "Fine"
    )
  )
  lines <- vapply(docs, function(d) toJSON(d, auto_unbox = TRUE), character(1))
  writeLines(lines, tmp)
  tmp
}


# ── load_securities_report ──────────────────────────────────────

test_that("load_securities_report reads valid JSONL", {
  path <- make_test_jsonl(10)
  on.exit(unlink(path))

  data <- load_securities_report(path)
  expect_s3_class(data, "tbl_df")
  expect_equal(nrow(data), 10)
  expect_true("document_id" %in% names(data))
  expect_true("seg_company_overview" %in% names(data))
})

test_that("load_securities_report attaches source metadata", {
  path <- make_test_jsonl(3)
  on.exit(unlink(path))

  data <- load_securities_report(path)
  expect_true(!is.null(attr(data, "source_path")))
  expect_true(!is.null(attr(data, "loaded_at")))
})

test_that("load_securities_report errors on missing file", {
  expect_error(
    load_securities_report("/nonexistent/path.jsonl"),
    "not found"
  )
})

test_that("load_securities_report errors on empty file", {
  path <- make_empty_jsonl()
  on.exit(unlink(path))

  expect_error(load_securities_report(path), "empty|No records")
})

test_that("load_securities_report reads tier columns when present", {
  path <- make_test_jsonl(20, with_tiers = TRUE)
  on.exit(unlink(path))

  data <- load_securities_report(path)
  expect_true("quality_tier" %in% names(data))
  expect_true("error_rate" %in% names(data))
  expect_true(all(data$quality_tier %in%
                    c("perfect", "near", "moderate", "severe")))
})
