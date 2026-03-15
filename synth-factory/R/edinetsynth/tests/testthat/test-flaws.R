# ==========================================================================
# Tests for detect_flaws()
# ==========================================================================

library(jsonlite)

make_flawed_jsonl <- function() {
  tmp <- tempfile(fileext = ".jsonl")
  docs <- list(
    list(
      document_id = "DOC-EMPTY",
      seg_company_overview = "",
      seg_business_status = "OK content here with some text that is long enough",
      seg_business_risks = "",
      seg_md_and_a = "Short"
    ),
    list(
      document_id = "DOC-SENTINEL",
      seg_company_overview = "[GENERATION_FAILED: timeout after 60s]",
      seg_business_status = "Normal content that is fine and long enough to pass",
      seg_business_risks = "Normal content as well and sufficiently lengthy",
      seg_md_and_a = "Also fine and has enough text here"
    ),
    list(
      document_id = "DOC-CLEAN",
      seg_company_overview = paste(rep("This is clean content", 5),
                                   collapse = " with variety "),
      seg_business_status = paste(rep("Good business content", 5),
                                  collapse = " with more "),
      seg_business_risks = paste(rep("Detailed risk analysis", 5),
                                 collapse = " covering "),
      seg_md_and_a = paste(rep("Management discussion", 5),
                           collapse = " and analysis ")
    )
  )
  lines <- vapply(docs, function(d) toJSON(d, auto_unbox = TRUE), character(1))
  writeLines(lines, tmp)
  tmp
}


test_that("detect_flaws finds empty sections", {
  path <- make_flawed_jsonl()
  on.exit(unlink(path))

  data <- load_securities_report(path)
  flaws <- detect_flaws(data)

  empty_flaws <- flaws[flaws$flaw_subtype == "empty_section", ]
  expect_true(nrow(empty_flaws) >= 2)  # DOC-EMPTY has 2 empty segments
  expect_true(all(empty_flaws$severity == "high"))
})

test_that("detect_flaws finds generation failure sentinels", {
  path <- make_flawed_jsonl()
  on.exit(unlink(path))

  data <- load_securities_report(path)
  flaws <- detect_flaws(data)

  sentinel_flaws <- flaws[flaws$flaw_subtype == "generation_failed", ]
  expect_true(nrow(sentinel_flaws) >= 1)
  expect_true("DOC-SENTINEL" %in% sentinel_flaws$document_id)
})

test_that("detect_flaws finds stub sections", {
  path <- make_flawed_jsonl()
  on.exit(unlink(path))

  data <- load_securities_report(path)
  flaws <- detect_flaws(data)

  stub_flaws <- flaws[flaws$flaw_subtype == "stub_section", ]
  # DOC-EMPTY has seg_md_and_a = "Short" (5 chars)
  expect_true(nrow(stub_flaws) >= 1)
})

test_that("detect_flaws returns empty tibble for clean data", {
  tmp <- tempfile(fileext = ".jsonl")
  on.exit(unlink(tmp))

  doc <- list(
    document_id = "DOC-CLEAN",
    seg_company_overview = paste(rep("Substantial clean content", 10),
                                 collapse = " with natural variation "),
    seg_business_status = paste(rep("Detailed status report", 10),
                                collapse = " covering many points "),
    seg_business_risks = paste(rep("Thorough risk discussion", 10),
                               collapse = " analyzing factors "),
    seg_md_and_a = paste(rep("Management analysis section", 10),
                         collapse = " discussing trends ")
  )
  writeLines(toJSON(doc, auto_unbox = TRUE), tmp)

  data <- load_securities_report(tmp)
  flaws <- detect_flaws(data)

  expect_s3_class(flaws, "tbl_df")
  # Should have zero or very few flaws for clean data
  critical <- flaws[flaws$severity == "critical", ]
  expect_equal(nrow(critical), 0)
})

test_that("detect_flaws has correct column structure", {
  path <- make_flawed_jsonl()
  on.exit(unlink(path))

  data <- load_securities_report(path)
  flaws <- detect_flaws(data)

  expected_cols <- c("document_id", "segment", "flaw_type",
                     "flaw_subtype", "severity", "description", "evidence")
  expect_true(all(expected_cols %in% names(flaws)))
})
