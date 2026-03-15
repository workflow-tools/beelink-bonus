# Wise Business Banking — Analysis for Japanese B2B Data Sales

> **Date:** March 2026
> **Account holder:** ML Upskill Agents UG (Germany)
> **Question:** Can Wise Business replace a Japanese domestic bank account
> for receiving JDEX data sales revenue?

---

## Bank Details on File

### JPY Receiving (for Japanese buyers)
- **IBAN:** GB27 TRWI 2308 0124 2779 08
- **SWIFT/BIC:** TRWIGB2LXXX
- **Bank:** Wise Payments Limited
- **Address:** 1st Floor, Worship Square, 65 Clifton Street, London, EC2A 4JE, UK

### EUR Receiving (for German/EU transactions, UG→GK royalties)
- **IBAN:** BE79 9055 9177 0533
- **SWIFT/BIC:** TRWIBEB1XXX
- **Bank:** Wise, Rue du Trône 100, 3rd Floor, Brussels, 1050, Belgium

---

## The Good News

### Zengin System Access
Wise Payments Japan K.K. now has direct access to the Zengin System
(全銀システム / ぜんぎんシステム — Japan's domestic payment clearing network).
This means Japanese companies can send domestic 振込 (ふりこみ — bank transfers)
to Wise JPY accounts at domestic transfer speeds and fees. Wise was the
**first non-bank** to gain this access.

Bank code for domestic furikomi: **0200** (ワイズ・ペイメンツ・ジャパン)

### Type 1 License
Wise Payments Japan K.K. holds a Type 1 Fund Transfer Service Provider
(第一種資金移動業 / だいいっしゅしきんいどうぎょう) license from the Kanto
Local Finance Bureau (license #00040). This enables transactions up to
¥150M per transaction — more than sufficient for data sales.

### JDEX Compatibility (Probable)
JDEX (operated by Kanematsu via Dawex technology) is a B2B data marketplace.
Japanese B2B payments are 96% bank transfer (振込). If JDEX uses standard
振込 for seller payouts, and if they accept Wise's Zengin-accessible
account details (bank code 0200), then Wise should work.

**However:** This is unverified. JDEX may require a traditional Japanese
bank account (普通預金 / ふつうよきん at a 銀行 / ぎんこう), not a payment
institution account.

---

## The Bad News

### It Is NOT a Japanese Bank Account

You're correct — Wise is a **資金移動業者** (しきんいどうぎょうしゃ — fund
transfer service provider), not a **銀行** (ぎんこう — bank). This distinction
matters in several concrete ways:

1. **Corporate bank account for GK formation:** The GK formation process
   requires depositing initial capital into a Japanese bank account. Wise
   does not qualify. You still need a traditional Japanese bank (SMBC, GMO
   Aozora, PayPay Bank, etc.) for the corporate account of Misawa Data GK.

2. **Business Manager Visa scrutiny:** Immigration evaluators looking at
   "genuine business activity in Japan" expect to see a 銀行 account, not
   a 資金移動業者 account. Wise won't hurt, but it won't help demonstrate
   substance either.

3. **Some Japanese companies won't pay to non-bank accounts:** Larger
   corporations' accounting departments may flag a Wise account (bank code
   0200, non-traditional bank name) during their 振込 approval process.
   This is conservative bureaucratic caution, not a legal restriction.

4. **Holding limits if registered in Japan:** If you ever register your
   Wise address as Japan, a default ¥1M holding limit applies across all
   currencies. The Type 1 license raises the per-transaction limit to ¥150M,
   but the holding limit means you'd need to sweep funds regularly.
   Since your UG is registered in Germany, this likely doesn't apply to
   your current account — but verify.

### The IBAN Problem

Your JPY account has a **GB-prefixed IBAN** (GB27 TRWI...) and a UK bank
address. To a Japanese accounting department processing a 振込:

- The IBAN format is unfamiliar (Japanese domestic transfers use bank code
  + branch code + account number, not IBAN)
- The bank address says "London, United Kingdom"
- The company name on the invoice says "ML Upskill Agents UG" (German)

This creates a cognitive mismatch that could slow procurement at
conservative Japanese companies. Dr. Tanaka's accounting department might
classify this as an international wire transfer rather than a domestic
振込, which triggers different (slower, more expensive) processing.

**Mitigation:** When providing payment details to Japanese buyers, provide
the **domestic Zengin format** (bank code 0200 + branch + account number)
rather than the IBAN. Wise should provide these details in your JPY account
dashboard. This makes it look like a domestic transfer.

---

## Practical Recommendation

### For Now (Pre-GK, UG selling on JDEX)

Use Wise for receiving JPY payments. Provide Zengin-format account details
(not the GB IBAN) to Japanese buyers. This works for:
- JDEX marketplace payouts (if they support Zengin transfers to code 0200)
- Direct invoicing to Japanese companies
- Small to medium transactions (well within ¥150M Type 1 limit)

### After GK Formation

Open a proper Japanese 銀行 account for Misawa Data GK. Use that as the
primary receiving account for JDEX and Japanese customers. Use Wise for:
- Cross-border transfers (GK→UG royalty payments, sent in EUR)
- Currency conversion (JPY→EUR at Wise's competitive mid-market rate)
- Backup payment channel

### EUR Account (UG→GK Royalties)

The Belgium IBAN (BE79 9055...) is perfect for receiving royalty payments
from GK back to UG in EUR. The GK pays in JPY from its Japanese bank,
Wise converts at mid-market rate, UG receives EUR. This is the most
cost-effective way to repatriate royalty revenue vs. a traditional SWIFT
transfer through German banks.

---

## Action Items

- [ ] Check Wise dashboard for Zengin-format JPY account details (bank code
  0200 + branch + account number) — use THESE for Japanese invoices, not IBAN
- [ ] Register as JDEX seller and check what bank account formats they accept
- [ ] Verify whether JDEX generates 見積書/請求書 automatically or if we
  need to provide our own
- [ ] Once GK is formed, open traditional 銀行 account (GMO Aozora or
  PayPay Bank as first attempts)
- [ ] Set up Wise as the GK→UG royalty payment channel using EUR account

---

*Cross-references:*
- `GK-FORMATION-CHECKLIST.md` — banking "Valley of Death" section
- `IP-STRATEGY.md` — royalty flow architecture
- `../synth-factory/docs/USER-STORY-DR-TANAKA.md` — procurement friction
