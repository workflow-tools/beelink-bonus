#' Generate Sample EDINET Data for Package Demos
#'
#' Creates a small, self-contained JSONL dataset that mimics the structure
#' of a real VilseckKI synthetic EDINET corpus. Used for:
#' - Package vignettes and demos (no external data needed)
#' - HuggingFace dataset card examples
#' - Buyer evaluation without downloading the full dataset
#' - CI/CD testing of downstream NLP pipelines
#'
#' The generated data includes realistic Japanese financial Keigo, proper
#' quality tier distribution (80/10/8/2), and deliberately planted flaws
#' in Tier 2-4 documents that mirror the FSA compliance taxonomy.
#'
#' @param n Integer. Number of documents to generate. Default 50.
#' @param output_path Character or NULL. If provided, writes JSONL to disk
#'   and returns the path invisibly. If NULL (default), returns a tibble
#'   directly (same format as [load_securities_report()]).
#' @param seed Integer. Random seed for reproducibility. Default 42.
#'
#' @return If `output_path` is NULL, a tibble matching [load_securities_report()]
#'   output. If `output_path` is provided, the path is returned invisibly.
#'
#' @examples
#' # Get a tibble directly (no file I/O):
#' demo <- make_sample_data(n = 20)
#' nrow(demo)
#' names(demo)
#'
#' # Write to disk for use with load_securities_report():
#' path <- make_sample_data(n = 50, output_path = tempfile(fileext = ".jsonl"))
#' reports <- load_securities_report(path)
#'
#' # Full demo pipeline:
#' demo <- make_sample_data()
#' stats <- segment_summary(demo)
#' flaws <- detect_flaws(demo)
#' plot_quality_report(demo, output_dir = tempdir())
#'
#' @importFrom jsonlite toJSON stream_in
#' @importFrom dplyr as_tibble
#' @export
make_sample_data <- function(n = 50, output_path = NULL, seed = 42) {
  set.seed(seed)

  tiers <- c("perfect", "near", "moderate", "severe")
  error_rates <- c(0.0, 0.03, 0.12, 0.30)
  tier_probs <- c(0.80, 0.10, 0.08, 0.02)

  # ── Section generators ──────────────────────────────────────────
  # Each produces realistic Japanese financial text appropriate
  # for the quality tier. Tiers 3-4 contain deliberate flaws.

  gen_company_overview <- function(tier) {
    city <- sample(
      c("\u6771\u4eac\u90fd\u6e2f\u533a", "\u5927\u962a\u5e02\u5317\u533a",
        "\u540d\u53e4\u5c4b\u5e02\u4e2d\u533a", "\u798f\u5ca1\u5e02\u535a\u591a\u533a",
        "\u672d\u5e4c\u5e02\u4e2d\u592e\u533a", "\u6a2a\u6d5c\u5e02\u897f\u533a"), 1
    )
    industry <- sample(
      c("\u60c5\u5831\u901a\u4fe1", "\u88fd\u9020", "\u5c0f\u58f2",
        "\u91d1\u878d", "\u4e0d\u52d5\u7523", "\u5316\u5b66"), 1
    )
    suffix <- sample(
      c("\u30c6\u30af\u30ce\u30ed\u30b8\u30fc", "\u30de\u30c6\u30ea\u30a2\u30eb\u30ba",
        "\u30d5\u30fc\u30ba", "\u30a8\u30ca\u30b8\u30fc", "\u30b5\u30fc\u30d3\u30b9"), 1
    )
    emp <- sample(100:5000, 1)
    yr <- sample(1950:2010, 1)

    base <- paste0(
      "\u7b2c\u4e00\u90e8 \u4f01\u696d\u60c5\u5831\n\n",
      "\u4f1a\u793e\u540d: ", city, sample(c("\u6771", "\u5357", "\u5317", "\u897f"), 1),
      suffix, "\u682a\u5f0f\u4f1a\u793e\n",
      "\u8a2d\u7acb: ", yr, "\u5e74\n",
      "\u5f93\u696d\u54e1\u6570: ", format(emp, big.mark = ","),
      "\u540d\uff08\u9023\u7d50\uff09\n\n",
      "\u5f53\u793e\u30b0\u30eb\u30fc\u30d7\u306f", industry,
      "\u4e8b\u696d\u3092\u4e2d\u5fc3\u306b\u3001",
      sample(c("\u56fd\u5185\u5916", "\u30a2\u30b8\u30a2\u592a\u5e73\u6d0b\u5730\u57df",
               "\u30b0\u30ed\u30fc\u30d0\u30eb"), 1),
      "\u3067\u4e8b\u696d\u5c55\u958b\u3057\u3066\u304a\u308a\u307e\u3059\u3002",
      "\u4e3b\u8981\u306a\u4e8b\u696d\u30bb\u30b0\u30e1\u30f3\u30c8\u3068\u3057\u3066\u3001",
      sample(c("\u30b7\u30b9\u30c6\u30e0\u30a4\u30f3\u30c6\u30b0\u30ec\u30fc\u30b7\u30e7\u30f3",
               "\u96fb\u5b50\u90e8\u54c1\u88fd\u9020", "\u98df\u54c1\u52a0\u5de5",
               "\u8cc7\u7523\u904b\u7528"), 1),
      "\u4e8b\u696d\u304a\u3088\u3073",
      sample(c("\u30b3\u30f3\u30b5\u30eb\u30c6\u30a3\u30f3\u30b0",
               "\u7269\u6d41\u30b5\u30fc\u30d3\u30b9", "\u7814\u7a76\u958b\u767a"), 1),
      "\u4e8b\u696d\u3092\u5c55\u958b\u3057\u3066\u304a\u308a\u307e\u3059\u3002"
    )
    if (tier == "severe") base <- substr(base, 1, 30)  # stub flaw
    base
  }

  gen_business_status <- function(tier) {
    plan <- sample(c("Vision 2030", "Next Stage", "Growth 2028",
                      "Transform 2027", "Accelerate 2029"), 1)
    target <- sample(50:500, 1)
    paste0(
      "\u7d4c\u55b6\u65b9\u91dd\u3068\u3057\u3066\u3001\u5f53\u793e\u30b0\u30eb\u30fc\u30d7\u306f\u4e2d\u671f\u7d4c\u55b6\u8a08\u753b\u300c",
      plan, "\u300d\u306b\u57fa\u3065\u304d\u4e8b\u696d\u3092\u63a8\u9032\u3057\u3066\u304a\u308a\u307e\u3059\u3002\n\n",
      "\u5bfe\u51e6\u3059\u3079\u304d\u8ab2\u984c\uff1a\n",
      "1. \u30c7\u30b8\u30bf\u30eb\u30c8\u30e9\u30f3\u30b9\u30d5\u30a9\u30fc\u30e1\u30fc\u30b7\u30e7\u30f3\u306e\u63a8\u9032\n",
      "2. \u30b5\u30b9\u30c6\u30ca\u30d3\u30ea\u30c6\u30a3\u7d4c\u55b6\u306e\u5f37\u5316\n",
      "3. \u30b0\u30ed\u30fc\u30d0\u30eb\u5c55\u958b\u306e\u52a0\u901f\n",
      if (tier == "perfect") "4. \u4eba\u6750\u78ba\u4fdd\u30fb\u80b2\u6210\u306e\u5f37\u5316\n" else "",
      "\nKPI: \u58f2\u4e0a\u9ad8", target, "\u5104\u5186\uff08\u76ee\u6a19\uff09\n",
      "\u55b6\u696d\u5229\u76ca\u7387", sample(5:15, 1), "%\u4ee5\u4e0a\u3092\u76ee\u6307\u3057\u3066\u307e\u3044\u308a\u307e\u3059\u3002"
    )
  }

  gen_business_risks <- function(tier) {
    if (tier == "severe") return("")  # empty section = severe structural flaw
    if (tier == "moderate") {
      # VAGUE_RISK_FACTOR: hedging language, no specifics
      return(paste0(
        "\u4e8b\u696d\u7b49\u306e\u30ea\u30b9\u30af\n\n",
        "\u5f53\u793e\u30b0\u30eb\u30fc\u30d7\u306e\u4e8b\u696d\u305d\u306e\u4ed6\u306b\u95a2\u3059\u308b\u30ea\u30b9\u30af\u306b\u3064\u3044\u3066\u3001",
        "\u6295\u8cc7\u5224\u65ad\u306b\u91cd\u8981\u306a\u5f71\u97ff\u3092\u53ca\u307c\u3059\u53ef\u80fd\u6027\u306e\u3042\u308b\u4e8b\u9805\u3092\u4ee5\u4e0b\u306b\u8a18\u8f09\u3057\u3066\u304a\u308a\u307e\u3059\u3002\n\n",
        "\u69d8\u3005\u306a\u30ea\u30b9\u30af\u304c\u3042\u308a\u307e\u3059\u3002",
        "\u4e0d\u900f\u660e\u306a\u8981\u56e0\u304c\u5b58\u5728\u3057\u307e\u3059\u3002",
        "\u4e00\u822c\u7684\u306a\u7d4c\u55b6\u74b0\u5883\u306e\u60aa\u5316\u306b\u3088\u308a\u3001",
        "\u5f53\u793e\u306e\u696d\u7e3e\u306b\u60aa\u5f71\u97ff\u3092\u53ca\u307c\u3059\u53ef\u80fd\u6027\u304c\u3042\u308a\u307e\u3059\u3002",
        "\u305d\u306e\u4ed6\u306e\u8981\u56e0\u306b\u3088\u3063\u3066\u3082\u3001",
        "\u60aa\u5f71\u97ff\u3092\u53ca\u307c\u3059\u53ef\u80fd\u6027\u304c\u3042\u308a\u307e\u3059\u3002"
      ))
    }
    # Tier 1 & 2: specific, well-formed risk disclosures
    risk1 <- sample(c("\u666f\u6c17\u52d5\u5411", "\u70ba\u66ff\u5909\u52d5",
                       "\u539f\u6750\u6599\u4fa1\u683c"), 1)
    region <- sample(c("\u5317\u7c73", "\u30a2\u30b8\u30a2\u592a\u5e73\u6d0b",
                        "\u6b27\u5dde", "\u4e2d\u56fd"), 1)
    impact <- sample(c("120%", "15\u5104\u5186", "8.5%"), 1)
    law <- sample(c("\u500b\u4eba\u60c5\u5831\u4fdd\u8b77\u6cd5",
                     "\u91d1\u878d\u5546\u54c1\u53d6\u5f15\u6cd5",
                     "\u72ec\u5360\u7981\u6b62\u6cd5"), 1)
    paste0(
      "\u4e8b\u696d\u7b49\u306e\u30ea\u30b9\u30af\n\n",
      "\u5f53\u793e\u30b0\u30eb\u30fc\u30d7\u306e\u4e8b\u696d\u305d\u306e\u4ed6\u306b\u95a2\u3059\u308b\u30ea\u30b9\u30af\u306b\u3064\u3044\u3066\u3001",
      "\u6295\u8cc7\u5224\u65ad\u306b\u91cd\u8981\u306a\u5f71\u97ff\u3092\u53ca\u307c\u3059\u53ef\u80fd\u6027\u306e\u3042\u308b\u4e8b\u9805\u3092\u4ee5\u4e0b\u306b\u8a18\u8f09\u3057\u3066\u304a\u308a\u307e\u3059\u3002\n\n",
      "1. \u5e02\u5834\u74b0\u5883\u306e\u5909\u52d5\u30ea\u30b9\u30af\n",
      "\u5f53\u793e\u306e\u4e8b\u696d\u306f", risk1,
      "\u306e\u5f71\u97ff\u3092\u53d7\u3051\u307e\u3059\u3002",
      "\u524d\u5e74\u5ea6\u6bd4", impact, "\u306e\u5f71\u97ff\u304c\u3042\u308a\u307e\u3059\u3002\n\n",
      "2. ", region, "\u5e02\u5834\u306b\u304a\u3051\u308b\u7af6\u4e89\u30ea\u30b9\u30af\n",
      region, "\u5e02\u5834\u306b\u304a\u3051\u308b\u7af6\u4e89\u6fc0\u5316\u306e\u30ea\u30b9\u30af\u304c\u3042\u308a\u307e\u3059\u3002\n\n",
      "3. \u6cd5\u898f\u5236\u306e\u5909\u66f4\u30ea\u30b9\u30af\n",
      law, "\u7b49\u306e\u6539\u6b63\u306b\u3088\u308a\u8ffd\u52a0\u5bfe\u5fdc\u304c\u5fc5\u8981\u3068\u306a\u308b\u53ef\u80fd\u6027\u304c\u3042\u308a\u307e\u3059\u3002"
    )
  }

  gen_mda <- function(tier) {
    revenue <- sample(100:900, 1)
    op_margin <- runif(1, 0.05, 0.15)
    net_margin <- runif(1, 0.02, 0.10)
    paste0(
      "\u7d4c\u55b6\u8005\u306b\u3088\u308b\u8ca1\u653f\u72b6\u614b\u3001\u7d4c\u55b6\u6210\u7e3e\u53ca\u3073\u30ad\u30e3\u30c3\u30b7\u30e5\u30fb\u30d5\u30ed\u30fc\u306e\u72b6\u6cc1\u306e\u5206\u6790\n\n",
      "\u5f53\u9023\u7d50\u4f1a\u8a08\u5e74\u5ea6\u306e\u58f2\u4e0a\u9ad8\u306f", revenue,
      "\u5104\u5186\uff08\u524d\u671f\u6bd4",
      sample(c("+", "-"), 1), sample(1:15, 1), ".",
      sample(0:9, 1), "%\uff09\u3068\u306a\u308a\u307e\u3057\u305f\u3002\n\n",
      "\u55b6\u696d\u5229\u76ca\u306f", round(revenue * op_margin), "\u5104\u5186\u3001",
      "\u7d4c\u5e38\u5229\u76ca\u306f", round(revenue * (op_margin - 0.01)), "\u5104\u5186\u3001",
      "\u89aa\u4f1a\u793e\u682a\u4e3b\u306b\u5e30\u5c5e\u3059\u308b\u5f53\u671f\u7d14\u5229\u76ca\u306f",
      round(revenue * net_margin), "\u5104\u5186\u3068\u306a\u308a\u307e\u3057\u305f\u3002\n\n",
      "\u30bb\u30b0\u30e1\u30f3\u30c8\u5225\u306e\u6982\u6cc1\uff1a\n",
      "\u56fd\u5185\u4e8b\u696d: \u58f2\u4e0a\u9ad8", round(revenue * 0.6),
      "\u5104\u5186\uff08\u524d\u671f\u6bd4+", sample(1:10, 1), ".", sample(0:9, 1), "%\uff09\n",
      "\u6d77\u5916\u4e8b\u696d: \u58f2\u4e0a\u9ad8", round(revenue * 0.4),
      "\u5104\u5186\uff08\u524d\u671f\u6bd4", sample(c("+", "-"), 1),
      sample(1:12, 1), ".", sample(0:9, 1), "%\uff09"
    )
  }

  gen_sustainability <- function(tier) {
    if (tier %in% c("near", "moderate")) {
      # MISSING_HUMAN_CAPITAL_METRICS for flaw tiers
      return(paste0(
        "\u30b5\u30b9\u30c6\u30ca\u30d3\u30ea\u30c6\u30a3\u306b\u95a2\u3059\u308b\u8003\u3048\u65b9\u53ca\u3073\u53d6\u7d44\n\n",
        "\u5f53\u793e\u30b0\u30eb\u30fc\u30d7\u306f\u3001\u30b5\u30b9\u30c6\u30ca\u30d3\u30ea\u30c6\u30a3\u3092\u91cd\u8981\u306a\u7d4c\u55b6\u8ab2\u984c\u3068\u4f4d\u7f6e\u3065\u3051\u3066\u304a\u308a\u307e\u3059\u3002",
        "\u74b0\u5883\u8ca0\u8377\u306e\u4f4e\u6e1b\u306b\u5411\u3051\u305f\u53d6\u308a\u7d44\u307f\u3092\u63a8\u9032\u3057\u3066\u304a\u308a\u307e\u3059\u3002",
        "\u4eba\u7684\u8cc7\u672c\u306b\u95a2\u3059\u308b\u65b9\u91dd\u3092\u7b56\u5b9a\u3057\u3066\u304a\u308a\u307e\u3059\u3002",
        "\u591a\u69d8\u6027\u306e\u63a8\u9032\u306b\u52aa\u3081\u3066\u304a\u308a\u307e\u3059\u3002"
      ))
    }
    # Tier 1: compliant with mandatory metrics
    paste0(
      "\u30b5\u30b9\u30c6\u30ca\u30d3\u30ea\u30c6\u30a3\u306b\u95a2\u3059\u308b\u8003\u3048\u65b9\u53ca\u3073\u53d6\u7d44\n\n",
      "\u5f53\u793e\u30b0\u30eb\u30fc\u30d7\u306f\u3001\u30b5\u30b9\u30c6\u30ca\u30d3\u30ea\u30c6\u30a3\u3092\u91cd\u8981\u306a\u7d4c\u55b6\u8ab2\u984c\u3068\u4f4d\u7f6e\u3065\u3051\u3066\u304a\u308a\u307e\u3059\u3002\n\n",
      "\u4eba\u7684\u8cc7\u672c\u306b\u95a2\u3059\u308b\u6307\u6a19\uff1a\n",
      "\u7ba1\u7406\u8077\u306b\u5360\u3081\u308b\u5973\u6027\u306e\u5272\u5408: ", sample(15:35, 1), ".",
      sample(0:9, 1), "%\n",
      "\u7537\u5973\u306e\u8cc3\u91d1\u306e\u5dee\u7570: ", sample(10:25, 1), ".",
      sample(0:9, 1), "%\n",
      "\u80b2\u5150\u4f11\u696d\u53d6\u5f97\u7387: ", sample(50:95, 1), ".",
      sample(0:9, 1), "%\n\n",
      "\u74b0\u5883\u306b\u95a2\u3059\u308b\u6307\u6a19\uff1a\n",
      "CO2\u6392\u51fa\u91cf: ", sample(10000:50000, 1), "t-CO2\uff08Scope 1+2\uff09\n",
      "\u518d\u751f\u53ef\u80fd\u30a8\u30cd\u30eb\u30ae\u30fc\u6bd4\u7387: ", sample(10:40, 1), "%"
    )
  }

  gen_governance <- function(tier) {
    n_dir <- sample(6:12, 1)
    n_outside <- sample(2:4, 1)
    n_aud <- sample(3:5, 1)
    n_aud_out <- sample(2:3, 1)
    paste0(
      "\u30b3\u30fc\u30dd\u30ec\u30fc\u30c8\u30fb\u30ac\u30d0\u30ca\u30f3\u30b9\u306e\u72b6\u6cc1\u7b49\n\n",
      "\u5f53\u793e\u306f\u76e3\u67fb\u5f79\u4f1a\u8a2d\u7f6e\u4f1a\u793e\u3067\u3042\u308a\u3001\u53d6\u7de0\u5f79",
      n_dir, "\u540d\uff08\u3046\u3061\u793e\u5916\u53d6\u7de0\u5f79",
      n_outside, "\u540d\uff09\u3001\u76e3\u67fb\u5f79", n_aud,
      "\u540d\uff08\u3046\u3061\u793e\u5916\u76e3\u67fb\u5f79", n_aud_out,
      "\u540d\uff09\u3067\u69cb\u6210\u3055\u308c\u3066\u304a\u308a\u307e\u3059\u3002\n\n",
      "\u53d6\u7de0\u5f79\u4f1a\u306f\u539f\u5247\u6bce\u6708\u958b\u50ac\u3057\u3001\u91cd\u8981\u306a\u610f\u601d\u6c7a\u5b9a\u3092\u884c\u3063\u3066\u304a\u308a\u307e\u3059\u3002",
      "\u5185\u90e8\u76e3\u67fb\u90e8\u9580\u306f", sample(3:8, 1),
      "\u540d\u3067\u69cb\u6210\u3055\u308c\u3001\u5b9a\u671f\u7684\u306b\u76e3\u67fb\u3092\u5b9f\u65bd\u3057\u3066\u304a\u308a\u307e\u3059\u3002"
    )
  }

  gen_financial <- function(tier) {
    paste0(
      "\u7d4c\u7406\u306e\u72b6\u6cc1\n\n",
      "1. \u9023\u7d50\u8ca1\u52d9\u8af8\u8868\u306e\u4f5c\u6210\u65b9\u6cd5\n",
      "\u5f53\u793e\u306e\u9023\u7d50\u8ca1\u52d9\u8af8\u8868\u306f\u3001",
      sample(c("\u65e5\u672c\u57fa\u6e96\uff08J-GAAP\uff09",
               "\u56fd\u969b\u8ca1\u52d9\u5831\u544a\u57fa\u6e96\uff08IFRS\uff09"), 1),
      "\u306b\u6e96\u62e0\u3057\u3066\u4f5c\u6210\u3057\u3066\u304a\u308a\u307e\u3059\u3002\n\n",
      "2. \u4e3b\u8981\u306a\u4f1a\u8a08\u65b9\u91dd\n",
      "\u53ce\u76ca\u8a8d\u8b58: \u5c65\u884c\u7fa9\u52d9\u306e\u5145\u8db3\u6642\u70b9\u3067\u8a8d\u8b58\n",
      "\u6e1b\u4fa1\u511f\u5374: \u6709\u5f62\u56fa\u5b9a\u8cc7\u7523\u306f\u5b9a\u984d\u6cd5\n",
      "\u306e\u308c\u3093: ", sample(c("5\u5e74", "10\u5e74", "20\u5e74"), 1),
      "\u3067\u5747\u7b49\u511f\u5374"
    )
  }

  gen_going_concern <- function(tier, is_distressed) {
    if (!is_distressed) return("")
    if (tier == "severe") {
      # SOFTENED_GOING_CONCERN: present but missing statutory phrase
      return(paste0(
        "\u7d99\u7d9a\u4f01\u696d\u306e\u524d\u63d0\u306b\u95a2\u3059\u308b\u6ce8\u8a18\n\n",
        "\u5f53\u793e\u306f\u3001\u4e00\u5b9a\u306e\u8ca1\u52d9\u7684\u8ab2\u984c\u3092\u6709\u3057\u3066\u304a\u308a\u307e\u3059\u304c\u3001",
        "\u7d4c\u55b6\u9663\u306f\u7d4c\u55b6\u6539\u5584\u8a08\u753b\u3092\u63a8\u9032\u3057\u3066\u304a\u308a\u307e\u3059\u3002",
        "\u4eca\u5f8c\u306e\u4e8b\u696d\u5c55\u958b\u306b\u3088\u308a\u3001\u72b6\u6cc1\u306e\u6539\u5584\u304c\u898b\u8fbc\u307e\u308c\u307e\u3059\u3002"
      ))
    }
    # Proper going concern with statutory phrase
    paste0(
      "\u7d99\u7d9a\u4f01\u696d\u306e\u524d\u63d0\u306b\u95a2\u3059\u308b\u6ce8\u8a18\n\n",
      "\u5f53\u793e\u306f\u3001\u7d99\u7d9a\u7684\u306a\u55b6\u696d\u640d\u5931\u306e\u8a08\u4e0a\u304a\u3088\u3073\u50b5\u52d9\u8d85\u904e\u306e\u72b6\u6cc1\u306b\u3042\u308a\u3001",
      "\u7d99\u7d9a\u4f01\u696d\u306e\u524d\u63d0\u306b\u91cd\u8981\u306a\u4e0d\u78ba\u5b9f\u6027\u304c\u8a8d\u3081\u3089\u308c\u307e\u3059\u3002",
      "\u7d4c\u55b6\u9663\u306f\u4ee5\u4e0b\u306e\u65bd\u7b56\u3092\u5b9f\u65bd\u4e2d\u3067\u3042\u308a\u307e\u3059\uff1a\n",
      "1. \u4e0d\u63a1\u7b97\u4e8b\u696d\u306e\u7e2e\u5c0f\u30fb\u64a4\u9000\n",
      "2. \u56fa\u5b9a\u8cbb\u524a\u6e1b\uff08\u5e74\u9593", sample(5:20, 1), "\u5104\u5186\u898f\u6a21\uff09\n",
      "3. \u65b0\u898f\u878d\u8cc7\u306e\u78ba\u4fdd"
    )
  }

  # ── Generate documents ──────────────────────────────────────────

  docs <- vector("list", n)

  for (i in seq_len(n)) {
    tier_idx <- sample(seq_along(tiers), 1, prob = tier_probs)
    tier <- tiers[tier_idx]
    is_distressed <- sample(c(TRUE, FALSE), 1, prob = c(0.15, 0.85))

    doc <- list(
      document_id = sprintf("SAMPLE-%06d", i),
      quality_tier = tier,
      error_rate = error_rates[tier_idx],
      seg_company_overview = gen_company_overview(tier),
      seg_business_status = gen_business_status(tier),
      seg_business_risks = gen_business_risks(tier),
      seg_md_and_a = gen_mda(tier),
      seg_sustainability = gen_sustainability(tier),
      seg_corporate_governance = gen_governance(tier),
      seg_financial_highlights = gen_financial(tier),
      seg_going_concern = gen_going_concern(tier, is_distressed)
    )

    doc$document_content <- paste(
      unlist(doc[grep("^seg_", names(doc))]),
      collapse = "\n\n---\n\n"
    )
    docs[[i]] <- doc
  }

  # ── Output ──────────────────────────────────────────────────────

  if (!is.null(output_path)) {
    lines <- vapply(
      docs,
      function(d) jsonlite::toJSON(d, auto_unbox = TRUE),
      character(1)
    )
    writeLines(lines, output_path)
    message("Generated ", n, " sample documents at: ", output_path)
    return(invisible(output_path))
  }

  # Return as tibble (same as load_securities_report output)
  # Write to temp, read back — ensures consistent structure
  tmp <- tempfile(fileext = ".jsonl")
  lines <- vapply(
    docs,
    function(d) jsonlite::toJSON(d, auto_unbox = TRUE),
    character(1)
  )
  writeLines(lines, tmp)
  result <- load_securities_report(tmp)
  unlink(tmp)
  result
}
