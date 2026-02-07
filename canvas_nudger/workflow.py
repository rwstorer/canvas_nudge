from datetime import datetime, timedelta
from .defaults import get_message_templates

def get_last_week_range():
    today = datetime.now()
    end = today
    start = today - timedelta(days=7)
    return start, end


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

            for assignment in course_assignments:
                aid = str(assignment["id"])
                subs = course_submissions.get(aid, [])

                # Find this student's submission
                sub = next((s for s in subs if s["user_id"] == sid), None)

                if sub and sub.get("submitted_at"):
                    completed.append(assignment)
                else:
                    missing.append(assignment)

            student_statuses.append({
                "id": sid,
                "name": student.get("name"),
                "completed_all": len(missing) == 0,
                "completed_assignments": completed,
                "missing_assignments": missing,
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

    # Build missing list
    missing_lines = []
    for a in student_status["missing_assignments"]:
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
