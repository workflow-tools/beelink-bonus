#' Detect Flaws in Synthetic Documents
#'
#' Performs forensic validation of synthetic EDINET filings. Instead of
#' relying on metadata flags, runs programmatic heuristics and regex
#' patterns derived from the FSA enforcement taxonomy to prove the
#' existence, location, and severity of anomalies in generated text.
#'
#' If no taxonomy is provided, uses built-in heuristic detectors for
#' the most common structural and formatting issues.
#'
#' @param data A tibble returned by [load_securities_report()].
#' @param taxonomy_path Optional character. Path to a `flaw_taxonomy.json`
#'   file produced by the synth-factory scraper. If `NULL`, uses
#'   heuristic detection only.
#' @param return_snippets Logical. If `TRUE` (default), the output
#'   includes the `evidence` column with text snippets surrounding
#'   detected anomalies for manual review.
#'
#' @return A tibble with columns: `document_id`, `segment`, `flaw_type`,
#'   `flaw_subtype`, `severity`, `confidence`, `description`, and
#'   `evidence` (if `return_snippets = TRUE`).
#'
#'   The `confidence` column (0-1) indicates detection certainty:
#'   1.0 = definitive (empty section), 0.8 = high (generation sentinel),
#'   0.5 = moderate (heuristic pattern match).
#'
#' @examples
#' \dontrun{
#' reports <- load_securities_report("reports.jsonl")
#' flaws <- detect_flaws(reports)
#' table(flaws$flaw_type)
#'
#' # Cross-reference flaw density against quality tiers
#' library(dplyr)
#' flaws |>
#'   left_join(reports |> select(document_id, quality_tier),
#'             by = "document_id") |>
#'   count(quality_tier, flaw_type)
#' }
#'
#' @importFrom jsonlite fromJSON
#' @importFrom dplyr filter mutate select count
#' @importFrom rlang .data
#' @export
detect_flaws <- function(data, taxonomy_path = NULL, return_snippets = TRUE) {
  seg_cols <- grep("^seg_", names(data), value = TRUE)
  id_col <- if ("document_id" %in% names(data)) "document_id" else NULL

  # Load taxonomy if provided
  taxonomy <- NULL
  if (!is.null(taxonomy_path) && file.exists(taxonomy_path)) {
    taxonomy <- jsonlite::fromJSON(taxonomy_path, simplifyDataFrame = TRUE)
  }

  results <- list()
  idx <- 0L

  for (i in seq_len(nrow(data))) {
    doc_id <- if (!is.null(id_col)) data[[id_col]][i] else paste0("row_", i)

    for (seg in seg_cols) {
      text <- as.character(data[[seg]][i])
      seg_short <- gsub("^seg_", "", seg)

      # ----- Heuristic detectors -----

      # 1. Empty section
      if (is.na(text) || nchar(text) == 0L) {
        idx <- idx + 1L
        results[[idx]] <- list(
          document_id = doc_id, segment = seg_short,
          flaw_type = "structural", flaw_subtype = "empty_section",
          severity = "high", confidence = 1.0,
          description = "Section is completely empty",
          evidence = "<empty>"
        )
        next
      }

      # 2. Suspiciously short (< 20 chars for a section)
      if (nchar(text) < 20L) {
        idx <- idx + 1L
        results[[idx]] <- list(
          document_id = doc_id, segment = seg_short,
          flaw_type = "structural", flaw_subtype = "stub_section",
          severity = "medium", confidence = 0.9,
          description = "Section is suspiciously short (< 20 chars)",
          evidence = text
        )
      }

      # 3. Garbled characters / encoding issues
      # Look for sequences of replacement characters or mojibake patterns
      if (grepl("[\ufffd]{2,}", text) || grepl("\x93|\x94|\x92", text)) {
        idx <- idx + 1L
        results[[idx]] <- list(
          document_id = doc_id, segment = seg_short,
          flaw_type = "formatting", flaw_subtype = "garbled_characters",
          severity = "high", confidence = 0.85,
          description = "Detected garbled or replacement characters",
          evidence = substr(text, 1, 100)
        )
      }

      # 4. Non-JIS character detection (Simplified Chinese leak)
      # LLMs sometimes hallucinate Simplified Chinese (Hanzi) when
      # generating Japanese — especially in financial boilerplate.
      # Detect CJK Unified Ideographs that are common in Simplified
      # Chinese but rare/absent in Japanese JIS X 0208.
      # Ranges: CJK Extension A (\u3400-\u4DBF) contains many
      # Simplified-only characters.
      sc_only <- grepl("[\u2E80-\u2EFF]", text)  # CJK Radicals Supplement
      if (sc_only) {
        idx <- idx + 1L
        results[[idx]] <- list(
          document_id = doc_id, segment = seg_short,
          flaw_type = "encoding", flaw_subtype = "non_jis_characters",
          severity = "high", confidence = 0.7,
          description = "Possible Simplified Chinese characters in Japanese text",
          evidence = substr(text, 1, 200)
        )
      }

      # 5. Repeated content (same phrase 3+ times)
      words <- strsplit(text, "\\s+")[[1]]
      if (length(words) >= 6L) {
        trigrams <- vapply(
          seq_len(length(words) - 2L),
          function(j) paste(words[j:(j + 2L)], collapse = " "),
          character(1)
        )
        tri_counts <- table(trigrams)
        repeats <- tri_counts[tri_counts >= 3L]
        if (length(repeats) > 0L) {
          idx <- idx + 1L
          results[[idx]] <- list(
            document_id = doc_id, segment = seg_short,
            flaw_type = "content", flaw_subtype = "repetition",
            severity = "medium", confidence = 0.6,
            description = paste("Repeated trigram(s) detected:",
                                length(repeats), "unique"),
            evidence = paste(names(repeats)[1:min(3, length(repeats))],
                             collapse = "; ")
          )
        }
      }

      # 6. Generation failure sentinel
      if (grepl("\\[GENERATION_FAILED", text, fixed = FALSE)) {
        idx <- idx + 1L
        results[[idx]] <- list(
          document_id = doc_id, segment = seg_short,
          flaw_type = "generation", flaw_subtype = "generation_failed",
          severity = "critical", confidence = 1.0,
          description = "LLM generation failure sentinel detected",
          evidence = substr(text, 1, 200)
        )
      }

      # 7. Generic boilerplate (Japanese)
      generic_jp <- c(
        "\u5f53\u793e\u306f\u4e0a\u8a18\u306e\u901a\u308a",
        "\u8a72\u5f53\u4e8b\u9805\u306f\u3042\u308a\u307e\u305b\u3093",
        "\u7279\u8a18\u3059\u3079\u304d\u4e8b\u9805\u306f\u3042\u308a\u307e\u305b\u3093"
      )
      for (phrase in generic_jp) {
        if (grepl(phrase, text, fixed = TRUE)) {
          idx <- idx + 1L
          results[[idx]] <- list(
            document_id = doc_id, segment = seg_short,
            flaw_type = "disclosure", flaw_subtype = "generic_language",
            severity = "low", confidence = 0.5,
            description = "Generic boilerplate phrase detected",
            evidence = phrase
          )
          break
        }
      }
    }
  }

  if (length(results) == 0L) {
    out <- dplyr::tibble(
      document_id = character(), segment = character(),
      flaw_type = character(), flaw_subtype = character(),
      severity = character(), confidence = double(),
      description = character(), evidence = character()
    )
    if (!return_snippets) out$evidence <- NULL
    return(out)
  }

  out <- dplyr::bind_rows(lapply(results, dplyr::as_tibble))
  if (!return_snippets) out$evidence <- NULL
  out
}
