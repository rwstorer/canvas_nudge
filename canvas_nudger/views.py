from datetime import datetime
from django.shortcuts import render
from django.views.generic import FormView, TemplateView
from django.urls import reverse_lazy
from .workflow import get_last_week_range, build_weekly_status, generate_message
from .forms import StartForm, ConfirmCoursesForm, MessageTemplateForm
from . import canvas_client
from .defaults import load_defaults, get_message_templates, save_message_templates, update_defaults


class StartView(FormView):
    template_name = "canvas_nudger/start.html"
    form_class = StartForm
    success_url = reverse_lazy("courses_confirm")
          
    def get_initial(self):
        initial = super().get_initial()
        defaults = load_defaults()

        for key in ["canvas_api_url", "api_token", "course_ids_raw", "start_date", "end_date"]:
            if defaults.get(key):
                initial[key] = defaults[key]

        return initial
        

    def form_valid(self, form):
        cleaned = form.cleaned_data

        # Store in session
        self.request.session["api_token"] = cleaned["api_token"]
        self.request.session["course_ids"] = [ c.strip() for c in cleaned["course_ids_raw"].split(",") if c.strip() ]
        self.request.session["canvas_api_url"] = cleaned["canvas_api_url"]
        self.request.session["start_date"] = str(cleaned["start_date"])
        self.request.session["end_date"] = str(cleaned["end_date"])
        
        # save to json
        update_defaults({
            "canvas_api_url": cleaned["canvas_api_url"], 
            "api_token": cleaned["api_token"], 
            "course_ids_raw": cleaned["course_ids_raw"], 
            "start_date": str(cleaned["start_date"]), 
            "end_date": str(cleaned["end_date"]),
        })


        return super().form_valid(form)


class ConfirmCoursesView(FormView):
    template_name = "canvas_nudger/courses_confirm.html"
    form_class = ConfirmCoursesForm
    success_url = reverse_lazy("weekly_report") 
    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        token = self.request.session.get("api_token")
        course_ids = self.request.session.get("course_ids", [])
        base_url = self.request.session.get("canvas_api_url")
        # Fetch course metadata from Canvas
        courses = canvas_client.get_courses_by_ids(base_url, token, course_ids)
        # Store raw course data in session for later steps
        self.request.session["courses"] = courses
        # Build choices for the form
        choices = [ (str(c["id"]), f'{c["name"]} ({c["course_code"]})') for c in courses ] 
        kwargs["course_choices"] = choices
        return kwargs
    
    def form_valid(self, form):
        selected = form.cleaned_data["courses"] 
        self.request.session["selected_course_ids"] = selected
        return super().form_valid(form)


class WeeklyReportView(TemplateView):
    template_name = "canvas_nudger/weekly_report.html"

    def get(self, request, *args, **kwargs):
        token = request.session.get("api_token")
        selected_ids = request.session.get("selected_course_ids", [])
        courses = request.session.get("courses", [])
        base_url = self.request.session.get("canvas_api_url")

        # Filter only selected courses
        selected_courses = [c for c in courses if str(c["id"]) in selected_ids]

        start_raw = request.session.get("start_date")
        end_raw = request.session.get("end_date")
        if start_raw and end_raw:
            start = datetime.fromisoformat(start_raw)
            end = datetime.fromisoformat(end_raw)
        else:
            start, end = get_last_week_range()

        students_map = {}
        assignments_map = {}
        submissions_map = {}

        for course in selected_courses:
            cid = str(course["id"])

            # Fetch students
            students = canvas_client.get_students(base_url, cid, token)
            students_map[cid] = students

            # Fetch assignments due last week
            assignments_raw = canvas_client.get_assignments(base_url, cid, token)
            assignments = canvas_client.filter_assignments_by_date(assignments_raw, start, end)
            assignments_map[cid] = assignments

            # Fetch submissions for those assignments
            assignment_ids = [a["id"] for a in assignments]
            submissions = canvas_client.get_submissions(base_url, cid, assignment_ids, token)

            # Keep the raw dict: {assignment_id: [submissions]}
            submissions_map[cid] = submissions

        # Build the weekly report structure
        weekly_report = build_weekly_status(
            selected_courses,
            students_map,
            assignments_map,
            submissions_map,
        )

        # Store for next step
        request.session["weekly_report"] = weekly_report

        return self.render_to_response({"weekly_report": weekly_report})


class MessagePreviewView(TemplateView):
    template_name = "canvas_nudger/messages_preview.html"

    def post(self, request):
        weekly_report = request.session.get("weekly_report")
        selected_ids = request.POST.getlist("selected_student_ids")

        # selected_ids look like: ["courseid:studentid", ...]
        pending_messages = []

        for pair in selected_ids:
            course_id, student_id = pair.split(":")

            # Find course
            course = next(
                (c for c in weekly_report["courses"] if str(c["id"]) == course_id),
                None
            )
            if not course:
                continue

            # Find student
            student = next(
                (s for s in course["students"] if str(s["id"]) == student_id),
                None
            )
            if not student:
                continue

            # Generate message
            msg = generate_message(student)

            pending_messages.append({
                "course_id": course_id,
                "course_name": course["name"],
                "student_id": student_id,
                "student_name": student["name"],
                "message_type": msg["message_type"],
                "message_body": msg["message_body"],
            })

        # Store for Step 5
        request.session["pending_messages"] = pending_messages

        return render(request, self.template_name, {
            "messages": pending_messages
        })


class SendMessagesView(TemplateView):
    template_name = "canvas_nudger/messages_sent.html"

    def post(self, request):
        token = request.session.get("api_token")
        pending = request.session.get("pending_messages", [])
        base_url = self.request.session.get("canvas_api_url")

        sent_report = []

        # Collect edited messages from the form
        edited_messages = {}
        for key, value in request.POST.items():
            if key.startswith("message_"):
                # key format: message_courseid_studentid
                _, course_id, student_id = key.split("_", 2)
                edited_messages[f"{course_id}:{student_id}"] = value

        for msg in pending:
            key = f"{msg['course_id']}:{msg['student_id']}"
            body = edited_messages.get(key, msg["message_body"])

            # Canvas requires a subject — we can generate a simple one
            subject = (
                "Great work this week!"
                if msg["message_type"] == "congrats"
                else "A quick update on your assignments"
            )

            result = canvas_client.send_inbox_message(
                base_url=base_url,
                token=token,
                recipient_id=msg["student_id"],
                subject=subject,
                body=body,
            )

            sent_report.append({
                "course_name": msg["course_name"],
                "student_name": msg["student_name"],
                "message_body": body,
                "status": "sent" if result["success"] else "failed",
                "error": result.get("error"),
            })

        # Store for display
        request.session["sent_report"] = sent_report

        # Clear pending messages
        if "pending_messages" in request.session:
            del request.session["pending_messages"]

        return render(request, self.template_name, {
            "sent_report": sent_report
        })


class MessageTemplateView(FormView):
    template_name = "canvas_nudger/message_templates.html"
    form_class = MessageTemplateForm
    success_url = reverse_lazy("message_templates")

    def get_initial(self):
        templates = get_message_templates()
        return {
            "template_congrats": templates["congrats"],
            "template_encourage": templates["encourage"],
        }

    def form_valid(self, form):
        action = self.request.POST.get("action")

        if action == "preview":
            # Render preview page
            sample_data = {
                "name": "Sample Student",
                "missing_list": "- Assignment 1 (due 2024-01-10)\n- Assignment 2 (due 2024-01-12)"
            }

            preview_congrats = form.cleaned_data["template_congrats"].format(
                name=sample_data["name"]
            )
            preview_encourage = form.cleaned_data["template_encourage"].format(
                name=sample_data["name"],
                missing_list=sample_data["missing_list"]
            )

            return render(self.request, "canvas_nudger/template_preview.html", {
                "preview_congrats": preview_congrats,
                "preview_encourage": preview_encourage,
            })

        # Otherwise: save templates
        save_message_templates(
            form.cleaned_data["template_congrats"],
            form.cleaned_data["template_encourage"]
        )
        return super().form_valid(form)
