if we change attribute in database then delete the previous create new

Use from models import * when models.py is at the root or a top-level module.
Use from .models import * for importing a module in the same application or package directory (recommended within apps).
Use from application.models import * when you want to import from the models.py inside the application package that is at the project root level.


`url_for` is a Flask function that generates a URL for a specific route (view function).
Instead of hard-coding a URL path like `/login`, you use `url_for('login')`, which asks Flask to find the function named `login` and return its correct URL path.
Its main benefit is that if you change the route in your Python code (e.g., from `/login` to `/auth/login`), all your `url_for` links will update automatically, and none of your links will break.


<a href="{{ url_for('add_doctor', **auth_params) }}" class="btn btn-primary">Create</a>



ALTER TABLE medical_record ADD COLUMN visit_type VARCHAR(100);
ALTER TABLE medical_record ADD COLUMN test_done VARCHAR(255);

INSERT INTO appointment (reason, appt_date, status, patient_id, doctor_id) 
VALUES ('Follow-up', '2025-12-01 10:00:00', 'pending', 1, 1);

DELETE FROM appointment WHERE id = 1;


DELETE FROM appointment;
DELETE FROM sqlite_sequence WHERE name='appointment';


#Dtae : 16/01/2026
How to assigned patient to doctor


Install Flask-Migrate with pip install Flask-Migrate to enable Alembic-based database migrations for your Flask-SQLAlchemy app. This handles schema changes like adding the time_slot column without dropping tables.

