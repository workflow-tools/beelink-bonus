#' Load a VilseckKI Synthetic Securities Report Dataset
#'
#' Reads a JSONL file produced by synth-factory and returns a tidy tibble
#' with one row per document. Segment columns are prefixed with `seg_`.
#'
#' @param path Character. Path to a `.jsonl` file.
#' @param simplify Logical. If `TRUE` (default), flatten nested JSON into
#'   top-level columns. Set `FALSE` to keep raw list-columns.
#'
#' @return A [tibble][dplyr::tibble] with columns for document metadata,
#'   quality tier, error rate, and segment text.
#'
#' @examples
#' \dontrun{
#' reports <- load_securities_report("securities_reports_mixed.jsonl")
#' nrow(reports)
#' names(reports)
#' }
#'
#' @importFrom jsonlite stream_in
#' @importFrom dplyr as_tibble
#' @export
load_securities_report <- function(path, simplify = TRUE) {
  if (!file.exists(path)) {
    stop("File not found: ", path, call. = FALSE)
  }

  info <- file.info(path)
  if (info$size == 0L) {
    stop("File is empty: ", path, call. = FALSE)
  }

  con <- file(path, open = "r")
  on.exit(close(con), add = TRUE)

  df <- jsonlite::stream_in(con, simplifyDataFrame = simplify, verbose = FALSE)

  if (nrow(df) == 0L) {
    stop("No records found in: ", path, call. = FALSE)
  }

  # Ensure tibble

  df <- dplyr::as_tibble(df)

  # Attach metadata as attributes for downstream use
  attr(df, "source_path") <- normalizePath(path, mustWork = FALSE)
  attr(df, "loaded_at") <- Sys.time()


  df
}
