# invoice-collector

Collect invoices/receipts from the user's Gmail into a git-tracked ledger —
**invoice number + amount only, never the attached files**.

Use this skill whenever the user asks to collect/aggregate invoices from email
("תאסוף את החשבוניות מהמייל", "כמה חשבוניות קיבלתי החודש", "תעדכן את טבלת
החשבוניות"), or asks about totals per vendor/month.

## Output

Ledger CSV at `invoices/ledger.csv` (repo root), one row per invoice/receipt:

```
date,vendor,invoice_number,amount,currency,gmail_message_id,notes
```

- `date` — ISO `YYYY-MM-DD` (email date).
- `invoice_number` — the vendor's document number (מספר חשבונית / מספר מסמך /
  receipt #). For Wolt use the order number (מס' הזמנה).
- `amount` — numeric total, no thousands separators. `UNKNOWN` when the amount
  exists only inside an attached PDF (we never download attachments).
- `gmail_message_id` — dedupe key. Never emit two rows with the same id unless
  one email carries two documents (then add a `-1`/`-2` suffix in `notes`).

## Workflow

1. **Search** Gmail via the Gmail MCP tools. Use ALL of these queries and
   paginate each to the end of the requested date range (add
   `after:YYYY/MM/DD` / `before:YYYY/MM/DD`):
   - `חשבונית OR קבלה`
   - `invoice OR receipt`
   Snippets already contain vendor + amount for many senders (Wolt, Meta,
   Verifone, Gett, Apple subscription renewals) — harvest those without
   fetching the full message.
2. **Fetch bodies only when the snippet lacks the amount or number**
   (`get_message`). Large results are saved to a tool-results file — extract
   with `jq -r '.plaintextBody // .htmlBody'` + regex for
   `(₪|ILS|NIS|\$|USD|EUR)\s?[0-9,.]+` and vice-versa. Fan the fetches out to
   general-purpose subagents in batches (~15 ids each) that return bare CSV
   rows — this keeps the main context small.
3. **Never download attachments.** If the amount is only in the PDF, record
   `UNKNOWN` — the user explicitly does not want the files.
4. **Merge** the new rows:
   `python3 .claude/skills/invoice-collector/scripts/merge_ledger.py new_rows.csv`
   (dedupes by `gmail_message_id`, sorts by date, prints a per-vendor summary).
5. **Commit & push** `invoices/ledger.csv` on the working branch (sessions are
   ephemeral; anything not pushed is lost).
6. **Report** to the user: rows added, totals per currency, and which rows are
   `UNKNOWN` (offer to resolve them from the PDFs only if the user asks).

## Vendor cheatsheet (learned from this mailbox)

| Sender | Number | Amount |
|---|---|---|
| `info@wolt.com` | order id in snippet | `סה"כ ILS X` in snippet |
| `invoice+statements@*` (Stripe: Anthropic, Make/Celonis, ElevenLabs, Lovable, Pipeboard, Clara) | `#N-N` in subject | first `$X` in body |
| `no_reply@email.apple.com` | `מספר מסמך` in body | total `X ₪` in body |
| `noreply@business-updates.facebook.com` (Meta Ads) | transaction id in body | `₪X` in snippet |
| `gateway@verifone.co.il` | terminal voucher | `X₪ :סכום` in snippet (this is the user's own POS — likely income, note it) |
| `ipos@hyp.co.il`, `notify@morning.co`, `billing@easybizy.net`, `no-reply@ypay.co.il`, `taim@taim.co.il`, docserver/Holmes | number in subject/body | usually PDF-only → `UNKNOWN` |
| `Thankyou@partner.net.il`, `noreply@out.cardcom.co.il`, `payments-noreply@google.com` | month reference | body/PDF |
| `sales@payproglobal.com` | order `#N` in subject | `X USD` in snippet |
| `do-not-reply@gett.com` | ride receipt | `₪X` in snippet |

Marketing noise to skip: `info@wellybox.com`, newsletters mentioning
"invoice/חשבונית" without an actual document.
