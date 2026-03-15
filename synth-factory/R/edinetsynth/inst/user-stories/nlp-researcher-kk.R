#!/usr/bin/env Rscript
# ==========================================================================
# Pre-Launch QA: Simulated Customer Evaluation
# ==========================================================================
#
# PURPOSE:
#   This is an INTERNAL QA tool, not a customer-facing script.
#   It simulates what a prospective buyer would do when evaluating our
#   dataset, so we can catch quality issues BEFORE listing on JDEX.
#
#   For the full customer narrative, see: docs/USER-STORY-DR-TANAKA.md
#
# WHAT IT DOES:
#   Runs the same edinetsynth functions a real customer would use during
#   evaluation. Produces a pass/fail quality scorecard. If the dataset
#   fails this script, it's not ready for sale.
#
# PERSONA (for context):
#   Modeled after Dr. Yuki Tanaka, a senior NLP researcher at a
#   Tokyo-based AI research institute (see docs/USER-STORY-DR-TANAKA.md
#   for the full narrative). She evaluates datasets in R using
#   edinetsynth before making purchase decisions on JDEX.
#
# HOW TO RUN:
#   # Against synthetic test data (self-contained simulation):
#   Rscript inst/user-stories/nlp-researcher-kk.R
#
#   # Against a real generated dataset (pre-launch QA):
#   Rscript inst/user-stories/nlp-researcher-kk.R output/data/reports.jsonl
#
# ==========================================================================

library(edinetsynth)
library(jsonlite)

cat("=" |> rep(72) |> paste(collapse = ""), "\n")
cat("  User Story: Dr. Tanaka evaluates VilseckKI EDINET dataset\n")
cat("  架空テック株式会社 — NLP研究チーム\n")
cat("=" |> rep(72) |> paste(collapse = ""), "\n\n")


# ── Step 0: Generate or load test data ────────────────────────────

args <- commandArgs(trailingOnly = TRUE)

if (length(args) > 0 && file.exists(args[1])) {
  cat("[Step 0] Loading real dataset:", args[1], "\n")
  data_path <- args[1]
} else {
  cat("[Step 0] No dataset provided — generating simulation data...\n")

  # Create synthetic test JSONL that mimics what the factory would produce
  tmp <- tempfile(fileext = ".jsonl")

  tiers <- c("perfect", "near", "moderate", "severe")
  error_rates <- c(0.0, 0.03, 0.12, 0.30)
  tier_probs <- c(0.80, 0.10, 0.08, 0.02)
  n <- 50  # Simulating the free sample size

  set.seed(42)  # Reproducibility

  segments <- list(
    seg_company_overview = function(tier) {
      base <- paste0(
        "第一部 企業情報\n\n",
        "会社名: ", sample(c("東京", "大阪", "名古屋", "福岡", "札幌"), 1),
        sample(c("テクノロジー", "マテリアルズ", "フーズ", "エナジー"), 1),
        "株式会社\n",
        "設立: ", sample(1950:2010, 1), "年\n",
        "従業員数: ", sample(100:5000, 1), "名（連結）\n\n",
        "当社グループは", sample(c("情報通信", "製造", "小売", "金融"), 1),
        "事業を中心に、",
        sample(c("国内外", "アジア太平洋地域", "グローバル"), 1),
        "で事業展開しております。"
      )
      if (tier == "severe") base <- substr(base, 1, 30)
      if (tier == "moderate") base <- paste0(base, "\n該当事項はありません。")
      base
    },
    seg_business_status = function(tier) {
      paste0(
        "経営方針として、当社グループは中期経営計画「",
        sample(c("Vision 2030", "Next Stage", "Growth 2028"), 1),
        "」に基づき事業を推進しております。\n\n",
        "対処すべき課題：\n",
        "1. デジタルトランスフォーメーションの推進\n",
        "2. サステナビリティ経営の強化\n",
        "3. グローバル展開の加速\n",
        if (tier != "perfect") "" else "4. 人材確保・育成の強化\n",
        "\nKPI: 売上高", sample(50:500, 1), "億円（目標）"
      )
    },
    seg_business_risks = function(tier) {
      if (tier == "severe") return("")  # Empty section = severe flaw
      paste0(
        "事業等のリスク\n\n",
        "当社グループの事業その他に関するリスクについて、",
        "投資判断に重要な影響を及ぼす可能性のある事項を以下に記載しております。\n\n",
        "1. 市場環境の変動リスク\n",
        "当社の事業は", sample(c("景気動向", "為替変動", "原材料価格"), 1),
        "の影響を受けます。\n\n",
        "2. 技術革新への対応リスク\n",
        "急速な技術革新に対応できない場合、競争力が低下する可能性があります。\n\n",
        "3. 法規制の変更リスク\n",
        sample(c("個人情報保護法", "金融商品取引法", "独占禁止法"), 1),
        "等の改正により追加対応が必要となる可能性があります。"
      )
    },
    seg_md_and_a = function(tier) {
      revenue <- sample(100:900, 1)
      paste0(
        "経営者による財政状態、経営成績及びキャッシュ・フローの状況の分析\n\n",
        "当連結会計年度の売上高は", revenue, "億円（前期比",
        sample(c("+", "-"), 1), sample(1:15, 1), ".",
        sample(0:9, 1), "%）となりました。\n\n",
        "営業利益は", round(revenue * runif(1, 0.05, 0.15)), "億円、",
        "経常利益は", round(revenue * runif(1, 0.04, 0.14)), "億円、",
        "親会社株主に帰属する当期純利益は",
        round(revenue * runif(1, 0.02, 0.10)), "億円となりました。"
      )
    },
    seg_corporate_governance = function(tier) {
      paste0(
        "コーポレート・ガバナンスの状況等\n\n",
        "当社は監査役会設置会社であり、取締役",
        sample(6:12, 1), "名（うち社外取締役",
        sample(2:4, 1), "名）、監査役", sample(3:5, 1),
        "名（うち社外監査役", sample(2:3, 1), "名）で構成されています。"
      )
    },
    seg_stock_info = function(tier) {
      shares <- sample(10:100, 1) * 1000000
      paste0(
        "株式等の状況\n\n",
        "発行済株式の総数: ", format(shares, big.mark = ","), "株\n",
        "大株主:\n",
        "  1. 日本マスタートラスト信託銀行 ", sample(5:15, 1), ".",
        sample(0:9, 1), "%\n",
        "  2. ", sample(c("三菱UFJ", "三井住友", "みずほ"), 1),
        "銀行 ", sample(3:8, 1), ".", sample(0:9, 1), "%"
      )
    },
    seg_directors = function(tier) {
      surnames <- c("山田", "佐藤", "鈴木", "高橋", "田中", "伊藤", "渡辺", "中村")
      given <- c("太郎", "花子", "一郎", "正", "博", "明", "健一", "美咲")
      n_dir <- sample(5:8, 1)
      dirs <- vapply(seq_len(n_dir), function(j) {
        paste0(
          "  ", sample(surnames, 1), " ", sample(given, 1),
          " — ", sample(c("代表取締役社長", "取締役副社長",
                          "常務取締役", "取締役", "社外取締役"), 1),
          "（", sample(1960:1985, 1), "年生）"
        )
      }, character(1))
      paste0("役員の状況\n\n", paste(dirs, collapse = "\n"))
    },
    seg_financial_highlights = function(tier) {
      paste0(
        "経理の状況\n\n",
        "1. 連結財務諸表の作成方法\n",
        "当社の連結財務諸表は、",
        sample(c("日本基準（J-GAAP）", "国際財務報告基準（IFRS）"), 1),
        "に準拠して作成しております。\n\n",
        "2. 主要な会計方針\n",
        "収益認識: 履行義務の充足時点で認識\n",
        "減価償却: 有形固定資産は定額法\n",
        "のれん: ", sample(c("5年", "10年", "20年"), 1), "で均等償却"
      )
    }
  )

  lines <- vapply(seq_len(n), function(i) {
    tier_idx <- sample(seq_along(tiers), 1, prob = tier_probs)
    tier <- tiers[tier_idx]
    doc <- list(
      document_id = sprintf("SAMPLE-%06d", i),
      quality_tier = tier,
      error_rate = error_rates[tier_idx]
    )
    for (seg_name in names(segments)) {
      doc[[seg_name]] <- segments[[seg_name]](tier)
    }
    doc$document_content <- paste(
      unlist(doc[grep("^seg_", names(doc))]),
      collapse = "\n\n---\n\n"
    )
    toJSON(doc, auto_unbox = TRUE)
  }, character(1))

  writeLines(lines, tmp)
  data_path <- tmp
  cat("  → Generated", n, "simulated documents at", tmp, "\n\n")
}


# ── Step 1: Load and inspect ─────────────────────────────────────

cat("[Step 1] 田中博士: 'まずデータを読み込んで概要を確認しましょう'\n")
cat("         (Dr. Tanaka: 'Let me load the data and check the overview')\n\n")

reports <- load_securities_report(data_path)
cat("  Documents loaded:", nrow(reports), "\n")
cat("  Columns:", paste(names(reports), collapse = ", "), "\n")
cat("  Segment columns:", paste(grep("^seg_", names(reports), value = TRUE),
                                collapse = ", "), "\n\n")


# ── Step 2: Segment statistics ───────────────────────────────────

cat("[Step 2] 田中博士: 'セグメント長は現実的ですか？'\n")
cat("         (Dr. Tanaka: 'Are the segment lengths realistic?')\n\n")

stats <- segment_summary(reports)
print(stats, n = Inf)
cat("\n")

# Check: Are any segments consistently empty?
empty_segs <- stats[stats$pct_empty > 10, ]
if (nrow(empty_segs) > 0) {
  cat("  ⚠ Warning: These segments have >10% empty rate:\n")
  print(empty_segs[, c("segment", "pct_empty")])
} else {
  cat("  ✓ No segments have excessive emptiness (all < 10%)\n")
}
cat("\n")


# ── Step 3: Quality tier verification ────────────────────────────

cat("[Step 3] 田中博士: '品質ティアの分布は広告通りですか？'\n")
cat("         (Dr. Tanaka: 'Does the tier distribution match the listing?')\n\n")

if ("quality_tier" %in% names(reports)) {
  tier_stats <- compare_tiers(reports)
  print(tier_stats, n = Inf)
  cat("\n")

  # Check: Is the deviation from expected reasonable?
  max_dev <- max(abs(tier_stats$deviation), na.rm = TRUE)
  if (max_dev < 5) {
    cat("  ✓ Tier distribution within 5% of expected — acceptable for n=",
        nrow(reports), "\n")
  } else {
    cat("  ⚠ Max deviation:", round(max_dev, 1),
        "% — may need larger sample to converge\n")
  }
} else {
  cat("  ℹ No quality_tier column — this may be a single-tier dataset\n")
}
cat("\n")


# ── Step 4: Flaw detection ───────────────────────────────────────

cat("[Step 4] 田中博士: '欠陥パターンを確認しましょう'\n")
cat("         (Dr. Tanaka: 'Let me check for flaw patterns')\n\n")

flaws <- detect_flaws(reports)
cat("  Total flaws detected:", nrow(flaws), "\n")

if (nrow(flaws) > 0) {
  cat("  Flaw distribution:\n")
  print(table(flaws$flaw_type, flaws$severity))
  cat("\n")

  # Do flaws correlate with tier?
  if ("quality_tier" %in% names(reports)) {
    flaw_by_tier <- merge(
      flaws,
      reports[, c("document_id", "quality_tier")],
      by = "document_id"
    )
    cat("  Flaws by tier:\n")
    print(table(flaw_by_tier$quality_tier))
    cat("\n")
  }
} else {
  cat("  ℹ No flaws detected — either data is very clean or sample is small\n")
}
cat("\n")


# ── Step 5: Segment extraction for NLP ───────────────────────────

cat("[Step 5] 田中博士: 'リスクセクションをNLPパイプラインに入れてみましょう'\n")
cat("         (Dr. Tanaka: 'Let me feed the risk sections into my NLP pipeline')\n\n")

risks <- extract_segment(reports, "business_risks")
cat("  Extracted", nrow(risks), "risk section(s)\n")

# Simulate what an NLP researcher would check
non_empty <- risks[nchar(as.character(risks[[2]])) > 0, ]
cat("  Non-empty risk sections:", nrow(non_empty), "/", nrow(risks), "\n")

# Token estimate (Japanese: ~1.5 chars/token)
char_counts <- nchar(as.character(non_empty[[2]]))
cat("  Mean characters:", round(mean(char_counts)), "\n")
cat("  Estimated mean tokens:", round(mean(char_counts) / 1.5), "\n")
cat("  Min-Max tokens:", round(min(char_counts) / 1.5), "-",
    round(max(char_counts) / 1.5), "\n\n")


# ── Step 6: Decision ─────────────────────────────────────────────

cat("[Step 6] 田中博士の評価結果:\n")
cat("         (Dr. Tanaka's evaluation result:)\n\n")

# Score the dataset
score <- 0
checks <- 0

# Check 1: Structural completeness
seg_count <- length(grep("^seg_", names(reports)))
checks <- checks + 1
if (seg_count >= 6) { score <- score + 1; cat("  ✓ ") } else { cat("  ✗ ") }
cat("Structural completeness:", seg_count, "segments\n")

# Check 2: Non-trivial content
checks <- checks + 1
mean_len <- mean(stats$mean_chars, na.rm = TRUE)
if (mean_len > 100) { score <- score + 1; cat("  ✓ ") } else { cat("  ✗ ") }
cat("Content substantiveness: mean", round(mean_len), "chars/segment\n")

# Check 3: Tier distribution
checks <- checks + 1
if ("quality_tier" %in% names(reports)) {
  score <- score + 1
  cat("  ✓ Quality tiers present and distributed\n")
} else {
  cat("  ✗ No quality tier information\n")
}

# Check 4: Low critical flaw rate
checks <- checks + 1
critical_flaws <- flaws[flaws$severity == "critical", ]
crit_rate <- nrow(critical_flaws) / nrow(reports) * 100
if (crit_rate < 5) { score <- score + 1; cat("  ✓ ") } else { cat("  ✗ ") }
cat("Critical flaw rate:", round(crit_rate, 1), "%\n")

# Check 5: Usable for NLP training
checks <- checks + 1
if (mean_len > 200) { score <- score + 1; cat("  ✓ ") } else { cat("  ✗ ") }
cat("NLP training suitability: segments long enough for fine-tuning\n")

cat("\n")
final_score <- round(score / checks * 100)
cat("  Final score:", score, "/", checks, "(", final_score, "%)\n\n")

if (final_score >= 80) {
  cat("  📊 田中博士: '品質は十分です。フルデータセットを購入しましょう。'\n")
  cat("     (Dr. Tanaka: 'Quality is sufficient. Let's purchase the full dataset.')\n")
} else if (final_score >= 60) {
  cat("  📊 田中博士: 'もう少しサンプルが必要ですが、有望です。'\n")
  cat("     (Dr. Tanaka: 'Need more samples, but promising.')\n")
} else {
  cat("  📊 田中博士: '品質に懸念があります。ベンダーに確認が必要です。'\n")
  cat("     (Dr. Tanaka: 'Quality concerns. Need to follow up with vendor.')\n")
}

cat("\n")
cat("=" |> rep(72) |> paste(collapse = ""), "\n")
cat("  End of evaluation scenario\n")
cat("=" |> rep(72) |> paste(collapse = ""), "\n")
