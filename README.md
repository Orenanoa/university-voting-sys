# IUIU Student Voting System

A Django web application for running student elections at the Islamic University in Uganda (IUIU).
Students are registered, candidates stand for positions, registered voters cast ballots, and results are counted automatically.

## Group Members

| No. | Name | Registration Number | Role |
|-----|------|---------------------|------|
| 1 | _Full name_ | _Reg. no._ | _e.g. Team leader_ |
| 2 | _Full name_ | _Reg. no._ | _e.g. Models and admin_ |
| 3 | _Full name_ | _Reg. no._ | _e.g. Templates_ |
| 4 | _Full name_ | _Reg. no._ | _e.g. Authentication_ |
| 5 | _Full name_ | _Reg. no._ | _e.g. Deployment_ |

## Live Project

Deployed on Render: _paste the link here after deploying_

## Login Details (for the lecturer)

- Admin site: `/admin/`
- Username: `admin`
- Password: `admin123`

## Features

- Models: Student, Election, Position, Candidate, Voter, Ballot
- Full CRUD (create, read, update, delete) for every model
- Authentication: login, logout, register
- Roles: only the admin (staff user) can create, update and delete records and start or end elections;
  normal users can view every page and cast ballots
  (set `STAFF_ONLY_EDITING = False` in `voting_system/settings.py` to give every logged-in user full CRUD)
- Ballot validation (election must be ongoing, one vote per position, approved candidates only)
- Results page, custom Django admin theme, JavaScript form validation with success alerts

## Run Locally

```
python -m venv venv
venv\Scripts\activate            (Windows)   |   source venv/bin/activate   (Mac/Linux)
pip install -r requirements.txt
python manage.py migrate
python manage.py create_default_admin      # creates admin / admin123
python manage.py load_dummy_data           # five rows of dummy data per model
python manage.py runserver
```

Run the tests with `python manage.py test`.

## Deploy on Render

1. Push this project to GitHub.
2. On render.com choose **New > Blueprint**, select the repository, and click **Apply** (it reads `render.yaml`).
   Or choose **New > Web Service** and set:
   - Build command: `./build.sh`
   - Start command: `python manage.py migrate && python manage.py create_default_admin && python manage.py load_dummy_data && gunicorn voting_system.wsgi:application`
   - Environment variables: `PYTHON_VERSION=3.12.8`, `DEBUG=False`, `SECRET_KEY=<any long random text>`
3. When the deploy finishes, open the `.onrender.com` link.

## Project Structure

- `elections/` models, forms, views, admin, tests and the `load_dummy_data` / `create_default_admin` commands
- `templates/` site pages and the custom admin template
- `static/` logo and admin CSS
