#!/usr/bin/env python3
"""
Email Data Extractor for I-485 PDF Filler

Fetches applicant questionnaire data directly from a Gmail inbox and
generates a ready-to-use data file for fill_i485.py.

This script is designed for immigration law firms that receive client
questionnaires via email. Instead of manually transcribing 175+ fields,
this extracts the data automatically.

=== WORKFLOW ===

    Client fills questionnaire → Sends email → This script extracts →
    Generates data.py → fill_i485.py fills the PDF

=== REQUIREMENTS ===

    1. Google OAuth2 credentials (client_id + client_secret)
       Stored at: ~/Library/Application Support/gogcli/credentials.json

    2. Refresh token for the Gmail account stored in macOS Keychain:
       security find-generic-password -s "gogcli" -a "token:default:<email>" -w

    3. Gmail API enabled in Google Cloud Console

=== SETUP (one-time) ===

    1. Go to https://console.cloud.google.com/apis/credentials
    2. Create OAuth 2.0 credentials (Desktop app)
    3. Download the JSON and save as:
       ~/Library/Application Support/gogcli/credentials.json
    4. Enable the Gmail API in your Google Cloud project
    5. Run the OAuth flow once to get a refresh token:

       import google_auth_oauthlib.flow
       flow = google_auth_oauthlib.flow.InstalledAppFlow.from_client_secrets_file(
           'credentials.json', scopes=['https://www.googleapis.com/auth/gmail.readonly'])
       creds = flow.run_local_server(port=0)
       print(creds.refresh_token)

    6. Store the refresh token in macOS Keychain:
       security add-generic-password -s "gogcli" \\
           -a "token:default:your@email.com" \\
           -w '{"refresh_token": "YOUR_TOKEN"}'

=== USAGE ===

    # Search for a specific email by sender + keyword
    python3 extract_from_email.py --account user@firm.com --search "from:karen i-485"

    # Fetch a specific email by Gmail message ID
    python3 extract_from_email.py --account user@firm.com --message-id 19d4f572956effdc

    # Just dump the email content (for inspection before generating data)
    python3 extract_from_email.py --account user@firm.com --search "from:karen cuestionario" --dump-only

Author: URPE AI Lab (https://urpeailab.com)
License: MIT
"""

import json
import os
import sys
import subprocess
import urllib.request
import urllib.parse
import base64
import re
import argparse
from datetime import datetime


# ============================================
# GMAIL AUTH
# ============================================

def get_access_token(account_email: str) -> str:
    """
    Get a fresh Gmail API access token using stored OAuth2 credentials.

    Credentials are stored in two places:
    1. Client ID/Secret: ~/Library/Application Support/gogcli/credentials.json
    2. Refresh Token: macOS Keychain under service "gogcli"

    This pattern works for any Google Workspace or personal Gmail account.
    """
    # Load client credentials
    cred_path = os.path.expanduser(
        "~/Library/Application Support/gogcli/credentials.json"
    )
    if not os.path.exists(cred_path):
        print(f"Error: Credentials not found at {cred_path}", file=sys.stderr)
        print("See the setup instructions in this script's docstring.", file=sys.stderr)
        sys.exit(1)

    with open(cred_path) as f:
        creds = json.load(f)

    # Get refresh token from macOS Keychain
    result = subprocess.run(
        ["security", "find-generic-password", "-s", "gogcli",
         "-a", f"token:default:{account_email}", "-w"],
        capture_output=True, text=True
    )
    if result.returncode != 0:
        print(f"Error: No token found in Keychain for {account_email}", file=sys.stderr)
        print(f"Store it with: security add-generic-password -s gogcli "
              f"-a 'token:default:{account_email}' -w '<json>'", file=sys.stderr)
        sys.exit(1)

    token_data = json.loads(result.stdout.strip())

    # Exchange refresh token for access token
    data = urllib.parse.urlencode({
        'client_id': creds['client_id'],
        'client_secret': creds['client_secret'],
        'refresh_token': token_data['refresh_token'],
        'grant_type': 'refresh_token'
    }).encode()

    req = urllib.request.Request('https://oauth2.googleapis.com/token', data=data)
    resp = json.loads(urllib.request.urlopen(req).read())
    return resp['access_token']


# ============================================
# GMAIL API
# ============================================

def gmail_api(access_token: str, endpoint: str) -> dict:
    """Make a Gmail API request."""
    url = f"https://gmail.googleapis.com/gmail/v1/users/me/{endpoint}"
    req = urllib.request.Request(url, headers={'Authorization': f'Bearer {access_token}'})
    return json.loads(urllib.request.urlopen(req).read())


def search_messages(access_token: str, query: str, max_results: int = 5) -> list:
    """Search Gmail messages by query string."""
    encoded_query = urllib.parse.quote(query)
    data = gmail_api(access_token, f"messages?q={encoded_query}&maxResults={max_results}")
    return data.get('messages', [])


def get_message(access_token: str, message_id: str) -> dict:
    """Fetch a complete Gmail message by ID."""
    return gmail_api(access_token, f"messages/{message_id}?format=full")


def extract_body(payload: dict) -> list:
    """
    Recursively extract text content from a Gmail message payload.

    Gmail messages can be deeply nested multipart structures.
    This walks through all parts and extracts text/plain and text/html.
    """
    parts = []
    mime = payload.get('mimeType', '')

    if payload.get('body', {}).get('data'):
        text = base64.urlsafe_b64decode(
            payload['body']['data']
        ).decode('utf-8', errors='replace')
        parts.append((mime, text))

    for part in payload.get('parts', []):
        parts.extend(extract_body(part))

    return parts


def get_email_text(msg: dict) -> str:
    """
    Get the plaintext content of an email message.
    Falls back to stripping HTML tags if no plain text is available.
    """
    body_parts = extract_body(msg['payload'])

    # Prefer plain text
    for mime, text in body_parts:
        if 'text/plain' in mime:
            return text

    # Fall back to cleaned HTML
    for mime, text in body_parts:
        if 'text/html' in mime:
            clean = re.sub(r'<style[^>]*>.*?</style>', '', text, flags=re.DOTALL)
            clean = re.sub(r'<br\s*/?>', '\n', clean, flags=re.IGNORECASE)
            clean = re.sub(r'<[^>]+>', '', clean)
            clean = re.sub(r'&nbsp;', ' ', clean)
            clean = re.sub(r'&amp;', '&', clean)
            clean = re.sub(r'&lt;', '<', clean)
            clean = re.sub(r'&gt;', '>', clean)
            clean = re.sub(r'\n\s*\n', '\n', clean)
            return clean.strip()

    return ""


def get_email_headers(msg: dict) -> dict:
    """Extract common headers from a Gmail message."""
    return {h['name']: h['value'] for h in msg['payload']['headers']}


# ============================================
# QUESTIONNAIRE PARSER
# ============================================

def parse_questionnaire(text: str) -> dict:
    """
    Parse a structured I-485 questionnaire from email text into
    a dictionary of extracted fields.

    This parser is designed for the standard URPE questionnaire format
    but can be adapted for other formats. It uses section headers
    and field labels to identify data.

    Returns a dict with normalized keys like:
        full_name, dob, birth_city, birth_country, ssn,
        current_address, prior_addresses, employment, parents, etc.
    """
    data = {}

    # Helper: extract value after a label
    def extract_after(label, content=text):
        pattern = rf'{re.escape(label)}\s*:?\s*(.+?)(?:\n|$)'
        match = re.search(pattern, content, re.IGNORECASE)
        return match.group(1).strip().strip('*') if match else None

    # --- Personal Info ---
    data['full_name'] = extract_after('Nombre completo')
    data['other_names'] = extract_after('Otros nombres usados')
    data['dob'] = extract_after('Fecha de nacimiento')
    data['birth_city_country'] = extract_after('Ciudad y pa.s de nacimiento')
    data['nationality'] = extract_after('Nacionalidad')
    data['ssn'] = extract_after('N.mero de Seguro Social')
    data['marital_status'] = extract_after('Estado civil actual')

    # --- Current Address ---
    addr_match = re.search(
        r'Direcci.n actual en EE\.UU\..*?:\s*\n?\s*(.+?)(?:\n|$)',
        text, re.IGNORECASE
    )
    if addr_match:
        data['current_address'] = addr_match.group(1).strip().strip('*')

    # --- Prior Addresses ---
    prior_match = re.search(
        r'Direcciones anteriores en EE\.UU\..*?\n([\s\S]*?)(?=Direcciones en su pa.s|3\.|$)',
        text, re.IGNORECASE
    )
    if prior_match:
        lines = [l.strip().strip('*') for l in prior_match.group(1).strip().split('\n') if l.strip()]
        data['prior_addresses_us'] = lines

    abroad_match = re.search(
        r'Direcciones en su pa.s.*?:\s*\n?\s*([\s\S]*?)(?=3\.|INFORMACI.N DE ENTRADA|$)',
        text, re.IGNORECASE
    )
    if abroad_match:
        data['prior_address_abroad'] = abroad_match.group(1).strip().strip('*')

    # --- Entry Info ---
    data['port_of_entry'] = extract_after('Ciudad/puerto por el que ingres')
    data['last_entry_date'] = extract_after('Fecha de .ltima entrada')
    data['entry_status'] = extract_after('Estatus con el que ingres')
    data['i94_number'] = extract_after('N.mero I-94')
    data['visa_type'] = extract_after('Tipo de visa')
    data['visa_expiry'] = extract_after('Fecha de vencimiento de la visa')
    data['current_status'] = extract_after('Estatus migratorio actual')

    # --- Employment ---
    emp_match = re.search(
        r'Empleo actual.*?:\s*\n?([\s\S]*?)(?=Empleos anteriores|$)',
        text, re.IGNORECASE
    )
    if emp_match:
        data['current_employer'] = emp_match.group(1).strip().strip('*')

    prior_emp_match = re.search(
        r'Empleos anteriores.*?:\s*\n?([\s\S]*?)(?=Per.odos sin empleo|5\.|$)',
        text, re.IGNORECASE
    )
    if prior_emp_match:
        data['prior_employment'] = prior_emp_match.group(1).strip().strip('*')

    # --- Parents ---
    data['father_name'] = extract_after('Padre.*?Nombre completo') or extract_after('Padre:.*?Nombre completo')
    father_section = re.search(r'Padre:?\s*\n([\s\S]*?)(?=Madre|$)', text, re.IGNORECASE)
    if father_section:
        data['father_name'] = extract_after('Nombre completo', father_section.group(1)) or data.get('father_name')
        data['father_dob'] = extract_after('Fecha de nacimiento', father_section.group(1))
        data['father_birth'] = extract_after('Ciudad y pa.s de nacimiento', father_section.group(1))

    mother_section = re.search(r'Madre:?\s*(.+?)?\n([\s\S]*?)(?=6\.|INFORMACI.N DEL C.NYUGE|$)', text, re.IGNORECASE)
    if mother_section:
        data['mother_name'] = mother_section.group(1).strip().strip('*') if mother_section.group(1) else None
        data['mother_name'] = data['mother_name'] or extract_after('Nombre completo', mother_section.group(2))
        data['mother_dob'] = extract_after('Fecha de nacimiento', mother_section.group(2))
        data['mother_birth'] = extract_after('Ciudad y pa.s de nacimiento', mother_section.group(2))

    # --- Spouse ---
    spouse_section = re.search(
        r'INFORMACI.N DEL C.NYUGE.*?\n([\s\S]*?)(?=7\.|INFORMACI.N DE HIJOS|$)',
        text, re.IGNORECASE
    )
    if spouse_section:
        s = spouse_section.group(1)
        data['spouse_name'] = extract_after('Nombre completo', s)
        data['spouse_dob'] = extract_after('Fecha de nacimiento', s)
        data['spouse_birth'] = extract_after('Ciudad y pa.s de nacimiento', s)
        data['spouse_a_number'] = extract_after('N.mero A', s)
        data['spouse_ssn'] = extract_after('N.mero de Seguro Social', s)
        data['marriage_date'] = extract_after('fecha de matrimonio', s)

    # --- Children ---
    children_section = re.search(
        r'INFORMACI.N DE HIJOS.*?\n([\s\S]*?)(?=8\.|FAMILIARES QUE APLICAN|$)',
        text, re.IGNORECASE
    )
    if children_section:
        s = children_section.group(1)
        data['child_name'] = extract_after('Nombre completo', s)
        data['child_dob'] = extract_after('Fecha de nacimiento', s)
        data['child_birth'] = extract_after('Ciudad y pa.s de nacimiento', s)
        data['child_a_number'] = extract_after('N.mero A', s)

    # --- Biographic ---
    data['ethnicity'] = extract_after('Etnicidad')
    data['height'] = extract_after('Estatura')
    data['weight'] = extract_after('Peso')
    data['eye_color'] = extract_after('Color de ojos')
    data['hair_color'] = extract_after('Color de cabello')

    # --- Criminal / Violations ---
    data['worked_without_auth'] = extract_after('Ha trabajado sin autorizaci')
    data['immigration_violation'] = extract_after('Ha tenido alguna violaci.n migratoria')
    data['arrested'] = extract_after('Ha sido arrestado')

    # Clean None values
    return {k: v for k, v in data.items() if v is not None}


# ============================================
# OUTPUT
# ============================================

def print_parsed_data(parsed: dict):
    """Pretty-print the parsed questionnaire data."""
    print(f"\n{'='*60}")
    print("PARSED QUESTIONNAIRE DATA")
    print(f"{'='*60}")
    for key, value in parsed.items():
        if isinstance(value, list):
            print(f"\n{key}:")
            for item in value:
                print(f"  - {item}")
        else:
            display = str(value)[:100]
            print(f"  {key}: {display}")


def save_raw_text(text: str, output_path: str):
    """Save the raw email text for manual review."""
    with open(output_path, 'w') as f:
        f.write(text)
    print(f"Raw email text saved to: {output_path}")


# ============================================
# CLI
# ============================================

def main():
    parser = argparse.ArgumentParser(
        description='Extract I-485 questionnaire data from Gmail',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Search for the latest questionnaire email from Karen
  python3 extract_from_email.py --account firm@company.com --search "from:karen cuestionario i-485"

  # Fetch a specific email by Gmail API message ID
  python3 extract_from_email.py --account firm@company.com --message-id 19d4f572956effdc

  # Just dump the email content without parsing
  python3 extract_from_email.py --account firm@company.com --search "from:karen" --dump-only

  # Save parsed data for review
  python3 extract_from_email.py --account firm@company.com --search "from:karen" --save-text raw_email.txt
        """
    )

    parser.add_argument('--account', '-a', required=True,
                        help='Gmail account to read from (e.g., user@firm.com)')
    parser.add_argument('--search', '-s',
                        help='Gmail search query (e.g., "from:karen i-485")')
    parser.add_argument('--message-id', '-m',
                        help='Specific Gmail message ID (hex format from API)')
    parser.add_argument('--dump-only', action='store_true',
                        help='Just print the email content, don\'t parse')
    parser.add_argument('--save-text', help='Save raw email text to a file')
    parser.add_argument('--max-results', type=int, default=5,
                        help='Max search results (default: 5)')

    args = parser.parse_args()

    if not args.search and not args.message_id:
        parser.print_help()
        print("\nError: Either --search or --message-id is required.", file=sys.stderr)
        sys.exit(1)

    # Authenticate
    print(f"Authenticating as {args.account}...")
    access_token = get_access_token(args.account)
    print("  Authenticated successfully.")

    # Find the message
    if args.message_id:
        msg_id = args.message_id
    else:
        print(f"Searching: {args.search}")
        results = search_messages(access_token, args.search, args.max_results)
        if not results:
            print("No messages found.", file=sys.stderr)
            sys.exit(1)

        # Show search results and pick the first one
        print(f"Found {len(results)} message(s):")
        for i, ref in enumerate(results):
            msg = get_message(access_token, ref['id'])
            headers = get_email_headers(msg)
            print(f"  [{i}] {headers.get('Date', '?')} — {headers.get('From', '?')}")
            print(f"      Subject: {headers.get('Subject', '?')}")
            print(f"      ID: {ref['id']}")
        msg_id = results[0]['id']
        print(f"\nUsing first result: {msg_id}")

    # Fetch the message
    print(f"\nFetching message {msg_id}...")
    msg = get_message(access_token, msg_id)
    headers = get_email_headers(msg)
    print(f"  From: {headers.get('From', '?')}")
    print(f"  Subject: {headers.get('Subject', '?')}")
    print(f"  Date: {headers.get('Date', '?')}")

    # Extract text
    email_text = get_email_text(msg)

    if args.save_text:
        save_raw_text(email_text, args.save_text)

    if args.dump_only:
        print(f"\n{'='*60}")
        print("EMAIL CONTENT")
        print(f"{'='*60}")
        print(email_text)
        return

    # Parse the questionnaire
    print("\nParsing questionnaire...")
    parsed = parse_questionnaire(email_text)
    print_parsed_data(parsed)

    print(f"\n{'='*60}")
    print("NEXT STEPS")
    print(f"{'='*60}")
    print("1. Review the parsed data above for accuracy")
    print("2. Create a data file: cp example_data.py applicant_data.py")
    print("3. Map the parsed values into the field names from your field dump")
    print("4. Run: python3 fill_i485.py --input blank.pdf --data applicant_data.py --output filled.pdf")


if __name__ == '__main__':
    main()
