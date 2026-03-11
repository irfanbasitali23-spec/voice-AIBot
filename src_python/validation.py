import re
from datetime import datetime
from src_python.models.patient import US_STATES


def validate_create_patient(data):
    """Validate patient creation data. Returns list of error dicts or empty list."""
    errors = []

    # first_name
    fn = (data.get("first_name") or "").strip()
    if not fn:
        errors.append({"field": "first_name", "message": "First name is required"})
    elif len(fn) < 1 or len(fn) > 50:
        errors.append({"field": "first_name", "message": "First name must be 1-50 characters"})
    elif not re.match(r"^[a-zA-Z\s'\-]+$", fn):
        errors.append({"field": "first_name", "message": "First name can only contain letters, hyphens, and apostrophes"})

    # last_name
    ln = (data.get("last_name") or "").strip()
    if not ln:
        errors.append({"field": "last_name", "message": "Last name is required"})
    elif len(ln) < 1 or len(ln) > 50:
        errors.append({"field": "last_name", "message": "Last name must be 1-50 characters"})
    elif not re.match(r"^[a-zA-Z\s'\-]+$", ln):
        errors.append({"field": "last_name", "message": "Last name can only contain letters, hyphens, and apostrophes"})

    # date_of_birth
    dob_str = data.get("date_of_birth")
    if not dob_str:
        errors.append({"field": "date_of_birth", "message": "Date of birth is required"})
    else:
        try:
            dob = datetime.fromisoformat(dob_str.replace("Z", "+00:00")) if "T" in dob_str else datetime.strptime(dob_str, "%Y-%m-%d")
            if dob > datetime.now():
                errors.append({"field": "date_of_birth", "message": "Date of birth cannot be in the future"})
            if dob < datetime(1900, 1, 1):
                errors.append({"field": "date_of_birth", "message": "Date of birth is too far in the past"})
        except (ValueError, TypeError):
            errors.append({"field": "date_of_birth", "message": "Invalid date format"})

    # sex
    sex = data.get("sex")
    if not sex:
        errors.append({"field": "sex", "message": "Sex is required"})
    elif sex not in ("Male", "Female", "Other", "Decline to Answer"):
        errors.append({"field": "sex", "message": "Sex must be Male, Female, Other, or Decline to Answer"})

    # phone_number
    phone = data.get("phone_number")
    if not phone:
        errors.append({"field": "phone_number", "message": "Phone number is required"})
    else:
        cleaned = re.sub(r'\D', '', phone)
        if len(cleaned) != 10:
            errors.append({"field": "phone_number", "message": "Phone number must be a valid 10-digit U.S. number"})

    # email (optional)
    email = data.get("email")
    if email and email.strip():
        if not re.match(r'^[^@\s]+@[^@\s]+\.[^@\s]+$', email.strip()):
            errors.append({"field": "email", "message": "Invalid email format"})

    # address_line_1
    addr = (data.get("address_line_1") or "").strip()
    if not addr:
        errors.append({"field": "address_line_1", "message": "Address line 1 is required"})

    # city
    city = (data.get("city") or "").strip()
    if not city:
        errors.append({"field": "city", "message": "City is required"})
    elif len(city) < 1 or len(city) > 100:
        errors.append({"field": "city", "message": "City must be 1-100 characters"})

    # state
    state = (data.get("state") or "").strip()
    if not state:
        errors.append({"field": "state", "message": "State is required"})
    elif len(state) != 2:
        errors.append({"field": "state", "message": "State must be a 2-letter abbreviation"})
    elif state.upper() not in US_STATES:
        errors.append({"field": "state", "message": "Invalid U.S. state abbreviation"})

    # zip_code
    zc = (data.get("zip_code") or "").strip()
    if not zc:
        errors.append({"field": "zip_code", "message": "ZIP code is required"})
    elif not re.match(r'^\d{5}(-\d{4})?$', zc):
        errors.append({"field": "zip_code", "message": "ZIP code must be 5-digit or ZIP+4 format"})

    # emergency_contact_phone (optional)
    ec_phone = data.get("emergency_contact_phone")
    if ec_phone and ec_phone.strip():
        cleaned = re.sub(r'\D', '', ec_phone)
        if len(cleaned) != 10:
            errors.append({"field": "emergency_contact_phone", "message": "Emergency contact phone must be a valid 10-digit U.S. number"})

    return errors


def validate_update_patient(patient_id, data):
    """Validate patient update data. Returns list of error dicts or empty list."""
    errors = []

    # patient_id must be valid UUID
    if not patient_id or not re.match(
        r'^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$',
        patient_id, re.IGNORECASE
    ):
        errors.append({"field": "id", "message": "Patient ID must be a valid UUID"})

    # first_name (optional)
    fn = data.get("first_name")
    if fn is not None:
        fn = fn.strip()
        if len(fn) < 1 or len(fn) > 50:
            errors.append({"field": "first_name", "message": "First name must be 1-50 characters"})
        elif not re.match(r"^[a-zA-Z\s'\-]+$", fn):
            errors.append({"field": "first_name", "message": "First name can only contain letters, hyphens, and apostrophes"})

    # last_name (optional)
    ln = data.get("last_name")
    if ln is not None:
        ln = ln.strip()
        if len(ln) < 1 or len(ln) > 50:
            errors.append({"field": "last_name", "message": "Last name must be 1-50 characters"})
        elif not re.match(r"^[a-zA-Z\s'\-]+$", ln):
            errors.append({"field": "last_name", "message": "Last name can only contain letters, hyphens, and apostrophes"})

    # date_of_birth (optional)
    dob_str = data.get("date_of_birth")
    if dob_str is not None:
        try:
            dob = datetime.fromisoformat(dob_str.replace("Z", "+00:00")) if "T" in dob_str else datetime.strptime(dob_str, "%Y-%m-%d")
            if dob > datetime.now():
                errors.append({"field": "date_of_birth", "message": "Date of birth cannot be in the future"})
        except (ValueError, TypeError):
            errors.append({"field": "date_of_birth", "message": "Invalid date format"})

    # sex (optional)
    sex = data.get("sex")
    if sex is not None and sex not in ("Male", "Female", "Other", "Decline to Answer"):
        errors.append({"field": "sex", "message": "Invalid sex value"})

    # phone_number (optional)
    phone = data.get("phone_number")
    if phone is not None:
        cleaned = re.sub(r'\D', '', phone)
        if len(cleaned) != 10:
            errors.append({"field": "phone_number", "message": "Phone number must be a valid 10-digit U.S. number"})

    # email (optional)
    email = data.get("email")
    if email and email.strip():
        if not re.match(r'^[^@\s]+@[^@\s]+\.[^@\s]+$', email.strip()):
            errors.append({"field": "email", "message": "Invalid email format"})

    # state (optional)
    state = data.get("state")
    if state is not None:
        if len(state) != 2:
            errors.append({"field": "state", "message": "State must be a 2-letter abbreviation"})
        elif state.upper() not in US_STATES:
            errors.append({"field": "state", "message": "Invalid U.S. state abbreviation"})

    # zip_code (optional)
    zc = data.get("zip_code")
    if zc is not None:
        if not re.match(r'^\d{5}(-\d{4})?$', zc.strip()):
            errors.append({"field": "zip_code", "message": "ZIP code must be 5-digit or ZIP+4 format"})

    return errors


def validate_patient_id(patient_id):
    """Validate that patient_id is a valid UUID."""
    if not patient_id or not re.match(
        r'^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$',
        patient_id, re.IGNORECASE
    ):
        return [{"field": "id", "message": "Patient ID must be a valid UUID"}]
    return []
