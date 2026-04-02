"""
Example data file for I-485 PDF Filler.

This file contains SAMPLE data to demonstrate the field mapping.
Replace ALL values with your actual information before using.

IMPORTANT: This is for the I-485 edition 01/20/25.
If you have a different edition, run the field dump first:
    python3 fill_i485.py --dump your-blank-i485.pdf

=== HOW TO FIND THE CORRECT FIELD NAMES ===

1. Run the dump command to see all field names in your PDF:
    python3 fill_i485.py --dump blank-i485.pdf --output fields.json

2. For each field, the dump shows:
    - name: The exact field name to use as the dictionary key
    - type: "Text" (free text), "Button" (checkbox/radio), "Choice" (dropdown)
    - valid_values: For Buttons, the ONLY values the field accepts

3. CRITICAL for Yes/No questions:
    Each question has TWO Button fields: [0] and [1]
    One accepts "Y" (Yes), the other accepts "N" (No)
    You must check which index accepts which value!

    Example from field dump:
        Pt8Line25_YesNo[0] → valid_values: ["N"]  ← This is the NO button
        Pt8Line25_YesNo[1] → valid_values: ["Y"]  ← This is the YES button

    To answer YES → set [1] = "Y"
    To answer NO  → set [0] = "N"

    WARNING: The [0]/[1] mapping is NOT consistent across fields!
    Some fields have [0]=Yes, others have [0]=No. ALWAYS check the dump.

=== DATA STRUCTURE ===

The 'data' variable must be a dict mapping field names to string values.
"""

# Field name prefix (constant for I-485)
S = "form1[0]."

data = {
    # ============================================
    # PAGE 1 — Part 1: Information About You
    # ============================================
    f"{S}#subform[0].AlienNumber[0]": "123456789",
    f"{S}#subform[0].Pt1Line1_FamilyName[0]": "DOE",
    f"{S}#subform[0].Pt1Line1_GivenName[0]": "JOHN",
    f"{S}#subform[0].Pt1Line1_MiddleName[0]": "MICHAEL",
    f"{S}#subform[0].Pt1Line3_DOB[0]": "01/15/1990",  # MM/DD/YYYY
    # Used other DOB? No → Check dump: [0]=Y, [1]=N → set [1]=N
    f"{S}#subform[0].Pt1Line3_YN[1]": "N",

    # ============================================
    # PAGE 2 — A-Number, Sex, Birth, Passport
    # ============================================
    # Have A-Number? Yes → [0]=Y → set [0]=Y
    f"{S}#subform[1].Pt1Line4_YN[0]": "Y",
    f"{S}#subform[1].Pt1Line4_AlienNumber[0]": "123456789",
    # Other A-Numbers? No → [1]=N → set [1]=N
    f"{S}#subform[1].Pt1Line5_YN[1]": "N",
    # Sex: Male → [0]=F, [1]=M → set [1]=M
    f"{S}#subform[1].Pt1Line6_CB_Sex[1]": "M",
    f"{S}#subform[1].Pt1Line7_CityTownOfBirth[0]": "MEXICO CITY",
    f"{S}#subform[1].Pt1Line7_CountryOfBirth[0]": "MEXICO",
    f"{S}#subform[1].Pt1Line8_CountryofCitizenshipNationality[0]": "MEXICO",
    f"{S}#subform[1].Pt1Line10_PassportNum[0]": "AB1234567",
    f"{S}#subform[1].Pt1Line10_ExpDate[0]": "12/31/2030",
    f"{S}#subform[1].Pt1Line10_Passport[0]": "MEXICO",
    f"{S}#subform[1].Pt1Line10_CityTown[0]": "MIAMI",
    f"{S}#subform[1].Pt1Line10_State[0]": "FL",  # State dropdown
    f"{S}#subform[1].Pt1Line10_DateofArrival[0]": "06/15/2020",

    # ============================================
    # PAGE 3 — I-94, Status, Physical Address
    # ============================================
    f"{S}#subform[2].Pt1Line12_Date[0]": "12/15/2020",
    f"{S}#subform[2].Pt1Line12_Status[0]": "B2",
    f"{S}#subform[2].Pt1Line14_Status[0]": "PENDING ASYLUM",
    # Physical Address
    f"{S}#subform[2].Pt1Line18_StreetNumberName[0]": "123 MAIN STREET APT 4B",
    f"{S}#subform[2].Pt1Line18_CityOrTown[0]": "ATLANTA",
    f"{S}#subform[2].Pt1Line18_State[0]": "GA",
    f"{S}#subform[2].Pt1Line18_ZipCode[0]": "30301",

    # ============================================
    # PAGE 4 — Prior Address, SSN
    # ============================================
    f"{S}#subform[3].Pt1Line19_SSN[0]": "123456789",

    # ============================================
    # PAGES 14-17 — Part 8: Yes/No Questions (Criminal, Security)
    # ============================================
    # IMPORTANT: For each question, check the field dump to know
    # which index [0] or [1] is Yes vs No.
    #
    # Example: Pt8Line25 (Have you ever been arrested?)
    #   [0] states=['N', 'Off'] → this is the NO button
    #   [1] states=['Y', 'Off'] → this is the YES button
    #   To answer No: set [0] = "N"
    f"{S}#subform[14].Pt8Line25_YesNo[0]": "N",
    f"{S}#subform[14].Pt8Line26_YesNo[0]": "N",
    # ... continue for all Part 8 questions ...

    # ============================================
    # PAGE 19 — Part 9: Public Charge
    # ============================================
    # Household size (text field)
    f"{S}#subform[18].Pt9Line57_HouseholdSize[0]": "4",
    # Income bracket: A=$0-27k, B=$27k-71k, C=$71k-141k, D=$141k-321k, E=over $321k
    f"{S}#subform[18].Pt9Line53_CB[2]": "C",  # $71,201 - $141,000

    # ============================================
    # PAGE 23 — Contact Info & Signature
    # ============================================
    f"{S}#subform[22].Pt3Line3_DaytimePhoneNumber1[0]": "4045551234",
    f"{S}#subform[22].Pt3Line7b_DateofSignature[0]": "04/02/2026",
}
