# canvas_nudge

Give a little nudge to students to complete assignments using Canvas inbox messages.

## **Structure**

- **`canvas_nudger/`**: Django app that implements the nudging UI and Canvas API integration.
  - [canvas_nudger/canvas_client.py](canvas_nudger/canvas_client.py): helpers for calling the Canvas API (courses, students, assignments, submissions, and sending messages).
  - [canvas_nudger/workflow.py](canvas_nudger/workflow.py): report generation and message generation logic.
  - [canvas_nudger/defaults.py](canvas_nudger/defaults.py) & [canvas_nudger/defaults.sample.json](canvas_nudger/defaults.sample.json): configuration storage and sample defaults.
  - [canvas_nudger/views.py](canvas_nudger/views.py): Django views backing the web flow (start, confirm courses, weekly report, preview, send, templates).
  - [canvas_nudger/templates/canvas_nudger/](canvas_nudger/templates/canvas_nudger/): HTML templates used by the app.
- **`nudger/`**: Django project scaffolding and settings ([nudger/settings.py](nudger/settings.py)).
- `manage.py`: Django CLI.
- `requirements.txt`: Python dependencies.
- [tree](#tree)

## **Purpose**

This small Django app queries a Canvas LMS instance for courses, assignments, and submissions, builds a weekly status report for students, generates personalized messages (congratulatory or encouraging), lets an instructor preview and edit messages, then sends them to students via Canvas Conversations (inbox).

## **Quickstart / Usage**

Prerequisites: Python 3.10+ (a virtualenv is recommended).

1. Install dependencies:
    - `pip install -r requirements.txt`

2. Configure defaults:
    - Create the folder `canvas_nudger/.env` and copy `canvas_nudger/defaults.sample.json` → `canvas_nudger/.env/defaults.json`.
    - Edit `canvas_nudger/.env/defaults.json` and set at minimum `canvas_api_url` and `api_token`. Optionally set `course_ids_raw`, `start_date`, and `end_date`.

3. Migrate and run the server:
    - `python manage.py migrate`
    - `python manage.py runserver`

4. Web UI flow (open http://localhost:8000/):
    - Start: provide Canvas API URL and API token, and optionally a comma-separated list of course IDs and date range.
    - Confirm courses: verify which courses to include.
    - Weekly report: the app fetches students, filters assignments by the date range, and builds a per-student status report.
    - Preview messages: select students, preview auto-generated messages, optionally edit them.
    - Send messages: messages are sent using the Canvas Conversations API.

## **Configuration / Templates**

- Message templates live in `canvas_nudger/.env/defaults.json` as `template_congrats` and `template_encourage`.
- Use the UI (Message Templates page) to preview and save templates; the app persists them to the same defaults file.

## **Development & Testing**
- Run unit tests (if any): `python manage.py test`.
- The project uses a local SQLite DB by default (`db.sqlite3`).

## **Notes & Security**

- The `api_token` is a Canvas API token—keep it secret. Storing it in `canvas_nudger/.env/defaults.json` is convenient for local testing but not suitable for production.
- This project is intended as a lightweight instructor tool and assumes the API token has sufficient Canvas permissions to read courses/users/assignments and send conversations.

## Tree

|   .gitignore
|   db.sqlite3
|   LICENSE
|   manage.py
|   README.md
|   requirements.txt
|
+---canvas_nudger
|   |   admin.py
|   |   apps.py
|   |   canvas_client.py
|   |   defaults.py
|   |   defaults.sample.json
|   |   forms.py
|   |   models.py
|   |   tests.py
|   |   urls.py
|   |   views.py
|   |   workflow.py
|   |   __init__.py
|   |
|   +---.env
|   |       defaults.json
|   |
|   +---migrations
|   |       __init__.py
|   |
|   |
|   +---templates
|   |   \---canvas_nudger
|   |           courses_confirm.html
|   |           messages_preview.html
|   |           messages_sent.html
|   |           message_templates.html
|   |           start.html
|   |           template_preview.html
|   |           weekly_report.html
|   |
|   +---templatetags
|          dict_extras.py
|          init__.py
|
|
+---nudger
        asgi.py
        settings.py
        urls.py
        wsgi.py
        __init__.py
