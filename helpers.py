import datetime
from flask import session

def is_logged_in():
    return bool(session.get('loggedin'))

def parse_iso_date(date_str):
    try:
        return datetime.datetime.strptime(date_str, "%Y-%m-%d").date()
    except (TypeError, ValueError):
        return None

def allowed_file(filename):
    ALLOWED_EXTENSIONS = {'jpg', 'jpeg', 'png', 'webp'}
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def build_range_conditions(range_type, table_alias=None, from_date=None, to_date=None):
    col = "created_at" if not table_alias else f"{table_alias}.created_at"
    if range_type == "all":    return "1=1", []
    if range_type == "today":  return f"DATE({col}) = CURDATE()", []
    if range_type == "7d":     return f"{col} >= DATE_SUB(CURDATE(), INTERVAL 7 DAY)", []
    if range_type == "30d":    return f"{col} >= DATE_SUB(CURDATE(), INTERVAL 30 DAY)", []
    if range_type == "custom": return f"DATE({col}) BETWEEN %s AND %s", [from_date, to_date]
    return "1=1", []