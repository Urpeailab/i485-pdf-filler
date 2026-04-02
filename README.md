# I-485 PDF Filler

Automated USCIS Form I-485 (Application to Register Permanent Residence or Adjust Status) filling using Python + pdftk.

**No cloud services. No data leaves your machine. 100% local.**

## Why this exists

Filling the I-485 is a 20+ page nightmare with 700+ fields. This tool lets you define your answers in a simple Python file and generates a correctly filled PDF in seconds. It handles the three hardest parts automatically:

1. **Field name discovery** — USCIS PDFs use cryptic internal names like `form1[0].#subform[14].Pt8Line25_YesNo[1]`. This tool dumps and maps them all.
2. **Checkbox index hell** — Each Yes/No question has TWO button fields (`[0]` and `[1]`), and which one is "Yes" vs "No" is **inconsistent across fields**. The tool verifies every single one.
3. **Cross-version compatibility** — When USCIS releases a new form edition, field names change. The dump tool lets you generate a fresh mapping in seconds.

## Requirements

- Python 3.8+
- [pdftk](https://www.pdflabs.com/tools/pdftk-server/) (PDF Toolkit)

### Install pdftk

```bash
# macOS
brew install pdftk-java

# Ubuntu / Debian
sudo apt install pdftk

# Windows
# Download from https://www.pdflabs.com/tools/pdftk-server/
```

## Quick Start

### Step 1: Download the blank I-485

Download from [uscis.gov/i-485](https://www.uscis.gov/i-485) and save it as `blank-i485.pdf`.

### Step 2: Dump the field map

```bash
python3 fill_i485.py --dump blank-i485.pdf --output fields.json
```

This generates a JSON file with every fillable field, its type, and valid values. You'll reference this to build your data file.

### Step 3: Create your data file

Copy `example_data.py` to `my_data.py` and fill in your information:

```bash
cp example_data.py my_data.py
# Edit my_data.py with your actual data
```

See [Understanding the Field Map](#understanding-the-field-map) below for how to read the dump.

### Step 4: Fill the form

```bash
# Editable (for review)
python3 fill_i485.py --input blank-i485.pdf --data my_data.py --output filled-i485.pdf

# Flattened (for submission — non-editable)
python3 fill_i485.py --input blank-i485.pdf --data my_data.py --output final-i485.pdf --flatten
```

The tool automatically runs a verification pass and reports any issues.

## Understanding the Field Map

When you run `--dump`, you get a JSON like this:

```json
{
  "page_1": [
    {
      "name": "form1[0].#subform[0].Pt1Line1_FamilyName[0]",
      "type": "Text",
      "valid_values": "any text",
      "description": "Part 1. Your last name..."
    },
    {
      "name": "form1[0].#subform[0].Pt1Line3_YN[0]",
      "type": "Button",
      "valid_values": ["Y"],
      "description": "Have you ever used any other date of birth? Select Yes."
    },
    {
      "name": "form1[0].#subform[0].Pt1Line3_YN[1]",
      "type": "Button",
      "valid_values": ["N"],
      "description": "Have you ever used any other date of birth? Select No."
    }
  ]
}
```

### Field Types

| Type | Description | How to set |
|------|-------------|------------|
| `Text` | Free text input | Any string value |
| `Button` | Checkbox or radio button | Must be one of `valid_values` |
| `Choice` | Dropdown/select | Must be one of `valid_values` |

### The Yes/No Trap

Each Yes/No question has **two** Button fields:

```
Pt8Line25_YesNo[0]  valid_values: ["N"]   ← Setting this to "N" marks NO
Pt8Line25_YesNo[1]  valid_values: ["Y"]   ← Setting this to "Y" marks YES
```

**The [0] and [1] indices are NOT consistent.** Some questions have `[0]=Yes, [1]=No`, others have it reversed. Always check `valid_values` from the dump.

If you set a value that doesn't match the field's valid options, pdftk will silently accept it but the checkbox **won't render** in the PDF. The verification step catches this.

### Critical Field Naming Pitfalls

These are real mistakes discovered during production use. Each one caused incorrect PDF output that looked right in the data but was wrong on the form.

#### 1. Address fields: "Number" means APT number, not street number

Every address section has two fields that look similar but mean different things:

| Field | What it actually is | Example value |
|-------|-------------------|---------------|
| `Part4Line7_StreetName[0]` | Full street address | `"1000 WATERMAN WAY"` |
| `P4Line7_Number[0]` | Apartment/Suite number only | `"204"` |
| `PriorStreetName[0]` | Full prior address | `"520 ROYAL JAY LANE"` |
| `PriorAddress_Number[0]` | Apt number only | `""` |

If you put `"520"` in `PriorAddress_Number`, the form shows it as an apartment number, not a street number.

#### 2. Employer fields: `EmployerName[0],[1],[2]` are NOT 3 employers

These three indexed fields are **one row with three columns**:

| Field | Column on form | What to put |
|-------|---------------|-------------|
| `EmployerName[0]` | "Employer or School (current)" | `"ACME HOSPITAL"` |
| `EmployerName[1]` | "Your Occupation" | `"REGISTERED NURSE"` |
| `EmployerName[2]` | "Name of Employer, Company" | `"ACME HOSPITAL"` |

#### 3. The form has 2 employment slots, not 1

| Slot | Location | Fields |
|------|----------|--------|
| **Item 7** | Page 8 (name) + Page 9 top (address/dates) | `Pt4Line7_*`, `Part4Line7_*`, `P4Line7_*` |
| **Item 8** | Page 9 bottom | `Pt4Line8_*`, `P4Line8_*` |

Item 8's description says "most recent employer outside the United States" but it functions as the second employment slot. Additional employers go in Part 14.

#### 4. "Recent Address" = address OUTSIDE the US

The `RecentStreetName` / `RecentCity` / `RecentCountry` fields on Page 4 are labeled "Most Recent Address **Outside the United States**". They are NOT another prior US address slot.

#### 5. Parent birth fields say "CityTown" but mean Country

Despite the field name `Pt5Line5_CityTownOfBirth`, the alt text says "Enter **Country** of Birth". Put the country, not the city:

```python
# WRONG — puts city in the country field
f"{S}#subform[9].Pt5Line5_CityTownOfBirth[0]": "CIRCASIA",
# CORRECT
f"{S}#subform[9].Pt5Line5_CityTownOfBirth[0]": "COLOMBIA",
```

#### 6. Part 14 has separate reference fields

Each Part 14 entry has **separate fields** for Page, Part, and Item numbers. Do NOT write the reference inside the text:

```python
# WRONG — reference embedded in text
f"{S}#subform[24].P14_Line2_AdditionalInfo[0]": "Part 1, Item 18, Page 4. 2320 MARGARITA DR...",

# CORRECT — reference in its own fields, text is just the data
f"{S}#subform[24].Pt9Line3a_PageNumber[0]": "4",
f"{S}#subform[24].Pt9Line3b_PartNumber[0]": "1",
f"{S}#subform[24].Pt9Line3c_ItemNumber[0]": "18",
f"{S}#subform[24].P14_Line2_AdditionalInfo[0]": "2320 MARGARITA DR, MYRTLE BEACH, SC 29577. From 11/10/2019 To 07/31/2025.",
```

## Email Extraction (for law firms)

If your clients send their questionnaire responses via email, the `extract_from_email.py` script can fetch and parse the data directly from Gmail — no manual copy-paste needed.

### How it works

```
┌──────────────────────┐
│ Client fills          │
│ questionnaire &       │──→ Sends email to firm
│ hits Reply            │
└──────────────────────┘
           │
           ▼
┌──────────────────────┐
│ extract_from_email.py │  ← Authenticates via OAuth2,
│                       │     fetches email via Gmail API,
│                       │     parses structured text
└──────────┬───────────┘
           │
           ▼
┌──────────────────────┐
│ Parsed data dict      │  ← name, DOB, SSN, addresses,
│                       │     employment, parents, spouse...
└──────────┬───────────┘
           │
           ▼
┌──────────────────────┐
│ applicant_data.py     │  ← Map parsed values to PDF fields
└──────────┬───────────┘
           │
           ▼
┌──────────────────────┐
│ fill_i485.py          │  ← Generates the filled PDF
└──────────────────────┘
```

### Usage

```bash
# Search Gmail for the questionnaire email
python3 extract_from_email.py --account firm@company.com --search "from:karen cuestionario i-485"

# Fetch a specific email by ID
python3 extract_from_email.py --account firm@company.com --message-id 19d4f572956effdc

# Just dump the email content (for inspection)
python3 extract_from_email.py --account firm@company.com --search "from:karen" --dump-only
```

### Gmail API Setup (one-time)

1. Go to [Google Cloud Console](https://console.cloud.google.com/apis/credentials)
2. Create OAuth 2.0 credentials (Desktop app type)
3. Download the JSON → save as `~/Library/Application Support/gogcli/credentials.json`
4. Enable the **Gmail API** in your Google Cloud project
5. Run the OAuth flow once to get a refresh token, then store it in macOS Keychain:

```bash
security add-generic-password -s "gogcli" \
    -a "token:default:your@email.com" \
    -w '{"refresh_token": "YOUR_REFRESH_TOKEN"}'
```

### What it parses

The parser extracts from the standard URPE questionnaire format:

| Field | Example |
|-------|---------|
| Full name | Paula Andrea Ocampo Giraldo |
| Date of birth | 06/13/1978 |
| Birth city/country | Circasia, Colombia |
| SSN | 820-54-1573 |
| Current address | 30502 Seaforth Dr, Sorrento FL 32776 |
| Prior addresses (US) | Multiple with dates |
| Prior address (abroad) | With dates |
| Port of entry | Fort Lauderdale FL |
| Entry date & status | 02/22/2019, B2 Tourist |
| Current employer | Company, address, position, dates |
| Prior employment | Multiple entries with dates |
| Parents | Names, DOB, birth places |
| Spouse | Name, DOB, A-number, SSN |
| Children | Name, DOB, A-number |
| Biometrics | Height, weight, eye/hair color |
| Criminal/violations | Yes/No answers |

The parser uses regex patterns tuned for Spanish-language questionnaires, but can be adapted for English versions.

## Architecture

```
┌─────────────────┐
│ Your Data (.py)  │  ← You define field→value pairs
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│  fill_i485.py   │  ← Generates XFDF from your data
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│    XFDF File    │  ← XML Forms Data Format
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│     pdftk       │  ← Merges XFDF into blank PDF
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│  Filled PDF     │  ← Verified output
└─────────────────┘
```

### Why XFDF + pdftk?

We tried several approaches before landing on this one:

| Approach | Result |
|----------|--------|
| `pypdf` / `PyPDF2` | Fields appeared filled when read back programmatically, but were **invisible** when opening the PDF. Silent failure. |
| `pdftk` with FDF | Works but FDF format is harder to generate correctly and has encoding issues with special characters. |
| `pdftk` with XFDF | Works perfectly. XFDF is just XML, easy to generate, handles Unicode, and pdftk processes it reliably. |
| Adobe JavaScript | Requires Adobe Acrobat (not free) and is platform-dependent. |

## File Structure

```
i485-pdf-filler/
├── fill_i485.py              # Main tool (dump, fill, verify)
├── extract_from_email.py     # Gmail data extraction + questionnaire parser
├── example_data.py           # Sample data file with field documentation
├── field_reference/
│   └── i485_01-20-25_fields.md  # Complete field reference for edition 01/20/25
└── README.md
```

## Troubleshooting

### Checkboxes not visible

1. **Wrong field index**: The most common issue. Run `--dump` and check which `[0]`/`[1]` accepts `Y` vs `N`.
2. **PDF viewer**: macOS Preview sometimes doesn't render form fields. Open with Adobe Acrobat Reader.
3. **Invalid value**: Setting `"Yes"` instead of `"Y"`, or `"1"` instead of the field's actual state option.

### Fields not filling

1. **Field name mismatch**: Names change between form editions. Always dump fields from YOUR PDF.
2. **Wrong subform index**: `#subform[0]` = page 1, `#subform[1]` = page 2, etc. But pages can be reordered in the dump output.

### Data appears in wrong location on the form

1. **Street number as apt number**: You put the full address in the `_Number` field instead of `_StreetName`. See [Critical Field Naming Pitfalls](#critical-field-naming-pitfalls).
2. **City in country field**: Some field names are misleading (e.g., `CityTownOfBirth` actually means Country for parent fields). Always read the `FieldNameAlt` from the dump.
3. **3 employers in 1 slot**: The `EmployerName[0],[1],[2]` fields are columns of one row, not separate employers.

### Verification fails

Run with `--no-verify` to skip verification and still get the PDF, then investigate the specific fields that failed.

## Disclaimer

This tool is provided as-is for educational purposes. It does not constitute legal advice. Always review the filled form carefully before submission and consult with an immigration attorney.

## License

MIT License. Created by [URPE AI Lab](https://urpeailab.com).
