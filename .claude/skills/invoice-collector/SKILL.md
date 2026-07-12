# invoice-collector

Collect invoices/receipts from the user's Gmail into a git-tracked ledger —
**invoice number + amount only, never the attached files**.

Use this skill whenever the user asks to collect/aggregate invoices from email
("תאסוף את החשבוניות מהמייל", "כמה חשבוניות קיבלתי החודש", "תעדכן את טבלת
החשבוניות"), or asks about totals per vendor/month.

## Output

Ledger CSV at `invoices/ledger.csv` (repo root), one row per invoice/receipt:

```
date,vendor,invoice_number,amount,currency,direction,gmail_message_id,notes
```

- `date` — ISO `YYYY-MM-DD` (email date).
- `invoice_number` — the vendor's document number (מספר חשבונית / מספר מסמך /
  receipt #). For Wolt use the order number (מס' הזמנה).
- `amount` — numeric total, no thousands separators. `UNKNOWN` when the amount
  exists only inside an attached PDF (we never download attachments).
- `direction` — `income` when a business of the user issued the document,
  `expense` when the user is the payer. The user's businesses:
  **אדוונס אסתטיק / Advance(d) Aesthetic Academy, גלונס אסתטיקה,
  מוז-חולצות ומתנות (מסוף "אדוונס אקדמי"), אושר וענונו, יוסף דן גור**.
  Verifone POS vouchers from that terminal are always income. Emails the user
  SENT with a חשבונית attached (in:sent) are income too.
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
3. **Documents behind links — fetch them.** Most Israeli invoice systems
   (morning/mrng.to, taim, ezcount, digital-invoice, doctor-clinix, docserver,
   easybizy, YPAY, Verifone `tgw-api.verifone.co.il/invoices/...pdf`) put a
   view/download link in the body. `curl -sL` the link, extract PDF text with
   `pypdf` (`pip install pypdf` on fresh containers). If the PDF is a scanned
   image with no text layer, OCR it with Gemini (`GEMINI_API_KEY` is set):
   POST base64 `inline_data` to
   `https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash:generateContent`
   asking for number/total/issuer/customer as JSON. Also search `in:sent` for
   invoices the user issued (income).
4. **True Gmail attachments cannot be downloaded** — the Gmail MCP connector
   exposes attachment metadata only (no content tool). Vendors whose amount
   lives only in an attached PDF with no link (hyp/upapp, Partner, Google
   Workspace, IEC, cardcom, y-it/soofa, scanned rent invoices) stay `UNKNOWN`
   unless a link exists. Don't burn time trying; note it and move on.
   **Fallback via Google Drive**: the Drive connector reads PDFs/JPEGs with
   OCR (`read_file_content`). The user keeps a Drive folder named
   "חשבוניות למעקב 📥" (folder id `1-EdHr7QezErSBkOiX83d5Yx7JQ9O_CE5`) — when
   attachment-only invoices need resolving, ask the user to drag those
   attachments into that folder (Gmail: hover the attachment →
   "Add to Drive"), then `search_files` with
   `parentId = '1-EdHr7QezErSBkOiX83d5Yx7JQ9O_CE5'`,
   `read_file_content` each, extract number/total/issuer/customer, update the
   matching `UNKNOWN` ledger rows by `gmail_message_id`, and clear the folder
   note in the report.
   **Hands-free sync**: `apps-script/save-invoice-attachments.gs` (in this
   skill dir) runs daily inside the user's Google account and drops every
   invoice attachment into that folder, named `<gmailMessageId>_<filename>` —
   match files to ledger rows by that id prefix. If files for `UNKNOWN` rows
   are missing from the folder, the script may not be installed yet; the
   one-time install steps are at the top of the .gs file.
4. **Merge** the new rows:
   `python3 .claude/skills/invoice-collector/scripts/merge_ledger.py new_rows.csv`
   (dedupes by `gmail_message_id`, sorts by date, prints a per-vendor summary).
5. **Commit & push** `invoices/ledger.csv` on the working branch (sessions are
   ephemeral; anything not pushed is lost).
6. **Report** to the user: rows added, totals per currency **split by
   income/expense**, and which rows remain `UNKNOWN` (attachment-only).

## Vendor cheatsheet (learned from this mailbox)

| Sender | Number | Amount |
|---|---|---|
| `info@wolt.com` | order id in snippet | `סה"כ ILS X` in snippet |
| `invoice+statements@*` (Stripe: Anthropic, Make/Celonis, ElevenLabs, Lovable, Pipeboard, Clara) | `#N-N` in subject | first `$X` in body |
| `no_reply@email.apple.com` | `מספר מסמך` in body | total `X ₪` in body |
| `noreply@business-updates.facebook.com` (Meta Ads) | transaction id in body | `₪X` in snippet |
| `gateway@verifone.co.il` | voucher + invoice pdf link in body | `X₪ :סכום` in body — **income** (user's POS "אדוונס אקדמי"; body has customer name + treatment description) |
| `notify@morning.co`, `billing@easybizy.net`, `no-reply@ypay.co.il`, `taim@taim.co.il`, docserver/Holmes, ezcount, digital-invoice, doctor-clinix | number in subject/body | fetch the body link (see step 3) |
| `ipos@hyp.co.il` (Revo Pilates) | attachment filename | attachment-only → `UNKNOWN` |
| `Thankyou@partner.net.il`, `noreply@out.cardcom.co.il`, `payments-noreply@google.com` | month reference | body/PDF |
| `sales@payproglobal.com` | order `#N` in subject | `X USD` in snippet |
| `do-not-reply@gett.com` | ride receipt | `₪X` in snippet |

Marketing noise to skip: `info@wellybox.com`, newsletters mentioning
"invoice/חשבונית" without an actual document.
