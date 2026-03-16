# ==========================================================================
# Tests for plot_advanced_quality() and plot_fsa_verification_summary()
# ==========================================================================

library(jsonlite)

# ── Helper: generate a realistic JSONL dataset with tiers and flaws ──────

make_tiered_jsonl <- function(n = 20) {
  tmp <- tempfile(fileext = ".jsonl")
  tiers <- c("perfect", "near", "moderate", "severe")
  tier_weights <- c(5, 7, 5, 3)  # rough distribution for n=20

  docs <- list()
  idx <- 1
  for (i in seq_len(n)) {
    tier <- tiers[((i - 1) %% 4) + 1]
    doc_id <- sprintf("DOC-%04d", i)

    # Base good content for all tiers
    co <- paste(rep("\u682a\u5f0f\u4f1a\u793e\u306e\u6982\u8981\u3067\u3059\u3002", 10), collapse = "")
    bs <- paste(rep("\u4e8b\u696d\u306e\u72b6\u6cc1\u306b\u3064\u3044\u3066\u8aac\u660e\u3057\u307e\u3059\u3002", 10), collapse = "")

    # Risks: Tier 1 = specific, Tier 4 = vague
    if (tier == "perfect") {
      br <- paste(
        "\u70ba\u66ff\u30ea\u30b9\u30af\u306f\u524d\u5e74\u5ea6\u6bd4120%\u306e\u5f71\u97ff\u304c\u3042\u308a\u307e\u3059\u3002",
        "\u5317\u7c73\u5e02\u5834\u306b\u304a\u3051\u308b\u7af6\u4e89\u6fc0\u5316\u306e\u30ea\u30b9\u30af\u304c\u3042\u308a\u307e\u3059\u3002",
        paste(rep("\u8a73\u7d30\u306a\u30ea\u30b9\u30af\u5206\u6790\u3002", 8), collapse = "")
      )
    } else if (tier == "severe") {
      # Vague risk — should trigger flaw detection
      br <- paste(
        "\u69d8\u3005\u306a\u30ea\u30b9\u30af\u304c\u3042\u308a\u307e\u3059\u3002",
        "\u4e0d\u900f\u660e\u306a\u8981\u56e0\u304c\u5b58\u5728\u3057\u307e\u3059\u3002",
        paste(rep("\u30ea\u30b9\u30af\u304c\u3042\u308a\u307e\u3059\u3002", 8), collapse = "")
      )
    } else {
      br <- paste(rep("\u30ea\u30b9\u30af\u306b\u3064\u3044\u3066\u8aac\u660e\u3057\u307e\u3059\u3002", 10), collapse = "")
    }

    mda <- paste(rep("\u7d4c\u55b6\u8005\u306b\u3088\u308b\u5206\u6790\u3002", 10), collapse = "")

    doc <- list(
      document_id = doc_id,
      quality_tier = tier,
      seg_company_overview = co,
      seg_business_status = bs,
      seg_business_risks = br,
      seg_md_and_a = mda
    )
    docs[[idx]] <- doc
    idx <- idx + 1
  }

  lines <- vapply(docs, function(d) toJSON(d, auto_unbox = TRUE), character(1))
  writeLines(lines, tmp)
  tmp
}


# ── Tests: plot_advanced_quality() ──────────────────────────────────────

test_that("plot_advanced_quality creates output directory", {
  path <- make_tiered_jsonl(12)
  on.exit(unlink(path))

  data <- load_securities_report(path)
  out_dir <- file.path(tempdir(), "test_adv_plots")
  if (dir.exists(out_dir)) unlink(out_dir, recursive = TRUE)

  result <- plot_advanced_quality(data, output_dir = out_dir)

  expect_true(dir.exists(out_dir))
  # Clean up
  unlink(out_dir, recursive = TRUE)
})

test_that("plot_advanced_quality returns named list of paths", {
  path <- make_tiered_jsonl(12)
  on.exit(unlink(path))

  data <- load_securities_report(path)
  out_dir <- file.path(tempdir(), "test_adv_paths")

  result <- plot_advanced_quality(data, output_dir = out_dir)

  expect_type(result, "list")
  # Should have at least the section quality scorecard (always available)
  expect_true(length(result) >= 1)

  # All returned values should be file paths that exist
  for (p in result) {
    expect_true(file.exists(p), info = paste("Missing:", p))
  }

  unlink(out_dir, recursive = TRUE)
})

test_that("plot_advanced_quality generates heatmap when flaws are detected", {
  path <- make_tiered_jsonl(20)
  on.exit(unlink(path))

  data <- load_securities_report(path)
  flaws <- detect_flaws(data)

  # Only expect heatmap if there are actual flaws AND quality_tier column
  if (nrow(flaws) > 0 && "quality_tier" %in% names(data)) {
    out_dir <- file.path(tempdir(), "test_heatmap")
    result <- plot_advanced_quality(data, output_dir = out_dir)

    expect_true("flaw_survival_heatmap" %in% names(result))
    expect_true(file.exists(result$flaw_survival_heatmap))
    # File should be non-trivial
    expect_true(file.info(result$flaw_survival_heatmap)$size > 1000)

    unlink(out_dir, recursive = TRUE)
  }
})

test_that("plot_advanced_quality generates tier density chart", {
  path <- make_tiered_jsonl(20)
  on.exit(unlink(path))

  data <- load_securities_report(path)
  flaws <- detect_flaws(data)

  if ("quality_tier" %in% names(data) && nrow(flaws) > 0) {
    out_dir <- file.path(tempdir(), "test_tier_density")
    result <- plot_advanced_quality(data, output_dir = out_dir)

    expect_true("tier_flaw_density" %in% names(result))
    expect_true(file.exists(result$tier_flaw_density))

    unlink(out_dir, recursive = TRUE)
  }
})

test_that("plot_advanced_quality generates section scorecard", {
  path <- make_tiered_jsonl(10)
  on.exit(unlink(path))

  data <- load_securities_report(path)
  out_dir <- file.path(tempdir(), "test_scorecard")
  result <- plot_advanced_quality(data, output_dir = out_dir)

  # Section scorecard should always generate when there are 3+ seg_ columns
  expect_true("section_quality_scorecard" %in% names(result))
  expect_true(file.exists(result$section_quality_scorecard))
  expect_true(file.info(result$section_quality_scorecard)$size > 1000)

  unlink(out_dir, recursive = TRUE)
})

test_that("plot_advanced_quality custom dimensions work", {
  path <- make_tiered_jsonl(8)
  on.exit(unlink(path))

  data <- load_securities_report(path)
  out_dir <- file.path(tempdir(), "test_dims")
  result <- plot_advanced_quality(
    data,
    output_dir = out_dir,
    width = 8, height = 5, dpi = 100
  )

  # Should still produce output

  expect_true(length(result) >= 1)

  unlink(out_dir, recursive = TRUE)
})


# ── Tests: plot_fsa_verification_summary() ──────────────────────────────

test_that("plot_fsa_verification_summary generates with sample data", {
  out_dir <- file.path(tempdir(), "test_fsa_summary")
  if (!dir.exists(out_dir)) dir.create(out_dir, recursive = TRUE)
  out_path <- file.path(out_dir, "fsa_summary.png")

  # NULL flaw_summary triggers sample data fallback
  result <- plot_fsa_verification_summary(
    flaw_summary = NULL,
    output_path = out_path
  )

  expect_equal(result, out_path)
  expect_true(file.exists(out_path))
  expect_true(file.info(out_path)$size > 5000)  # Non-trivial PNG

  unlink(out_dir, recursive = TRUE)
})

test_that("plot_fsa_verification_summary works with custom data", {
  out_dir <- file.path(tempdir(), "test_fsa_custom")
  if (!dir.exists(out_dir)) dir.create(out_dir, recursive = TRUE)
  out_path <- file.path(out_dir, "fsa_custom.png")

  custom_summary <- data.frame(
    flaw_id = c("FLAW_A", "FLAW_B"),
    flaw_name = c("Test Flaw Alpha", "Test Flaw Beta"),
    planted_count = c(100, 50),
    detected_count = c(95, 48),
    survival_rate = c(0.95, 0.96),
    detection_method = c("keyword", "LLM"),
    severity = c("critical", "moderate"),
    stringsAsFactors = FALSE
  )

  result <- plot_fsa_verification_summary(
    flaw_summary = custom_summary,
    output_path = out_path
  )

  expect_equal(result, out_path)
  expect_true(file.exists(out_path))

  unlink(out_dir, recursive = TRUE)
})

test_that("plot_fsa_verification_summary creates output directory", {
  out_dir <- file.path(tempdir(), "test_fsa_newdir", "nested")
  out_path <- file.path(out_dir, "fsa.png")

  result <- plot_fsa_verification_summary(output_path = out_path)

  expect_true(dir.exists(out_dir))
  expect_true(file.exists(out_path))

  unlink(file.path(tempdir(), "test_fsa_newdir"), recursive = TRUE)
})

test_that("plot_fsa_verification_summary returns path invisibly", {
  out_dir <- file.path(tempdir(), "test_fsa_invisible")
  out_path <- file.path(out_dir, "fsa.png")

  # Capture the invisible return
  result <- plot_fsa_verification_summary(output_path = out_path)
  expect_type(result, "character")
  expect_equal(result, out_path)

  unlink(out_dir, recursive = TRUE)
})

test_that("plot_fsa_verification_summary handles all severity levels", {
  out_dir <- file.path(tempdir(), "test_fsa_sev")
  out_path <- file.path(out_dir, "fsa.png")

  summary_all_sev <- data.frame(
    flaw_id = c("A", "B", "C"),
    flaw_name = c("Critical Flaw", "Moderate Flaw", "Low Flaw"),
    planted_count = c(30, 20, 10),
    detected_count = c(29, 19, 10),
    survival_rate = c(0.967, 0.95, 1.0),
    detection_method = c("keyword", "LLM", "keyword"),
    severity = c("critical", "moderate", "low"),
    stringsAsFactors = FALSE
  )

  result <- plot_fsa_verification_summary(
    flaw_summary = summary_all_sev,
    output_path = out_path
  )

  expect_true(file.exists(out_path))
  unlink(out_dir, recursive = TRUE)
})
