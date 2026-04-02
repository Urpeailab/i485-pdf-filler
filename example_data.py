"""
Example data file for I-485 PDF Filler.

This file contains SAMPLE data to demonstrate the field mapping.
Replace ALL values with your actual information before using.

IMPORTANT: This is for the I-485 edition 01/20/25.
If you have a different edition, run the field dump first:
    python3 fill_i485.py --dump your-blank-i485.pdf

=== CRITICAL FIELD NAMING PITFALLS ===

These are real mistakes we made and fixed. Read carefully.

1. ADDRESS FIELDS — "Number" means APT number, NOT street number:
    - Part4Line7_StreetName[0] → "Street Number and Name" (FULL address: "500 EXAMPLE DRIVE")
    - P4Line7_Number[0] → "Apt/Suite/Floor Number" (ONLY apt number, e.g., "204")
    Same pattern for ALL address sections:
    - PriorStreetName = full street address ("456 OAK AVENUE")
    - PriorAddress_Number = apt number only
    - RecentStreetName = full street address (for address OUTSIDE US)
    - RecentNumber = apt number only

2. EMPLOYER FIELDS — EmployerName[0],[1],[2] are NOT 3 employers:
    - EmployerName[0] = "Employer or School (current or most recent)" — left column
    - EmployerName[1] = "Your Occupation" — right column
    - EmployerName[2] = "Name of Employer, Company, or School" — second row
    These are 3 fields for ONE employer, not 3 separate employers.

3. EMPLOYMENT SLOTS — The form has 2 complete employer blocks:
    - Item 7 (Pages 8-9 top): Current employer (name, occupation, address, dates)
    - Item 8 (Page 9 bottom): Second employer (name, occupation, address, dates)
    Additional employers go in Part 14.

4. "RECENT ADDRESS" SECTION — This is for address OUTSIDE the US:
    - RecentStreetName on Page 4 = "Most Recent Address Outside the United States"
    - It is NOT another prior US address slot.

5. PARENT BIRTH FIELDS — Pt5Line5/Pt5Line10 are COUNTRY, not city:
    - Pt5Line5_CityTownOfBirth[0] = "Enter Country of Birth" (Parent 1)
    - Pt5Line10_CityTownOfBirth[0] = "Enter Country of Birth" (Parent 2)
    Despite the field name saying "CityTown", the alt text says Country.

6. YES/NO CHECKBOXES — [0] and [1] indices are INCONSISTENT:
    Each question has TWO Button fields. Check FieldStateOption to know which
    index accepts "Y" and which accepts "N". Do NOT assume [0]=Yes, [1]=No.

7. PART 14 — Has separate reference fields, don't put refs in the text:
    Each entry has 3 separate fields:
    - Pt9Line3a_PageNumber[i] = Page number
    - Pt9Line3b_PartNumber[i] = Part number
    - Pt9Line3c_ItemNumber[i] = Item number
    The text field (P14_Line*_AdditionalInfo) should contain ONLY the data,
    not "Part X, Item Y, Page Z" — those go in their own fields.

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
    # Used other DOB? No → [0]=Y, [1]=N → set [1]=N
    f"{S}#subform[0].Pt1Line3_YN[1]": "N",

    # ============================================
    # PAGE 2 — A-Number, Sex, Birth, Passport
    # ============================================
    f"{S}#subform[1].Pt1Line4_YN[0]": "Y",
    f"{S}#subform[1].Pt1Line4_AlienNumber[0]": "123456789",
    f"{S}#subform[1].Pt1Line5_YN[1]": "N",
    f"{S}#subform[1].Pt1Line6_CB_Sex[1]": "M",  # [0]=F, [1]=M
    f"{S}#subform[1].Pt1Line7_CityTownOfBirth[0]": "MEXICO CITY",
    f"{S}#subform[1].Pt1Line7_CountryOfBirth[0]": "MEXICO",
    f"{S}#subform[1].Pt1Line8_CountryofCitizenshipNationality[0]": "MEXICO",
    f"{S}#subform[1].Pt1Line10_PassportNum[0]": "AB1234567",
    f"{S}#subform[1].Pt1Line10_ExpDate[0]": "12/31/2030",
    f"{S}#subform[1].Pt1Line10_Passport[0]": "MEXICO",
    f"{S}#subform[1].Pt1Line10_CityTown[0]": "MIAMI",
    f"{S}#subform[1].Pt1Line10_State[0]": "FL",
    f"{S}#subform[1].Pt1Line10_DateofArrival[0]": "06/15/2020",

    # ============================================
    # PAGE 3 — I-94, Status, Physical Address
    # ============================================
    f"{S}#subform[2].Pt1Line12_Status[0]": "B2",
    f"{S}#subform[2].Pt1Line14_Status[0]": "PENDING ASYLUM",
    # StreetNumberName = FULL address (number + street name)
    f"{S}#subform[2].Pt1Line18_StreetNumberName[0]": "123 MAIN STREET",
    f"{S}#subform[2].Pt1Line18_CityOrTown[0]": "ATLANTA",
    f"{S}#subform[2].Pt1Line18_State[0]": "GA",
    f"{S}#subform[2].Pt1Line18_ZipCode[0]": "30301",

    # ============================================
    # PAGE 4 — Prior Address + Address Outside US + SSN
    # ============================================
    # Prior US Address — PriorStreetName = FULL address (NOT just street name)
    f"{S}#subform[3].Pt1Line18_PriorStreetName[0]": "456 OAK AVENUE",
    f"{S}#subform[3].Pt1Line18_PriorCity[0]": "MARIETTA",
    f"{S}#subform[3].Pt1Line18_PriorState[0]": "GA",
    f"{S}#subform[3].Pt1Line18_PriorZipCode[0]": "30060",
    f"{S}#subform[3].Pt1Line18_PriorCountry[0]": "UNITED STATES OF AMERICA",
    f"{S}#subform[3].Pt1Line18_PriorDateFrom[0]": "03/01/2018",
    f"{S}#subform[3].Pt1Line18PriorDateTo[0]": "06/14/2020",

    # Most Recent Address OUTSIDE the US (not another US prior address!)
    f"{S}#subform[3].Pt1Line18_RecentStreetName[0]": "CALLE 80 #45-20",
    f"{S}#subform[3].Pt1Line18_RecentCity[0]": "MEXICO CITY",
    f"{S}#subform[3].Pt1Line18_RecentCountry[0]": "MEXICO",
    f"{S}#subform[3].Pt1Line18_RecentDateFrom[0]": "01/01/2015",
    f"{S}#subform[3].Pt1Line18_RecentDateTo[0]": "02/28/2018",

    f"{S}#subform[3].Pt1Line19_SSN[0]": "123456789",

    # ============================================
    # PAGE 8 — Part 4: Employment Slot 1 (current)
    # ============================================
    # EmployerName[0] = employer/school name (left column)
    # EmployerName[1] = your occupation (right column)
    # EmployerName[2] = name of employer (second row)
    f"{S}#subform[7].Pt4Line7_EmployerName[0]": "ACME HOSPITAL",
    f"{S}#subform[7].Pt4Line7_EmployerName[1]": "REGISTERED NURSE",
    f"{S}#subform[7].Pt4Line7_EmployerName[2]": "ACME HOSPITAL",

    # ============================================
    # PAGE 9 — Employment Slot 1 address + dates
    # ============================================
    # Part4Line7_StreetName = FULL street address
    # P4Line7_Number = ONLY apt/suite number
    f"{S}#subform[8].Part4Line7_StreetName[0]": "100 HOSPITAL DRIVE",
    f"{S}#subform[8].P4Line7_City[0]": "ATLANTA",
    f"{S}#subform[8].P4Line7_State[0]": "GA",
    f"{S}#subform[8].P4Line7_ZipCode[0]": "30301",
    f"{S}#subform[8].P4Line7_Country[0]": "UNITED STATES OF AMERICA",
    f"{S}#subform[8].Pt4Line7_DateFrom[0]": "01/15/2023",
    f"{S}#subform[8].Pt4Line7_DateTo[0]": "PRESENT",

    # Employment Slot 2 (Item 8 — second employer, Page 9 bottom)
    f"{S}#subform[8].Pt4Line8_EmployerName[0]": "CITY MEDICAL CENTER",
    f"{S}#subform[8].Pt4Line8_Occupation[0]": "MEDICAL ASSISTANT",
    f"{S}#subform[8].P4Line8_StreetName[0]": "200 HEALTH BLVD",
    f"{S}#subform[8].P4Line8_City[0]": "MARIETTA",
    f"{S}#subform[8].P4Line8_State[0]": "GA",
    f"{S}#subform[8].P4Line8_ZipCode[0]": "30060",
    f"{S}#subform[8].P4Line8_Country[0]": "UNITED STATES OF AMERICA",
    f"{S}#subform[8].Pt4Line8_DateFrom[0]": "06/01/2020",
    f"{S}#subform[8].Pt4Line8_DateTo[0]": "01/14/2023",

    # ============================================
    # PAGE 9 — Part 5: Parents
    # ============================================
    f"{S}#subform[8].Pt5Line1_FamilyName[0]": "DOE",
    f"{S}#subform[8].Pt5Line1_GivenName[0]": "ROBERT",
    f"{S}#subform[8].Pt5Line3_DateofBirth[0]": "03/20/1960",
    # Parent 1 Country of Birth (field name says CityTown but it means COUNTRY)
    f"{S}#subform[9].Pt5Line5_CityTownOfBirth[0]": "MEXICO",

    # Mother
    f"{S}#subform[9].Pt5Line6_FamilyName[0]": "GARCIA LOPEZ",
    f"{S}#subform[9].Pt5Line6_GivenName[0]": "MARIA",
    f"{S}#subform[9].Pt5Line8_DateofBirth[0]": "07/10/1962",
    # Parent 2 Country of Birth (field name says CityTown but it means COUNTRY)
    f"{S}#subform[9].Pt5Line10_CityTownOfBirth[0]": "MEXICO",

    # ============================================
    # PAGE 24 — Part 14: Additional Information
    # ============================================
    # Each entry has SEPARATE fields for Page/Part/Item references
    # Do NOT write "Part X, Item Y" inside the text — use the reference fields

    # Entry 2: Third employer (doesn't fit in the 2 form slots)
    f"{S}#subform[24].Pt9Line3a_PageNumber[0]": "8",       # Page Number
    f"{S}#subform[24].Pt9Line3b_PartNumber[0]": "4",       # Part Number
    f"{S}#subform[24].Pt9Line3c_ItemNumber[0]": "7",       # Item Number
    f"{S}#subform[24].P14_Line2_AdditionalInfo[0]": "URGENT CARE CLINIC, 300 ELM ST, ATLANTA GA 30301. Receptionist. From 01/2018 To 05/2020.",

    # Entry 3: Additional prior address
    f"{S}#subform[24].Pt9Line3a_PageNumber[1]": "4",
    f"{S}#subform[24].Pt9Line3b_PartNumber[1]": "1",
    f"{S}#subform[24].Pt9Line3c_ItemNumber[1]": "18",
    f"{S}#subform[24].P14_Line3_AdditionalInfo[0]": "789 PINE ST, SAVANNAH, GA 31401. From 01/2015 To 02/2018.",
}
