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

This is the single most important thing to understand. Each Yes/No question has **two** Button fields:

```
Pt8Line25_YesNo[0]  valid_values: ["N"]   ← Setting this to "N" marks NO
Pt8Line25_YesNo[1]  valid_values: ["Y"]   ← Setting this to "Y" marks YES
```

**The [0] and [1] indices are NOT consistent.** Some questions have `[0]=Yes, [1]=No`, others have it reversed. Always check `valid_values` from the dump.

If you set a value that doesn't match the field's valid options, pdftk will silently accept it but the checkbox **won't render** in the PDF. The verification step catches this.

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
├── fill_i485.py      # Main tool (dump, fill, verify)
├── example_data.py   # Sample data file with field documentation
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

### Verification fails

Run with `--no-verify` to skip verification and still get the PDF, then investigate the specific fields that failed.

## Disclaimer

This tool is provided as-is for educational purposes. It does not constitute legal advice. Always review the filled form carefully before submission and consult with an immigration attorney.

## License

MIT License. Created by [URPE AI Lab](https://urpeailab.com).
