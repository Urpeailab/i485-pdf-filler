"""Example data schema for fill_i485_v2.py — principal + derivative family case.

Use this as a template. The same schema works for both principal and
derivative applicants; fill_i485_v2.py decides which Part 2 checkboxes
to tick based on whether --principal or --derivatives flagged it.

Save each applicant as its own JSON file:
    principal.json   (the person named on the I-140/I-360/I-130 petition)
    spouse.json      (derivative)
    child1.json      (derivative)

A derivative inherits from the principal:
  - I-360 receipt number (Pt2Line2_Receipt)
  - Principal's name (Pt2Line2_FamilyName/GivenName/MiddleName)
  - Principal's immigrant category (Pt2Line3c_CB)

Everything else (biographics, addresses, employment) is per-applicant.
"""

EXAMPLE_PRINCIPAL = {
    "names": {
        "apellidos": "DOE",
        "given_name": "JANE",
        "middle_name": None,
    },
    "identidad": {
        "fecha_nacimiento": "1985-04-15",
        "sexo": "F",
        "ciudad_nacimiento": "GUADALAJARA",
        "pais_nacimiento": "MEXICO",
        "nacionalidad_actual": "MEXICO",
    },
    "pasaporte_actual": {
        "numero": "G12345678",
        "fecha_expiracion": "2030-01-10",
        "pais_emisor": "MEXICO",
    },
    "visa_usa": {
        "control_number": "20221234567890",
        "fecha_emision": "2022-06-01",
    },
    "ultima_entrada_usa": {
        "fecha": "2022-11-01",
        "puerto_entrada_ciudad": "ATLANTA",
        "puerto_entrada_estado": "GA",
        "descripcion_admision": "R-1 Religious Worker",
        "status_al_entrar": "R-1",
    },
    "estatus_migratorio_actual": {
        "status_actual": "R-1",
        "fecha_expiracion": "2027-03-31",
    },
    "direccion_actual_usa": {
        "linea1": "500 EXAMPLE DRIVE APT 204",
        "ciudad": "ATLANTA",
        "estado": "GA",
        "zip": "30301",
        "telefono": "404-555-0100",
        "desde": "2022-11-01",
    },
    "direcciones_5_anos": [
        {"direccion": "500 EXAMPLE DRIVE APT 204, ATLANTA, GA 30301", "inicio": "2022-11", "fin": "Actual"},
        {"direccion": "123 PRIOR STREET, MIAMI, FL 33101", "inicio": "2020-01", "fin": "2022-10"},
    ],
    "ultima_direccion_pre_usa": {
        "direccion": "CALLE EJEMPLO 45",
        "ciudad": "GUADALAJARA",
        "pais": "MEXICO",
        "codigo_postal": "44100",
        "fin": "2020-01",
    },
    "empleo_actual": {
        "empleador": "EXAMPLE CHURCH OF ATLANTA",
        "ocupacion": "MINISTER OF RELIGION",
        "desde": "2022-11",
    },
    "i360_approval": {
        "receipt_number": "WAC0000000000",
        "priority_date": "2023-03-22",
        "class": "SD6",
        "notice_date": "2025-08-15",
    },
}

EXAMPLE_DERIVATIVE_SPOUSE = {
    "names": {"apellidos": "DOE", "given_name": "JOHN", "middle_name": None},
    "identidad": {
        "fecha_nacimiento": "1983-09-20",
        "sexo": "M",
        "ciudad_nacimiento": "MONTERREY",
        "pais_nacimiento": "MEXICO",
        "nacionalidad_actual": "MEXICO",
    },
    "pasaporte_actual": {
        "numero": "G87654321",
        "fecha_expiracion": "2029-05-05",
        "pais_emisor": "MEXICO",
    },
    "ultima_entrada_usa": {
        "fecha": "2022-11-01",
        "puerto_entrada_ciudad": "ATLANTA",
        "puerto_entrada_estado": "GA",
        "descripcion_admision": "R-2 Spouse of Religious Worker",
        "status_al_entrar": "R-2",
    },
    "estatus_migratorio_actual": {
        "status_actual": "R-2",
        "fecha_expiracion": "2027-03-31",
    },
    "direccion_actual_usa": {
        "linea1": "500 EXAMPLE DRIVE APT 204",
        "ciudad": "ATLANTA",
        "estado": "GA",
        "zip": "30301",
        "telefono": "404-555-0100",
        "desde": "2022-11-01",
    },
}
