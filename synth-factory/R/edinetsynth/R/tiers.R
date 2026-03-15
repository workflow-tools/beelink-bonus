#' Compare Quality Tiers in a Mixed Dataset
#'
#' Summarises the distribution of quality tiers and computes per-tier
#' statistics on segment lengths, error rates, and flaw counts.
#'
#' @param data A tibble returned by [load_securities_report()].
#'   Must contain a `quality_tier` column (present in mixed-tier datasets).
#'
#' @return A tibble with one row per tier and columns:
#'   `quality_tier`, `n`, `pct`, `mean_error_rate`,
#'   `mean_seg_chars`, `expected_pct`, `deviation`.
#'
#' @details
#' The expected tier distribution from the synth-factory defaults is:
#' perfect = 80%, near = 10%, moderate = 8%, severe = 2%.
#' The `deviation` column shows how far the observed distribution
#' is from these defaults (useful for marketplace QA claims).
#'
#' @examples
#' \dontrun{
#' reports <- load_securities_report("mixed_reports.jsonl")
#' compare_tiers(reports)
#' }
#'
#' @importFrom dplyr group_by summarise mutate n
#' @importFrom rlang .data
#' @export
compare_tiers <- function(data) {
  if (!"quality_tier" %in% names(data)) {
    message("No 'quality_tier' column found. ",
            "This dataset may not use mixed quality tiers.")
    return(
      dplyr::tibble(
        quality_tier = character(),
        n = integer(),
        pct = double(),
        mean_error_rate = double(),
        mean_seg_chars = double(),
        expected_pct = double(),
        deviation = double()
      )
    )
  }

  # Expected defaults from synth-factory
  expected <- c(
    perfect  = 80.0,
    near     = 10.0,
    moderate =  8.0,
    severe   =  2.0
  )

  seg_cols <- grep("^seg_", names(data), value = TRUE)
  total <- nrow(data)

  tier_stats <- dplyr::group_by(data, .data$quality_tier) |>
    dplyr::summarise(
      n = dplyr::n(),
      pct = dplyr::n() / total * 100,
      mean_error_rate = if ("error_rate" %in% names(data))
        mean(.data$error_rate, na.rm = TRUE) else NA_real_,
      mean_seg_chars = if (length(seg_cols) > 0)
        mean(rowMeans(
          sapply(seg_cols, function(s) nchar(as.character(.data[[s]])),
                 USE.NAMES = FALSE),
          na.rm = TRUE
        ), na.rm = TRUE) else NA_real_,
      .groups = "drop"
    )

  # Add expected distribution and deviation
  tier_stats <- dplyr::mutate(
    tier_stats,
    expected_pct = expected[as.character(.data$quality_tier)],
    deviation = .data$pct - .data$expected_pct
  )

  # Order by tier severity
  tier_order <- c("perfect", "near", "moderate", "severe")
  tier_stats$quality_tier <- factor(
    tier_stats$quality_tier,
    levels = tier_order
  )
  tier_stats <- tier_stats[order(tier_stats$quality_tier), ]
  tier_stats$quality_tier <- as.character(tier_stats$quality_tier)

  # Run one-way ANOVA: does quality_tier significantly predict flaw count?
  # Attach result as an attribute — researchers love p-values.
  tryCatch({
    flaws <- detect_flaws(data, return_snippets = FALSE)
    if (nrow(flaws) > 0 && "quality_tier" %in% names(data)) {
      flaw_counts <- dplyr::count(flaws, .data$document_id, name = "flaw_n")
      merged <- merge(
        data[, c("document_id", "quality_tier"), drop = FALSE],
        flaw_counts,
        by = "document_id", all.x = TRUE
      )
      merged$flaw_n[is.na(merged$flaw_n)] <- 0L
      if (length(unique(merged$quality_tier)) > 1) {
        aov_result <- stats::aov(flaw_n ~ quality_tier, data = merged)
        aov_summary <- summary(aov_result)
        attr(tier_stats, "anova_flaw_tier") <- aov_summary
        f_stat <- aov_summary[[1]][["F value"]][1]
        p_val <- aov_summary[[1]][["Pr(>F)"]][1]
        attr(tier_stats, "tier_flaw_f") <- f_stat
        attr(tier_stats, "tier_flaw_p") <- p_val
      }
    }
  }, error = function(e) {
    # Silently skip if ANOVA fails — it's a bonus feature
  })

  tier_stats
}
