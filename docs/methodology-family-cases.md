# Methodology — Family I-485 cases off a single I-360 / I-140

This is the playbook we follow when one approved employment-based petition
(I-360 religious worker, I-140 professional, etc.) unlocks concurrent
I-485s for the principal beneficiary and their derivative family members.
Everything below was written after running an actual case end-to-end, so
the order reflects where the friction really is, not an idealized flow.

## When this applies

You have:

- One approved I-360 or I-140 with a receipt number (WAC/EAC/LIN/SRC-XX-XXX-XXXXX).
- A principal beneficiary (the worker named on the petition).
- One or more derivatives — spouse on the matching dependent visa (R-2 / L-2
  / H-4 / etc.) and unmarried children under 21.
- A priority date that is either current on the State Department's
  Visa Bulletin for the relevant preference category, or current under
  "Dates for Filing" if USCIS has announced they are accepting that chart
  this month.

If the priority date is not current by either chart, you can still prepare
the package, but you cannot file it. Skip to "Visa Bulletin gating" below
before doing anything else.

## Step 1 — Inventory the raw documents

Before touching any form, list every document you have. In our case the
source folder was a Google Drive tree with scanned passports, entry
stamps, marriage/birth certificates, an I-797 approval notice for the
I-360, a verification-of-employment (VOE) letter, and prior
URPE-questionnaire intake data from a previous filing.

Build a spreadsheet/TSV with columns: `file_name`, `applicant`,
`document_type`, `issue_date`, `notes`. This becomes the audit trail
you'll append to the Google Doc at the end.

Mark each scanned PDF as either:

- **Text layer present** — you can run `pdftotext -layout file.pdf -` and get usable text.
- **Scanned / no text layer** — you need OCR. We route those through a
  multimodal model (Claude Read tool, Gemini Vision, or Tesseract) to
  extract fields.

Don't skip this. Later when the Google Doc asks "did you verify this
against a primary source?" you want to say yes for every field.

## Step 2 — Decide the immigrant category and fill the I-360 fields first

For EB-4 Special Immigrants (SD6 Minister of Religion, SD7 Religious
Worker, etc.) you'll populate:

- `Pt2Line2_CB[0]` → principal, `Pt2Line2_CB[1]` → derivative.
- `Pt2Line2_Receipt[0]` — the WAC/EAC number from the I-797 approval
  notice, exactly as printed.
- `Pt2Line3c_CB[9]` — the category checkbox (Minister of Religion in our
  case). The index `[9]` comes from the PDF field map; verify yours with
  `--dump` before assuming.
- Derivatives additionally need `Pt2Line2_FamilyName[0]`,
  `GivenName[0]`, `MiddleName[0]` — these are the **principal's** name,
  not the derivative's. USCIS is matching the derivative back to the
  approved petition.

In `fill_i485_v2.py` we pass the principal's full JSON into each
derivative's fill call; the builder reads `i360_approval.receipt_number`
from the principal when the current applicant is flagged derivative.

## Step 3 — Visa Bulletin gating

Before filing:

1. Check the current month's Visa Bulletin at travel.state.gov.
2. Find the preference category (e.g. "Employment-Based — Fourth Preference — Certain Religious Workers SD and SR").
3. Compare the priority date on the I-797 against both:
   - **Final Action Dates** (what actually issues green cards).
   - **Dates for Filing** (what USCIS sometimes accepts for I-485 intake).
4. Check USCIS's "When to File" page for the same month — that page
   declares which of the two charts USCIS is honoring for I-485 intake.
   This announcement is what matters; the Visa Bulletin alone is advisory.

If your priority date is **before** the applicable cutoff → you can file.
If it is **on or after** the cutoff → you cannot file yet. Prepare the
package, store it, and set a reminder to re-check every month.

In our case the I-797 explicitly flagged "not eligible to file adjustment
of status at this time." That language is template boilerplate, but it
aligned with a real retrogression: the priority date landed after the
cutoff, so we were correct to hold the filing.

## Step 4 — Fill the forms

Run `fill_i485_v2.py` with `--principal` + `--derivatives`. The script:

1. Reads the blank USCIS PDF with `pypdf`.
2. Maps every short field name (e.g. `Pt1Line1_FamilyName[0]`) to the full
   internal path. This insulates you from USCIS reshuffling subform
   indices between editions.
3. Resolves checkbox "on" values from `/_States_` on each field — never
   hardcode `/Y` or `/1`, because USCIS uses different state names per
   checkbox.
4. Writes with `NeedAppearances=True` so Preview.app, Acrobat, and USCIS's
   own viewers render the values. Without it, fields look blank even
   though the data is in the PDF structure.

Expected output: ~50-60 fields populated per person on a typical case.
The gaps (SSN, A-Number, some prior addresses) should be surfaced, not
silently skipped — see Step 5.

## Step 5 — Write the gaps document

The filled PDF alone is not the deliverable. The deliverable is
**PDF + gaps document**. The gaps document goes to the attorney or client
and lists:

- Every field we could not fill with confidence.
- Why it matters (hard block vs. nice-to-have).
- What source we'd need (primary document, client confirmation, etc.).
- Data consistency questions the attorney should resolve (e.g., employment
  start date in VOE vs. prior intake form).
- The full list of documents used, so the reviewer can trace any answer
  back to its source.

This is the artifact that protects the filing. Write it in prose, not
bulleted machine output. The attorney reading it should feel like a
paralegal wrote it, not a script.

Common gaps on religious-worker family cases:

- **A-Number** — often not on the front of the I-797. Check the back or
  wait until biometrics assigns one. Listed as "None" pre-biometric is
  usually acceptable.
- **SSN** — many derivatives don't have one. Answer Part 1 Item 19 as
  "No SSN issued," then check the SSA card + consent boxes.
- **Prior addresses** — 5-year history is required. If the client's
  answers only cover 3 years, flag it.
- **Employment dates** — if VOE and prior intake disagree, the VOE wins
  (formal document on employer letterhead trumps self-reported intake).
- **Part 14 additional info** — most dependent cases need Part 14 entries
  for extra employers, extra prior addresses, or expired non-immigrant
  status that the principal form cannot capture in the allotted slots.

## Step 6 — Deliver

Deliverables per case:

- `I-485-<Principal>.pdf` (filled)
- `I-485-<Dependent1>.pdf` (filled)
- ... one per applicant
- `I-485-GAPS-Y-DOCUMENTOS.md` (prose gaps document)
- Source documents inventory (TSV or Drive folder link)

Upload to a shared Drive folder and share with the reviewing attorney.
Do not commit any of these files to git — see "PII protection" below.

## PII protection

This repo's `.gitignore` already excludes:

- `*.pdf` — filled forms always contain personal data.
- `*.xfdf` — intermediate form data.
- `*_data.py` except `example_*.py` — per-case JSON/Python data.

Additionally, in your working directory:

- Keep raw scans in a directory outside the repo root, or add it to
  `.gitignore` explicitly.
- Don't paste receipt numbers, A-Numbers, SSNs, or passport numbers into
  code comments, commit messages, or PR descriptions.
- The methodology doc you commit (this file) should describe the pattern,
  never the specific client.

## What we didn't automate (yet)

- **Priority date monitoring** — right now we manually re-check each
  month. A small cron that scrapes the Visa Bulletin + compares against a
  list of pending cases would close the loop.
- **I-693 medical exam tracking** — must be within civil-surgeon's
  signature window; worth tracking per-case.
- **G-28 generation** — attorney-specific, not included here.
- **I-765 and I-131 companion forms** — usually filed concurrently for
  work/travel authorization. Same field-map pattern applies; separate
  fillers.

Those are the natural next scripts to build on top of this one.
