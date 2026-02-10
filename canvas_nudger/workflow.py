from datetime import datetime, timedelta
from pytz import utc
from .defaults import get_message_templates

def get_last_week_range():
    today = datetime.now()
    end = today
    start = today - timedelta(days=7)
    return start, end


def _is_assignment_expired(assignment):
    """Check if an assignment's lock_at date has passed."""
    lock_at = assignment.get("lock_at")
    if not lock_at:
        return False

    try:
        lock_dt = datetime.fromisoformat(lock_at.replace("Z", "+00:00"))
        # Ensure UTC timezone for comparison
        if lock_dt.tzinfo is None:
            lock_dt = utc.localize(lock_dt)
        now = datetime.now(utc)
        return now > lock_dt
    except (ValueError, TypeError):
        return False


def build_weekly_status(courses, students_map, assignments_map, submissions_map):
    """
    courses: list of course dicts
    students_map: {course_id: [students]}
    assignments_map: {course_id: [assignments]}
    submissions_map: {course_id: {assignment_id: [submissions]}}
    """

    report = {"courses": []}

    for course in courses:
        cid = str(course["id"])
        course_students = students_map[cid]
        course_assignments = assignments_map[cid]
        course_submissions = submissions_map[cid]

        student_statuses = []

        for student in course_students:
            sid = student["id"]

            completed = []
            missing = []
            expired = []

            for assignment in course_assignments:
                aid = str(assignment["id"])
                subs = course_submissions.get(aid, [])

                # Find this student's submission
                sub = next((s for s in subs if str(s.get("user_id")) == str(sid)), None)

                # Rule: submitted if:
                #   - submission exists with submitted_at present, OR
                #   - score > 0, OR
                #   - excused
                # Rule: missing if:
                #   - NOT any of the above

                has_submitted_at = sub and sub.get("submitted_at")
                score = sub.get("score") if sub else None
                excused = sub.get("excused", False) if sub else False

                is_submitted = (
                    has_submitted_at  # has submission with submitted_at
                    or (score is not None and score > 0)  # score > 0
                    or excused  # excused
                )

                if is_submitted:
                    completed.append(assignment)
                else:
                    # Not submitted. Check if assignment is expired.
                    if _is_assignment_expired(assignment):
                        expired.append(assignment)
                    else:
                        missing.append(assignment)

            student_statuses.append({
                "id": sid,
                "name": student.get("name"),
                "completed_all": len(missing) == 0,
                "completed_assignments": completed,
                "missing_assignments": missing,
                "expired_assignments": expired,
            })

        report["courses"].append({
            "id": cid,
            "name": course["name"],
            "students": student_statuses,
        })

    return report


def generate_message(student_status):
    templates = get_message_templates()
    name = student_status["name"]

    if student_status["completed_all"]:
        body = templates["congrats"].format(name=name)
        return {
            "message_type": "congrats",
            "message_body": body,
        }

    # Build missing list (explicitly exclude expired assignments)
    missing_lines = []
    expired_assignments = student_status.get("expired_assignments", [])
    expired_ids = {a.get("id") for a in expired_assignments}

    for a in student_status["missing_assignments"]:
        # Skip if this assignment is in the expired list
        if a.get("id") in expired_ids:
            continue

        due = a.get("due_at", "unknown due date")
        missing_lines.append(f"- {a['name']} (due {due})")

    missing_list = "\n".join(missing_lines)

    body = templates["encourage"].format(
        name=name,
        missing_list=missing_list
    )

    return {
        "message_type": "encourage",
        "message_body": body,
    }
