#!/usr/bin/env python3
"""Fill I-485 using pypdf with principal/derivative support for family AOS cases.

Two improvements over fill_i485.py:
  1. pypdf instead of pdftk+XFDF (no external binary, handles NeedAppearances).
  2. Principal/derivative pattern — the principal applicant's I-360 receipt
     number and name are inherited by dependent family members filing
     concurrent I-485s off the same petition (common in EB-4, EB-2, EB-3 cases).

Usage:
    python3 fill_i485_v2.py \\
        --blank blank-i485.pdf \\
        --principal principal.json \\
        --derivatives spouse.json child1.json child2.json \\
        --output-dir ./filled

Each JSON file describes one applicant. The first --principal is filled as
the principal; every --derivative inherits the principal's name + I-360
receipt number in Part 2 and gets marked as derivative.

See example_family_data.py for the JSON schema.
"""
import argparse
import json
from pathlib import Path
from pypdf import PdfReader, PdfWriter
from pypdf.generic import BooleanObject, NameObject


def mmddyyyy(iso):
    """Convert ISO date (YYYY-MM-DD) to MM/DD/YYYY. Empty on invalid input."""
    if not iso or not isinstance(iso, str) or len(iso) < 10:
        return ""
    try:
        y, m, d = iso[:10].split("-")
        return f"{m}/{d}/{y}"
    except Exception:
        return ""


def build_short_vals(person, principal=None):
    """Return dict {short_field_name: value} from one applicant's data.

    short_field_name is the last segment of the PDF's internal field name
    (e.g. "Pt1Line1_FamilyName[0]"). We resolve it to the full path at
    fill time so the same logic works across form editions as long as the
    short names are stable.
    """
    vals = {}
    is_principal = principal is None

    names = person.get("names", {}) or {}
    idn = person.get("identidad", {}) or {}
    passport = person.get("pasaporte_actual", {}) or {}
    visa = person.get("visa_usa", {}) or {}
    status = person.get("estatus_migratorio_actual", {}) or {}
    entry = person.get("ultima_entrada_usa", {}) or {}
    addr = person.get("direccion_actual_usa", {}) or {}
    prior_addrs = person.get("direcciones_5_anos", []) or []
    recent_outside = person.get("ultima_direccion_pre_usa", {}) or {}
    emp = person.get("empleo_actual", {}) or {}

    vals["Pt1Line1_FamilyName[0]"] = names.get("apellidos", "")
    vals["Pt1Line1_GivenName[0]"] = names.get("given_name", "")
    vals["Pt1Line1_MiddleName[0]"] = names.get("middle_name") or ""

    vals["Pt1Line3_DOB[0]"] = mmddyyyy(idn.get("fecha_nacimiento"))
    vals["Pt1Line3_YN[1]"] = "/1"
    vals["Pt1Line5_YN[1]"] = "/1"

    sex = idn.get("sexo")
    if sex == "F":
        vals["Pt1Line6_CB_Sex[0]"] = "/1"
    elif sex == "M":
        vals["Pt1Line6_CB_Sex[1]"] = "/1"

    vals["Pt1Line7_CityTownOfBirth[0]"] = idn.get("ciudad_nacimiento", "")
    vals["Pt1Line7_CountryOfBirth[0]"] = idn.get("pais_nacimiento", "")
    vals["Pt1Line8_CountryofCitizenshipNationality[0]"] = idn.get("nacionalidad_actual", "")

    vals["Pt1Line10_PassportNum[0]"] = passport.get("numero", "")
    vals["Pt1Line10_ExpDate[0]"] = mmddyyyy(passport.get("fecha_expiracion"))
    vals["Pt1Line10_Passport[0]"] = passport.get("pais_emisor", "")
    vals["Pt1Line10_VisaNum[0]"] = visa.get("visa_number_rojo") or visa.get("control_number", "")
    vals["Pt1Line10_NonImmDate[0]"] = mmddyyyy(visa.get("fecha_emision"))
    vals["Pt1Line10_CityTown[0]"] = entry.get("puerto_entrada_ciudad", "")
    vals["Pt1Line10_State[0]"] = entry.get("puerto_entrada_estado", "")
    vals["Pt1Line10_DateofArrival[0]"] = mmddyyyy(entry.get("fecha"))

    vals["Pt1Line11_Admitted[0]"] = entry.get("descripcion_admision", "")
    vals["Pt1Line12_Status[0]"] = entry.get("status_al_entrar", "")

    vals["Pt1Line13_YN[0]"] = "/1"

    vals["Pt1Line14_Status[0]"] = status.get("status_actual", "")
    vals["Pt1Line15_Date[0]"] = mmddyyyy(status.get("fecha_expiracion"))

    vals["Pt1Line16_YN[1]"] = "/1"
    vals["Pt1Line17_YN[0]"] = "/1"

    vals["Pt1Line18_StreetNumberName[0]"] = addr.get("linea1", "")
    vals["Pt1Line18_CityOrTown[0]"] = addr.get("ciudad", "")
    vals["Pt1Line18_State[0]"] = addr.get("estado", "")
    vals["Pt1Line18_ZipCode[0]"] = (addr.get("zip") or "").split("-")[0]
    vals["Pt1Line18_Date[0]"] = mmddyyyy(addr.get("desde"))
    vals["Pt1Line18_YN[0]"] = "/1"
    vals["Pt1Line18_last5yrs_YN[1]"] = "/1"

    if len(prior_addrs) > 1:
        prev = prior_addrs[1]
        parts = [p.strip() for p in prev.get("direccion", "").split(",")]
        if len(parts) >= 3:
            vals["Pt1Line18_PriorStreetName[0]"] = parts[0]
            vals["Pt1Line18_PriorCity[0]"] = parts[1]
            state_zip = parts[2].split()
            if len(state_zip) >= 2:
                vals["Pt1Line18_PriorState[0]"] = state_zip[0]
                vals["Pt1Line18_PriorZipCode[0]"] = state_zip[1]
        inicio = prev.get("inicio")
        if inicio and len(inicio) == 7:
            vals["Pt1Line18_PriorDateFrom[0]"] = mmddyyyy(inicio + "-01")
        fin = prev.get("fin")
        if fin and fin != "Actual" and len(fin) == 7:
            vals["Pt1Line18PriorDateTo[0]"] = mmddyyyy(fin + "-01")

    if recent_outside:
        direccion = recent_outside.get("direccion", "")
        vals["Pt1Line18_RecentStreetName[0]"] = direccion.split(",")[0] if direccion else ""
        vals["Pt1Line18_RecentCity[0]"] = recent_outside.get("ciudad", "")
        vals["Pt1Line18_RecentCountry[0]"] = recent_outside.get("pais", "")
        vals["Pt1Line18_RecentPostalCode[0]"] = recent_outside.get("codigo_postal", "")
        fin = recent_outside.get("fin")
        if fin and len(fin) == 7:
            vals["Pt1Line18_RecentDateTo[0]"] = mmddyyyy(fin + "-01")

    vals["Pt1Line19_YN[0]"] = "/1"
    vals["Pt1Line19_SSA_YN[0]"] = "/1"
    vals["Pt1Line19_Consent_YN[0]"] = "/1"

    vals["Pt2Line1_YN[1]"] = "/1"

    i360_src = person if is_principal else principal
    i360 = i360_src.get("i360_approval", {}) or {}
    if i360.get("receipt_number"):
        vals["Pt2Line2_Receipt[0]"] = i360["receipt_number"]

    if is_principal:
        vals["Pt2Line2_CB[0]"] = "/1"
        vals["Pt2Line3c_CB[9]"] = "/1"
    else:
        vals["Pt2Line2_CB[1]"] = "/1"
        vals["Pt2Line3c_CB[9]"] = "/1"
        pnames = principal.get("names", {})
        vals["Pt2Line2_FamilyName[0]"] = pnames.get("apellidos", "")
        vals["Pt2Line2_GivenName[0]"] = pnames.get("given_name", "")
        vals["Pt2Line2_MiddleName[0]"] = pnames.get("middle_name") or ""

    vals["Pt3Line3_DaytimePhoneNumber1[0]"] = addr.get("telefono", "")

    vals["Pt4Line1_YN[0]"] = "/1"
    vals["Pt4Line5_YN[0]"] = "/1"
    vals["Pt4Line6_YN[0]"] = "/1"

    if emp.get("empleador"):
        vals["Pt4Line7_EmployerName[2]"] = emp.get("empleador", "")
        vals["Pt4Line7_EmployerName[1]"] = emp.get("ocupacion", "")
        desde = emp.get("desde", "")
        if desde and len(desde) == 7:
            vals["Pt4Line7_DateFrom[0]"] = mmddyyyy(desde + "-01")

    return {k: v for k, v in vals.items() if v not in ("", None)}


def map_short_to_full(reader):
    """Build short_name -> full_field_name map from PDF AcroForm."""
    fields = reader.get_fields()
    smap = {}
    for fn in fields.keys():
        short = fn.split(".")[-1]
        if short not in smap:
            smap[short] = fn
    return smap


def checkbox_on_value(reader, full_name):
    """Return the 'on' value for a checkbox (e.g. '/Y', '/1', '/F') or None.

    USCIS forms use inconsistent state values across checkboxes. The actual
    options are stored in /_States_; we read them per-field rather than guess.
    """
    fields = reader.get_fields()
    f = fields.get(full_name)
    if not f:
        return None
    states = f.get("/_States_") or []
    for s in states:
        if s != "/Off":
            return s
    return None


def fill_one(blank_pdf, person_data, output_pdf, principal_data=None):
    reader = PdfReader(str(blank_pdf))
    short_map = map_short_to_full(reader)

    short_vals = build_short_vals(person_data, principal=principal_data)
    full_vals = {}
    missed = []
    for short, val in short_vals.items():
        full = short_map.get(short)
        if not full:
            missed.append(short)
            continue
        if isinstance(val, str) and val.startswith("/"):
            on_val = checkbox_on_value(reader, full)
            full_vals[full] = on_val or val
        else:
            full_vals[full] = val

    writer = PdfWriter(clone_from=reader)
    if "/AcroForm" in writer._root_object:
        writer._root_object["/AcroForm"][NameObject("/NeedAppearances")] = BooleanObject(True)

    for page in writer.pages:
        writer.update_page_form_field_values(page, full_vals)

    with open(output_pdf, "wb") as fh:
        writer.write(fh)
    print(f"OK {Path(output_pdf).name}: {len(full_vals)} fields filled (miss={len(missed)})")
    for m in missed:
        print(f"   MISS: {m}")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--blank", required=True, help="Path to blank-i485.pdf")
    ap.add_argument("--principal", required=True, help="JSON for principal applicant")
    ap.add_argument("--derivatives", nargs="*", default=[], help="JSONs for derivative applicants")
    ap.add_argument("--output-dir", default="./filled")
    args = ap.parse_args()

    out = Path(args.output_dir)
    out.mkdir(parents=True, exist_ok=True)

    principal = json.loads(Path(args.principal).read_text())
    principal_name = principal.get("names", {}).get("given_name", "principal").lower()
    fill_one(args.blank, principal, out / f"I-485-{principal_name}.pdf")

    for dep_path in args.derivatives:
        dep = json.loads(Path(dep_path).read_text())
        dep_name = dep.get("names", {}).get("given_name", "dep").lower()
        fill_one(args.blank, dep, out / f"I-485-{dep_name}.pdf", principal_data=principal)


if __name__ == "__main__":
    main()
