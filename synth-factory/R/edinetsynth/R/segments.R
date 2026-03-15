#' Extract a Single Segment from a Securities Report Dataset
#'
#' Pulls out one named segment column as a character vector, optionally
#' paired with the document ID for traceability.
#'
#' @param data A tibble returned by [load_securities_report()].
#' @param segment_name Character. Name of the segment to extract.
#'   Can be the full column name (e.g. `"seg_company_overview"`) or the
#'   short name (e.g. `"company_overview"`).
#' @param with_id Logical. If `TRUE` (default), return a two-column tibble
#'   with `document_id` and the segment text. If `FALSE`, return a plain
#'   character vector.
#'
#' @return A tibble or character vector depending on `with_id`.
#'
#' @examples
#' \dontrun{
#' reports <- load_securities_report("reports.jsonl")
#' risks <- extract_segment(reports, "business_risks")
#' head(risks)
#' }
#'
#' @importFrom dplyr select all_of
#' @importFrom rlang .data
#' @export
extract_segment <- function(data, segment_name, with_id = TRUE) {
  # Normalise: allow both "company_overview" and "seg_company_overview"
  col <- segment_name
  if (!col %in% names(data)) {
    col <- paste0("seg_", segment_name)
  }
  if (!col %in% names(data)) {
    available <- grep("^seg_", names(data), value = TRUE)
    stop(
      "Segment '", segment_name, "' not found. Available segments: ",
      paste(gsub("^seg_", "", available), collapse = ", "),
      call. = FALSE
    )
  }

  if (with_id) {
    id_col <- if ("document_id" %in% names(data)) "document_id" else NULL
    if (is.null(id_col)) {
      # Fall back to row numbers
      out <- dplyr::select(data, dplyr::all_of(col))
      out$document_id <- seq_len(nrow(out))
      out <- out[, c("document_id", col)]
    } else {
      out <- dplyr::select(data, dplyr::all_of(c(id_col, col)))
    }
    return(out)
  }

  data[[col]]
}


#' Segment-Level Summary Statistics
#'
#' Computes character counts, token estimates, and emptiness rates for
#' each `seg_*` column in the dataset.
#'
#' @param data A tibble returned by [load_securities_report()].
#'
#' @return A tibble with one row per segment and columns:
#'   `segment`, `n`, `mean_chars`, `median_chars`, `sd_chars`,
#'   `min_chars`, `max_chars`, `pct_empty`, `est_tokens`.
#'
#' @examples
#' \dontrun{
#' reports <- load_securities_report("reports.jsonl")
#' segment_summary(reports)
#' }
#'
#' @importFrom dplyr mutate group_by summarise
#' @importFrom tidyr pivot_longer
#' @importFrom rlang .data
#' @export
segment_summary <- function(data) {
  seg_cols <- grep("^seg_", names(data), value = TRUE)

  if (length(seg_cols) == 0L) {
    message("No segment columns (seg_*) found in data.")
    return(
      dplyr::tibble(
        segment = character(),
        n = integer(),
        mean_chars = double(),
        median_chars = double(),
        sd_chars = double(),
        min_chars = integer(),
        max_chars = integer(),
        pct_empty = double(),
        est_tokens = double()
      )
    )
  }

  # Pivot to long format
  long <- tidyr::pivot_longer(
    data,
    cols = dplyr::all_of(seg_cols),
    names_to = "segment",
    values_to = "text"
  )

  long <- dplyr::mutate(
    long,
    segment = gsub("^seg_", "", .data$segment),
    char_count = nchar(as.character(.data$text)),
    is_empty = is.na(.data$text) | nchar(as.character(.data$text)) == 0L
  )

  dplyr::group_by(long, .data$segment) |>
    dplyr::summarise(
      n = dplyr::n(),
      mean_chars = mean(.data$char_count, na.rm = TRUE),
      median_chars = stats::median(.data$char_count, na.rm = TRUE),
      sd_chars = stats::sd(.data$char_count, na.rm = TRUE),
      min_chars = min(.data$char_count, na.rm = TRUE),
      max_chars = max(.data$char_count, na.rm = TRUE),
      pct_empty = mean(.data$is_empty) * 100,
      # Japanese: ~1.5 chars/token; English: ~4 chars/token
      # Use 2.0 as a blend for mixed JP content
      est_tokens = mean(.data$char_count / 2.0, na.rm = TRUE),
      .groups = "drop"
    )
}
