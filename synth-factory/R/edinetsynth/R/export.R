#' Export Dataset to Hugging Face Format
#'
#' Converts an edinetsynth tibble to the JSONL format expected by
#' the Hugging Face `datasets` library, with optional train/test split.
#' Handles UTF-8 encoding correctly for Japanese text, avoiding the
#' encoding nightmares of CSV round-tripping between R and Python.
#'
#' After export, load in Python with:
#' \preformatted{
#' from datasets import load_dataset
#' ds = load_dataset("json", data_files={
#'     "train": "output/train.jsonl",
#'     "test": "output/test.jsonl"
#' })
#' }
#'
#' @param data A tibble returned by [load_securities_report()].
#' @param output_dir Character. Directory to write JSONL files.
#'   Created if it does not exist.
#' @param test_split Numeric between 0 and 1. Fraction of data for
#'   the test set. Default 0.2.
#' @param seed Integer. Random seed for reproducible splits.
#' @param stratify_by Optional character. Column name to stratify the
#'   split by (e.g., `"quality_tier"`). Ensures each split has
#'   proportional representation of each level.
#'
#' @return Invisibly, a list with `train_path`, `test_path`, `n_train`,
#'   `n_test`, and `columns`.
#'
#' @examples
#' \dontrun{
#' reports <- load_securities_report("reports.jsonl")
#' result <- export_to_hf_dataset(reports, output_dir = "hf_data/",
#'                                 stratify_by = "quality_tier")
#' cat("Train:", result$n_train, "Test:", result$n_test, "\n")
#' }
#'
#' @importFrom jsonlite toJSON
#' @export
export_to_hf_dataset <- function(data, output_dir = "hf_export",
                                  test_split = 0.2, seed = 42,
                                  stratify_by = NULL) {
  if (!dir.exists(output_dir)) {
    dir.create(output_dir, recursive = TRUE)
  }

  set.seed(seed)
  n <- nrow(data)

  if (!is.null(stratify_by) && stratify_by %in% names(data)) {
    # Stratified split
    test_idx <- integer(0)
    for (level in unique(data[[stratify_by]])) {
      level_idx <- which(data[[stratify_by]] == level)
      n_test <- max(1L, round(length(level_idx) * test_split))
      test_idx <- c(test_idx, sample(level_idx, n_test))
    }
  } else {
    n_test <- max(1L, round(n * test_split))
    test_idx <- sample(seq_len(n), n_test)
  }

  train_idx <- setdiff(seq_len(n), test_idx)

  # Write JSONL (one JSON object per line, UTF-8)
  write_jsonl <- function(df, path) {
    con <- file(path, open = "w", encoding = "UTF-8")
    on.exit(close(con), add = TRUE)
    for (i in seq_len(nrow(df))) {
      row <- as.list(df[i, , drop = FALSE])
      # Unlist single-element lists for clean JSON
      row <- lapply(row, function(x) if (length(x) == 1) x[[1]] else x)
      line <- jsonlite::toJSON(row, auto_unbox = TRUE, na = "null")
      writeLines(as.character(line), con)
    }
  }

  train_path <- file.path(output_dir, "train.jsonl")
  test_path <- file.path(output_dir, "test.jsonl")

  write_jsonl(data[train_idx, , drop = FALSE], train_path)
  write_jsonl(data[test_idx, , drop = FALSE], test_path)

  # Write a dataset_info.json for HF compatibility
  info <- list(
    description = "VilseckKI Synthetic EDINET Dataset",
    features = lapply(names(data), function(nm) {
      list(name = nm, dtype = if (is.numeric(data[[nm]])) "float64" else "string")
    }),
    splits = list(
      train = list(num_examples = length(train_idx)),
      test = list(num_examples = length(test_idx))
    ),
    source = "edinetsynth R package"
  )
  writeLines(
    jsonlite::toJSON(info, auto_unbox = TRUE, pretty = TRUE),
    file.path(output_dir, "dataset_info.json")
  )

  message("Exported ", length(train_idx), " train + ", length(test_idx),
          " test documents to: ", output_dir)

  invisible(list(
    train_path = train_path,
    test_path = test_path,
    n_train = length(train_idx),
    n_test = length(test_idx),
    columns = names(data)
  ))
}
