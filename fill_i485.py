#!/usr/bin/env python3
"""
I-485 PDF Filler — Automated USCIS Form I-485 (Application to Register
Permanent Residence or Adjust Status) filling using Python + pdftk.

Supports the 01/20/25 edition of the I-485 form.

Usage:
    1. Download the blank I-485 PDF from https://www.uscis.gov/i-485
    2. Edit your_data.py with your information
    3. Run: python3 fill_i485.py --input blank-i485.pdf --data your_data.py --output filled-i485.pdf

Requirements:
    - Python 3.8+
    - pdftk (brew install pdftk-java on macOS, apt install pdftk on Ubuntu)

How it works:
    1. Reads the blank I-485 PDF and extracts all fillable field names
    2. Loads your data from a Python config file
    3. Generates an XFDF (XML Forms Data Format) file with your answers
    4. Uses pdftk to merge the XFDF into the PDF
    5. Runs a verification pass to confirm all fields were set correctly

Author: URPE AI Lab (https://urpeailab.com)
License: MIT
"""

import subprocess
import sys
import os
import argparse
import importlib.util
import json
from pathlib import Path


# ============================================
# CORE: XFDF Generation
# ============================================

def build_xfdf(data: dict) -> str:
    """
    Build an XFDF (XML Forms Data Format) string from a field→value dictionary.

    XFDF is the format pdftk uses to fill PDF form fields. It's essentially XML
    that maps field names to values.

    Args:
        data: Dictionary mapping PDF field names to their values.
              For text fields: the value is a string.
              For checkboxes/radio buttons: the value must match one of the
              field's FieldStateOption values (e.g., 'Y', 'N', 'Off', '1', etc.)

    Returns:
        Complete XFDF XML string ready to write to a file.
    """
    xfdf = '<?xml version="1.0" encoding="UTF-8"?>\n'
    xfdf += '<xfdf xmlns="http://ns.adobe.com/xfdf/" xml:space="preserve">\n'
    xfdf += '<fields>\n'
    for field_name, value in data.items():
        safe_val = (str(value)
                    .replace('&', '&amp;')
                    .replace('<', '&lt;')
                    .replace('>', '&gt;')
                    .replace('"', '&quot;'))
        xfdf += f'<field name="{field_name}"><value>{safe_val}</value></field>\n'
    xfdf += '</fields>\n'
    xfdf += '</xfdf>\n'
    return xfdf


# ============================================
# CORE: Field Discovery
# ============================================

def dump_fields(pdf_path: str) -> list[dict]:
    """
    Extract all fillable fields from a PDF using pdftk.

    This is the critical first step. USCIS changes field names between form
    editions, so you MUST dump the fields from YOUR specific PDF version
    and use those exact names.

    Returns a list of dicts with keys: name, type, value, states, alt
    """
    result = subprocess.run(
        ['pdftk', pdf_path, 'dump_data_fields'],
        capture_output=True, text=True
    )
    if result.returncode != 0:
        print(f"Error dumping fields: {result.stderr}", file=sys.stderr)
        sys.exit(1)

    fields = []
    blocks = result.stdout.split('---')
    for block in blocks:
        lines = block.strip().split('\n')
        field = {'name': '', 'type': '', 'value': '', 'states': [], 'alt': ''}
        for line in lines:
            if line.startswith('FieldName:'):
                field['name'] = line.split(':', 1)[1].strip()
            elif line.startswith('FieldType:'):
                field['type'] = line.split(':', 1)[1].strip()
            elif line.startswith('FieldValue:'):
                field['value'] = line.split(':', 1)[1].strip()
            elif line.startswith('FieldStateOption:'):
                field['states'].append(line.split(':', 1)[1].strip())
            elif line.startswith('FieldNameAlt:'):
                field['alt'] = line.split(':', 1)[1].strip()
        if field['name']:
            fields.append(field)

    return fields


def generate_field_map(pdf_path: str, output_path: str):
    """
    Generate a complete field map from a PDF as a JSON file.

    This is meant to be run ONCE when you first get a new version of the form.
    It produces a JSON file documenting every field, its type, and valid values.

    For Button (checkbox/radio) fields, pay special attention to:
    - FieldStateOption: These are the ONLY valid values for that field
    - The index [0] vs [1]: Each Yes/No question has TWO fields.
      One accepts 'Y' (Yes), the other accepts 'N' (No).
      YOU MUST CHECK which index accepts which value — it varies per field!

    Example:
        Pt8Line25_YesNo[0] states=['N', 'Off']  → This is the NO button
        Pt8Line25_YesNo[1] states=['Y', 'Off']  → This is the YES button

        To answer YES: set [1] = 'Y'
        To answer NO:  set [0] = 'N'
    """
    fields = dump_fields(pdf_path)

    # Organize by subform (page)
    organized = {}
    for f in fields:
        # Extract subform number
        parts = f['name'].split('#subform[')
        if len(parts) > 1:
            subform = parts[1].split(']')[0]
            page_key = f"page_{int(subform) + 1}"
        else:
            page_key = "other"

        if page_key not in organized:
            organized[page_key] = []

        organized[page_key].append({
            'name': f['name'],
            'type': f['type'],
            'valid_values': [s for s in f['states'] if s != 'Off'] if f['states'] else 'any text',
            'description': f['alt'][:100] if f['alt'] else ''
        })

    with open(output_path, 'w') as fp:
        json.dump(organized, fp, indent=2)

    # Print summary
    total = len(fields)
    buttons = sum(1 for f in fields if f['type'] == 'Button')
    texts = sum(1 for f in fields if f['type'] == 'Text')
    choices = sum(1 for f in fields if f['type'] == 'Choice')
    print(f"Field map saved to: {output_path}")
    print(f"  Total fields: {total}")
    print(f"  Text fields:  {texts}")
    print(f"  Buttons:      {buttons} (checkboxes, radio buttons)")
    print(f"  Dropdowns:    {choices}")


# ============================================
# CORE: Fill PDF
# ============================================

def fill_pdf(input_pdf: str, data: dict, output_pdf: str, flatten: bool = False):
    """
    Fill a PDF form with data using pdftk + XFDF.

    Args:
        input_pdf:  Path to the blank/source PDF
        data:       Field name → value mapping
        output_pdf: Where to save the filled PDF
        flatten:    If True, flatten the PDF (makes it non-editable but
                    ensures visual consistency). Default False for review.
    """
    # Generate XFDF
    xfdf = build_xfdf(data)
    xfdf_path = output_pdf.replace('.pdf', '.xfdf')
    with open(xfdf_path, 'w', encoding='utf-8') as f:
        f.write(xfdf)

    # Build pdftk command
    cmd = ['pdftk', input_pdf, 'fill_form', xfdf_path, 'output', output_pdf]
    if flatten:
        cmd.append('flatten')

    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode != 0:
        print(f"Error filling PDF: {result.stderr}", file=sys.stderr)
        sys.exit(1)

    size = os.path.getsize(output_pdf)
    print(f"PDF generated: {output_pdf} ({size:,} bytes)")
    if not flatten:
        print("  Mode: editable (not flattened) — you can still modify fields in a PDF editor")

    return output_pdf


# ============================================
# CORE: Verification
# ============================================

def verify_pdf(pdf_path: str, expected_data: dict) -> bool:
    """
    Verify that all fields were correctly set in the output PDF.

    This is critical because:
    1. If a field name doesn't exist in the PDF, pdftk silently ignores it
    2. If a Button value doesn't match a valid FieldStateOption, it may appear
       set in the data but not render visually in the PDF viewer
    3. Some PDF viewers (especially macOS Preview) don't render all form
       elements correctly — always verify with Adobe Reader or a dump

    Returns True if all fields verified correctly.
    """
    fields = dump_fields(pdf_path)
    field_map = {f['name']: f for f in fields}

    errors = []
    missing = []
    invalid = []
    correct = 0

    for field_name, expected_value in expected_data.items():
        if field_name not in field_map:
            missing.append(field_name)
            continue

        actual = field_map[field_name]

        # Check if value was set
        if actual['value'] != expected_value:
            if actual['value'] == '' or actual['value'] == 'Off':
                errors.append(f"  NOT SET: {field_name} (expected '{expected_value}')")
            else:
                errors.append(f"  WRONG:   {field_name} = '{actual['value']}' (expected '{expected_value}')")
            continue

        # For buttons, verify the value is a valid state option
        if actual['type'] == 'Button':
            valid_states = [s for s in actual['states'] if s != 'Off']
            if expected_value not in valid_states:
                invalid.append(
                    f"  INVALID: {field_name} = '{expected_value}' "
                    f"(valid options: {valid_states})"
                )
                continue

        correct += 1

    # Report
    print(f"\n{'='*50}")
    print(f"VERIFICATION REPORT")
    print(f"{'='*50}")
    print(f"Fields checked:     {len(expected_data)}")
    print(f"Correct:            {correct}")

    if missing:
        print(f"\nMISSING ({len(missing)} fields not found in PDF):")
        for m in missing:
            print(f"  {m}")

    if errors:
        print(f"\nERRORS ({len(errors)}):")
        for e in errors:
            print(e)

    if invalid:
        print(f"\nINVALID VALUES ({len(invalid)}):")
        for i in invalid:
            print(i)

    if not missing and not errors and not invalid:
        print("\nAll fields verified correctly!")
        return True

    return False


# ============================================
# DATA LOADER
# ============================================

def load_data_module(data_path: str) -> dict:
    """Load field data from a Python file containing a 'data' dictionary."""
    spec = importlib.util.spec_from_file_location("user_data", data_path)
    if spec is None or spec.loader is None:
        print(f"Error: Cannot load {data_path}", file=sys.stderr)
        sys.exit(1)

    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)

    if not hasattr(module, 'data'):
        print(f"Error: {data_path} must contain a 'data' dictionary", file=sys.stderr)
        sys.exit(1)

    return module.data


# ============================================
# CLI
# ============================================

def main():
    parser = argparse.ArgumentParser(
        description='Fill USCIS Form I-485 PDF automatically',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Step 1: Generate field map from your blank PDF
  python3 fill_i485.py --dump blank-i485.pdf --output fields.json

  # Step 2: Create your data file (see example_data.py)

  # Step 3: Fill the form
  python3 fill_i485.py --input blank-i485.pdf --data my_data.py --output filled.pdf

  # Step 4: Fill and flatten (non-editable, for submission)
  python3 fill_i485.py --input blank-i485.pdf --data my_data.py --output final.pdf --flatten
        """
    )

    parser.add_argument('--input', '-i', help='Path to blank I-485 PDF')
    parser.add_argument('--data', '-d', help='Path to Python data file with field values')
    parser.add_argument('--output', '-o', help='Path for output PDF')
    parser.add_argument('--dump', help='Dump field map from a PDF (for discovery)')
    parser.add_argument('--flatten', action='store_true', help='Flatten PDF (non-editable)')
    parser.add_argument('--no-verify', action='store_true', help='Skip verification step')

    args = parser.parse_args()

    # Mode 1: Dump fields
    if args.dump:
        output = args.output or args.dump.replace('.pdf', '-fields.json')
        generate_field_map(args.dump, output)
        return

    # Mode 2: Fill form
    if not args.input or not args.data or not args.output:
        parser.print_help()
        print("\nError: --input, --data, and --output are required for filling.", file=sys.stderr)
        sys.exit(1)

    # Validate inputs
    if not os.path.exists(args.input):
        print(f"Error: Input PDF not found: {args.input}", file=sys.stderr)
        sys.exit(1)
    if not os.path.exists(args.data):
        print(f"Error: Data file not found: {args.data}", file=sys.stderr)
        sys.exit(1)

    # Check pdftk
    try:
        subprocess.run(['pdftk', '--version'], capture_output=True, check=True)
    except FileNotFoundError:
        print("Error: pdftk not found. Install it:", file=sys.stderr)
        print("  macOS:  brew install pdftk-java", file=sys.stderr)
        print("  Ubuntu: sudo apt install pdftk", file=sys.stderr)
        print("  Windows: https://www.pdflabs.com/tools/pdftk-server/", file=sys.stderr)
        sys.exit(1)

    # Load data
    print(f"Loading data from {args.data}...")
    user_data = load_data_module(args.data)

    text_count = sum(1 for v in user_data.values() if len(str(v)) > 2)
    button_count = sum(1 for v in user_data.values() if str(v) in ('Y', 'N'))
    print(f"  Total fields: {len(user_data)}")
    print(f"  Text fields:  {text_count}")
    print(f"  Checkboxes:   {button_count}")

    # Fill
    print(f"\nFilling PDF...")
    fill_pdf(args.input, user_data, args.output, flatten=args.flatten)

    # Verify
    if not args.no_verify:
        print("\nVerifying...")
        verify_pdf(args.output, user_data)


if __name__ == '__main__':
    main()
