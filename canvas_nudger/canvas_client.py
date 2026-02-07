from datetime import datetime
from pytz import utc
import requests

# Simple API cache to reduce duplicate calls
_api_cache = {}

def has_timezone(date_obj):
    return date_obj.tzinfo is not None and date_obj.tzinfo.utcoffset(date_obj) is not None

def _headers(token):
    return {"Authorization": f"Bearer {token}"}

def cached_get(url, headers, params=None):
    key = (url, tuple(sorted((params or {}).items())))
    if key in _api_cache:
        return _api_cache[key]

    resp = requests.get(url, headers=headers, params=params)
    resp.raise_for_status()
    data = resp.json()
    _api_cache[key] = data
    return data

# ------------------------------------------------------------
# Courses
# ------------------------------------------------------------
def get_courses_by_ids(base_url, token, course_ids):
    headers = _headers(token)
    courses = []

    for cid in course_ids:
        url = f"{base_url}/courses/{cid}"
        resp = requests.get(url, headers=headers)

        if resp.status_code == 200:
            data = resp.json()
            courses.append({
                "id": data.get("id"),
                "name": data.get("name"),
                "course_code": data.get("course_code"),
                "term": data.get("term", {}).get("name"),
            })
        else:
            courses.append({
                "id": cid,
                "name": f"(Error fetching course {cid})",
                "course_code": "N/A",
                "term": None,
                "error": True,
            })

    return courses

# ------------------------------------------------------------
# Students
# ------------------------------------------------------------
def get_students(base_url, course_id, token):
    url = f"{base_url}/courses/{course_id}/users"
    params = {
        "enrollment_type[]": "student",
        "per_page": 100,
    }
    return cached_get(url, _headers(token), params)

# ------------------------------------------------------------
# Assignments (course-level, no submissions)
# ------------------------------------------------------------
def get_assignments(base_url, course_id, token):
    url = f"{base_url}/courses/{course_id}/assignments"
    params = {"per_page": 100}
    resp = requests.get(url, headers=_headers(token), params=params)
    resp.raise_for_status()
    return resp.json()


# ------------------------------------------------------------
# Submissions (assignment-level)
# ------------------------------------------------------------
def get_submissions(base_url, course_id, assignment_ids, token):
    submissions = {}

    for aid in assignment_ids:
        url = f"{base_url}/courses/{course_id}/assignments/{aid}/submissions"
        params = {"per_page": 100}
        resp = requests.get(url, headers=_headers(token), params=params)
        resp.raise_for_status()
        submissions[str(aid)] = resp.json()

    return submissions

# ------------------------------------------------------------
# Merge assignments + submissions
# ------------------------------------------------------------
def merge_assignments_and_submissions(assignments, submissions):
    merged = []

    for a in assignments:
        aid = str(a["id"])
        a["submission"] = submissions.get(aid)
        merged.append(a)

    return merged

# ------------------------------------------------------------
# Course metadata
# ------------------------------------------------------------
def get_course(base_url, course_id, token):
    url = f"{base_url}/courses/{course_id}"
    return cached_get(url, _headers(token))

# ------------------------------------------------------------
# Send Canvas Inbox message
# ------------------------------------------------------------
def send_inbox_message(base_url, token, recipient_id, subject, body):
    url = f"{base_url}/conversations"
    payload = {
        "recipients[]": [recipient_id],
        "subject": subject,
        "body": body,
        "force_new": True,
    }

    resp = requests.post(url, headers=_headers(token), data=payload)

    if resp.status_code in (200, 201):
        return {"success": True, "data": resp.json()}

    return {
        "success": False,
        "error": f"{resp.status_code}: {resp.text}",
    }
    
    
def filter_assignments_by_date(assignments, start_date, end_date):
    filtered = []
    for a in assignments:
        due_at = a.get("due_at")
        if not due_at:
            continue

        due = datetime.fromisoformat(due_at.replace("Z", "+00:00"))

        if not has_timezone(start_date):
            start_date = utc.localize(start_date)
        if not has_timezone(end_date):
            end_date = utc.localize(end_date)
        if not has_timezone(due):
            due = utc.localize(due)

        if start_date <= due <= end_date:
            filtered.append(a)

    return filtered