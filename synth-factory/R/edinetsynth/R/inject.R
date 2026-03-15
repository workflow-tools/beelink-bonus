#' Inject Anomalies into Synthetic Documents
#'
#' Allows researchers to experiment with flaw injection locally before
#' purchasing the full enterprise-scale generation. This transitions
#' the product from a static dataset to a dynamic simulation environment.
#'
#' Applies deterministic text mutations to a clean dataset, simulating
#' the kinds of flaws found in real EDINET filings. Useful for:
#' - Generating training data for flaw-detection models
#' - Stress-testing document processing pipelines
#' - Understanding what each flaw type looks like in practice
#'
#' @param data A tibble returned by [load_securities_report()].
#' @param flaw_type Character. Type of flaw to inject. One of:
#'   `"empty_section"`, `"stub_section"`, `"repetition"`,
#'   `"generic_language"`, `"garbled_characters"`.
#' @param rate Numeric between 0 and 1. Fraction of documents to
#'   affect. Default 0.1 (10%).
#' @param segments Optional character vector of segment names to target.
#'   If `NULL` (default), a random segment is chosen per document.
#' @param seed Integer for reproducibility.
#'
#' @return A modified tibble with an `injected_flaw` column indicating
#'   which documents were modified and how.
#'
#' @examples
#' \dontrun{
#' reports <- load_securities_report("perfect_reports.jsonl")
#'
#' # Inject empty sections into 20% of documents
#' flawed <- inject_anomalies(reports, flaw_type = "empty_section", rate = 0.2)
#'
#' # Inject repetition into specific segments
#' flawed <- inject_anomalies(reports, flaw_type = "repetition",
#'                             segments = c("business_risks", "md_and_a"))
#'
#' # Verify the injection worked
#' detect_flaws(flawed)
#' }
#'
#' @export
inject_anomalies <- function(data, flaw_type = "empty_section",
                              rate = 0.1, segments = NULL, seed = 42) {
  valid_types <- c("empty_section", "stub_section", "repetition",
                   "generic_language", "garbled_characters")
  if (!flaw_type %in% valid_types) {
    stop("Unknown flaw_type: '", flaw_type, "'. Must be one of: ",
         paste(valid_types, collapse = ", "), call. = FALSE)
  }

  set.seed(seed)
  n <- nrow(data)
  n_affected <- max(1L, round(n * rate))
  affected_idx <- sample(seq_len(n), n_affected)

  seg_cols <- grep("^seg_", names(data), value = TRUE)
  if (length(seg_cols) == 0L) {
    stop("No segment columns (seg_*) found in data.", call. = FALSE)
  }

  # Resolve target segments
  if (!is.null(segments)) {
    target_cols <- paste0("seg_", segments)
    target_cols <- target_cols[target_cols %in% seg_cols]
    if (length(target_cols) == 0L) {
      stop("None of the specified segments found. Available: ",
           paste(gsub("^seg_", "", seg_cols), collapse = ", "),
           call. = FALSE)
    }
  } else {
    target_cols <- seg_cols
  }

  # Track injections
  data$injected_flaw <- NA_character_

  for (i in affected_idx) {
    # Pick a random target segment for this document
    col <- sample(target_cols, 1)
    text <- as.character(data[[col]][i])

    mutated <- switch(flaw_type,
      empty_section = "",

      stub_section = substr(text, 1, min(15, nchar(text))),

      repetition = {
        words <- strsplit(text, "\\s+")[[1]]
        if (length(words) >= 3) {
          phrase <- paste(words[1:min(3, length(words))], collapse = " ")
          paste(rep(phrase, 8), collapse = " ")
        } else {
          paste(rep(text, 5), collapse = " ")
        }
      },

      generic_language = {
        # Replace content with common boilerplate
        boilerplate <- c(
          "\u8a72\u5f53\u4e8b\u9805\u306f\u3042\u308a\u307e\u305b\u3093\u3002",
          "\u7279\u8a18\u3059\u3079\u304d\u4e8b\u9805\u306f\u3042\u308a\u307e\u305b\u3093\u3002",
          "\u5f53\u793e\u306f\u4e0a\u8a18\u306e\u901a\u308a\u3067\u3059\u3002"
        )
        paste(sample(boilerplate, 3, replace = TRUE), collapse = "\n")
      },

      garbled_characters = {
        # Insert replacement characters to simulate encoding issues
        chars <- strsplit(text, "")[[1]]
        if (length(chars) > 10) {
          inject_pos <- sample(seq_along(chars), min(5, length(chars)))
          chars[inject_pos] <- "\ufffd"
        }
        paste(chars, collapse = "")
      }
    )

    data[[col]][i] <- mutated
    data$injected_flaw[i] <- paste0(flaw_type, ":", gsub("^seg_", "", col))
  }

  message("Injected '", flaw_type, "' into ", n_affected, " of ", n,
          " documents (", round(rate * 100), "%)")
  data
}
