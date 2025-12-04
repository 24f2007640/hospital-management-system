from flask import render_template, request, redirect, url_for, current_app as app # Removed session, flash
from datetime import datetime, timedelta
from .models import db, User, Doctor, Patient, Appointment, MedicalRecord, Billing, DoctorAvailability
from werkzeug.exceptions import abort 



def get_auth_data(request):
    """Retrieves user_id and user_type from URL query parameters."""
    user_id = request.args.get('user_id', type=int)
    user_type = request.args.get('user_type')
    return user_id, user_type

def build_auth_params(user_id, user_type):
    """Builds a dictionary of URL parameters for authentication."""
    return {'user_id': user_id, 'user_type': user_type}

# -----------------------------------------------------------

@app.route('/')
def home():
    return redirect(url_for('login'))


@app.route('/login', methods=['GET', 'POST'])
def login():
    # session.clear() removed
    message = None
    if request.method == 'POST':
        username = request.form.get("username") 
        pwd = request.form.get('pwd')   

        this_user = User.query.filter_by(username=username).first()

        if this_user and this_user.password == pwd:
            
            # STATELESS AUTH SETUP
            auth_params = build_auth_params(this_user.id, this_user.type)
            
            if this_user.type == "manager":
                # Passing auth data via URL
                return redirect(url_for('manager_dashboard', **auth_params))
            elif this_user.type == "doctor":
                # Passing doctor_id and auth data via URL
                return redirect(url_for('doctor_dashboard', doctor_id=this_user.doctor_profile.id, **auth_params))
            elif this_user.type == "patient":
                # Passing auth data via URL
                return redirect(url_for('patient_dashboard', **auth_params))
        else:
            message = "Invalid username or password"

    return render_template("login.html", message=message)

@app.route('/logout')
def logout():
    # session.clear() removed
    # Simply redirects to login, no state management needed
    return redirect(url_for('login'))

@app.route('/register', methods=['GET', 'POST'])
def register():
    message = None
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password') 
        name = request.form.get('name')
        username_exists = User.query.filter_by(username=username).first()

        if username_exists:
            message = "Username already taken"
            return render_template("register.html", message=message)
        else:
            new_user = User(
                username=username,
                password=password, 
                email=request.form.get('email'),
                type='patient'
            )
            new_patient = Patient(
                name=name,
                phone=request.form.get('phone'),
                address=request.form.get('city'),
                user=new_user
            )
            db.session.add(new_user)
            db.session.add(new_patient)
            db.session.commit()
            return redirect(url_for('login'))

    return render_template("register.html", message=message)



#---------------------------------------------Manager------------------------------------------------

#coreect and running
@app.route('/manager/dashboard')
def manager_dashboard():
    user_id, user_type = get_auth_data(request)

    # AUTHENTICATION CHECK REPLACEMENT
    if user_type != 'manager' or not user_id:
        return redirect(url_for('login'))

    auth_params = build_auth_params(user_id, user_type)
    manager_user = User.query.get(user_id)
    
    doctors_list = Doctor.query.all()
    patients_list = Patient.query.all()
    appointments_list = Appointment.query.all()
    return render_template(
        "Adm_Admin-Welcome.html",
        manager_name=manager_user.username if manager_user else 'Manager',
        doctors=doctors_list,
        patients=patients_list,
        appointments=appointments_list,
        auth_params=auth_params # Passed to templates for link generation
    )

#coreect and running
@app.route('/manager/add_doctor', methods=['GET', 'POST'])
def add_doctor():
    user_id, user_type = get_auth_data(request)
    if user_type != 'manager' or not user_id:
        return redirect(url_for('login'))

    auth_params = build_auth_params(user_id, user_type)

    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        name = request.form.get('name')

        if User.query.filter_by(username=username).first():
            return render_template("Adm_Add-New-Doctor.html", message="Username already exists", auth_params=auth_params)

        new_user = User(
            username=username,
            password=password,
            email=request.form.get('email'),
            type='doctor'
        )
        new_doctor = Doctor(
            name=name,
            specialty=request.form.get('specialty'),
            phone=request.form.get('phone'),
            user=new_user
        )

        db.session.add(new_user)
        db.session.add(new_doctor)
        db.session.commit()

        # Redirect with auth params
        return redirect(url_for('manager_dashboard', **auth_params))

    return render_template("Adm_Add-New-Doctor.html", auth_params=auth_params)

#correct and running
@app.route('/doctor/delete/<int:doctor_id>')
def delete_doctor(doctor_id):
    user_id, user_type = get_auth_data(request)
    if user_type != 'manager' or not user_id:
        return redirect(url_for('login'))
    
    auth_params = build_auth_params(user_id, user_type)
    
    doctor = Doctor.query.get(doctor_id)
    if doctor:
        Appointment.query.filter_by(doctor_id=doctor.id).delete()
        MedicalRecord.query.filter_by(doctor_id=doctor.id).delete()
        db.session.delete(doctor)
        User.query.filter_by(id=doctor.user_id).delete()
        db.session.commit()
    # Redirect with auth params
    return redirect(url_for('manager_dashboard', **auth_params))

#correct and running
@app.route('/patient/delete/<int:patient_id>')
def delete_patient(patient_id):
    user_id, user_type = get_auth_data(request)
    if user_type != 'manager' or not user_id:
        return redirect(url_for('login'))
    
    auth_params = build_auth_params(user_id, user_type)

    patient = Patient.query.get(patient_id)
    if patient:
        Appointment.query.filter_by(patient_id=patient.id).delete()
        MedicalRecord.query.filter_by(patient_id=patient.id).delete()
        Billing.query.filter_by(patient_id=patient.id).delete()
        db.session.delete(patient)
        if patient.user_id:
            User.query.filter_by(id=patient.user_id).delete()
        db.session.commit()
    # Redirect with auth params
    return redirect(url_for('manager_dashboard', **auth_params))


#correct and running
@app.route('/patient/edit_profile', methods=['GET', 'POST'])
def edit_patient_profile():
    user_id, user_type = get_auth_data(request)
    if user_type != 'manager' or not user_id:
        return redirect(url_for('login'))
    
    # Get patient_id from query params to identify which patient to edit
    patient_id = request.args.get('patient_id')
    if not patient_id:
        return "Patient ID not provided", 400

    auth_params = build_auth_params(user_id, user_type)
    # Fetch patient by patient_id (assuming patient_id matches Patient.id or some unique id)
    patient = Patient.query.filter_by(id=patient_id).first()
    
    if not patient:
        return redirect(url_for('manager_dashboard'))  # or another manager page

    if request.method == 'POST':
        patient.name = request.form.get('name')
        patient.phone = request.form.get('phone')
        patient.address = request.form.get('city')
        if patient.user:
            patient.user.email = request.form.get('email')
        db.session.commit()
        return redirect(url_for('manager_dashboard', **auth_params))
    
    return render_template('Adm_Patient-profile.html', patient=patient, auth_params=auth_params)

@app.route('/doctor/edit_profile', methods=['GET', 'POST'])
def edit_doctor_profile():
    user_id, user_type = get_auth_data(request)
    if user_type != 'manager' or not user_id:
        return redirect(url_for('login'))
    
    doctor_id = request.args.get('doctor_id')
    if not doctor_id:
        return "Doctor ID not provided", 400

    auth_params = build_auth_params(user_id, user_type)
    doctor = Doctor.query.filter_by(id=doctor_id).first()

    if not doctor:
        return redirect(url_for('manager_dashboard'))

    if request.method == 'POST':
        doctor.name = request.form.get('name')
        doctor.specialty = request.form.get('specialty')
        doctor.phone = request.form.get('phone')
        if doctor.user:
            doctor.user.email = request.form.get('email')
        db.session.commit()
        
        return redirect(url_for('manager_dashboard', **auth_params))
    
    return render_template('Adm_Doctor-profile.html', doctor=doctor, auth_params=auth_params)






#----------------------------------------------Doctor------------------------------------------

#correct and running
@app.route('/doctor/dashboard/<int:doctor_id>')
def doctor_dashboard(doctor_id):
    user_id, user_type = get_auth_data(request)
    if user_type != 'doctor' or not user_id: 
         return redirect(url_for('login'))

    auth_params = build_auth_params(user_id, user_type)
    doctor = Doctor.query.get_or_404(doctor_id)
    
    appointments = Appointment.query.filter_by(doctor_id=doctor.id, status='pending') \
                    .order_by(Appointment.appt_date.asc()).all()
    
    patients = Patient.query.join(Appointment).filter(Appointment.doctor_id == doctor.id).distinct().all()

    return render_template('Doc_Welcome-doc.html', doctor=doctor, appointments=appointments, patients=patients, auth_params=auth_params)

#correct and running
@app.route('/doctor/availability/<int:doctor_id>', methods=['GET', 'POST'])
def doctor_availability(doctor_id):
    if request.method == 'POST':
        user_id = request.form.get('user_id')
        user_type = request.form.get('user_type')
    else:
        user_id, user_type = get_auth_data(request)
        
    if user_type != 'doctor' or not user_id:
        return redirect(url_for('login'))

    auth_params = build_auth_params(user_id, user_type)
    doctor = Doctor.query.get_or_404(doctor_id)

    today = datetime.today().date()
    possible_dates = [today + timedelta(days=i) for i in range(7)]
    possible_slots = ["08:00 - 12:00 am", "04:00 - 9:00 pm"]

    if request.method == 'POST':
        DoctorAvailability.query.filter(
            DoctorAvailability.doctor_id == doctor.id,
            DoctorAvailability.date.in_(possible_dates)
        ).delete(synchronize_session=False)
        selected = request.form.getlist('availabilities')
        for sel in selected:
            date_str, slot = sel.split('|')
            date = datetime.strptime(date_str, '%Y-%m-%d').date()
            new_avail = DoctorAvailability(date=date, time_slot=slot, doctor_id=doctor.id)
            db.session.add(new_avail)
        db.session.commit()
        return redirect(url_for('doctor_availability', doctor_id=doctor_id, **auth_params))

    availabilities = DoctorAvailability.query.filter_by(doctor_id=doctor.id).all()
    avail_map = {(a.date, a.time_slot) for a in availabilities}
    date_slots = []
    for dt in possible_dates:
        selected = [slot for slot in possible_slots if (dt, slot) in avail_map]
        date_slots.append({'date': dt, 'slots': possible_slots, 'selected': selected})

    return render_template('doc_docs-avail-Doc.html', doctor=doctor, date_slots=date_slots, auth_params=auth_params)


#correct and running not tested for upcoming appointment
@app.route('/doctor/update_history/<int:doctor_id>/<int:patient_id>', methods=['GET', 'POST'])
def update_patient_history(doctor_id, patient_id):
    user_id, user_type = get_auth_data(request)
    if user_type != 'doctor' or not user_id: 
        return redirect(url_for('login'))
        
    auth_params = build_auth_params(user_id, user_type)
    patient = Patient.query.get_or_404(patient_id)
    doctor = Doctor.query.get_or_404(doctor_id)

    record = MedicalRecord.query.filter_by(patient_id=patient.id, doctor_id=doctor.id).order_by(MedicalRecord.id.desc()).first()

    if request.method == 'POST':
        visit_type = request.form.get('visit_type')
        test_done = request.form.get('test_done')
        diagnosis = request.form.get('diagnosis')
        treatment = request.form.get('medicines')
        notes = request.form.get('prescription')

        if record:
            record.visit_type = visit_type
            record.test_done = test_done
            record.diagnosis = diagnosis
            record.treatment = treatment
            record.notes = notes
        else:
            record = MedicalRecord(
                visit_type=visit_type,
                test_done=test_done,
                diagnosis=diagnosis,
                treatment=treatment,
                notes=notes,
                patient_id=patient.id,
                doctor_id=doctor.id
            )
            db.session.add(record)
        db.session.commit()
        return redirect(url_for('doctor_dashboard', doctor_id=doctor_id, **auth_params))
    return render_template('Doc_Update-Pat-Hist.html', patient=patient, doctor=doctor, auth_params=auth_params, record=record)


@app.route('/doctor/appointment/complete/<int:appt_id>')
def complete_appointment(appt_id):
    user_id, user_type = get_auth_data(request)
    if user_type != 'doctor' or not user_id: 
         return redirect(url_for('login'))

    auth_params = build_auth_params(user_id, user_type)
    
    appointment = Appointment.query.get_or_404(appt_id)
    appointment.status = 'completed'
    db.session.commit()
    # Redirect with auth params
    return redirect(url_for('doctor_dashboard', doctor_id=appointment.doctor_id, **auth_params))

@app.route('/doctor/appointment/cancel/<int:appt_id>')
def cancel_appointment(appt_id):
    user_id, user_type = get_auth_data(request)
    if user_type != 'doctor' or not user_id: 
         return redirect(url_for('login'))

    auth_params = build_auth_params(user_id, user_type)
    
    appointment = Appointment.query.get_or_404(appt_id)
    appointment.status = 'cancelled'
    db.session.commit()
    # Redirect with auth params
    return redirect(url_for('doctor_dashboard', doctor_id=appointment.doctor_id, **auth_params))



#------------------------------------------------------Patient--------------------------------------

@app.route('/patient/dashboard')
def patient_dashboard():
    user_id, user_type = get_auth_data(request)
    if user_type != 'patient' or not user_id: 
        return redirect(url_for('login'))
        
    auth_params = build_auth_params(user_id, user_type)
    
    patient = Patient.query.get(user_id)
    if not patient:
        return redirect(url_for('login'))

    
    departments = ["Cardiology", "Oncology", "General"]

    
    appointments = Appointment.query \
        .filter_by(patient_id=patient.id, status="pending") \
        .join(Doctor) \
        .order_by(Appointment.appt_date.asc()) \
        .all()

    return render_template('pat_welcome.html',
                           patient=patient,
                           departments=departments,
                           appointments=appointments,
                           auth_params=auth_params)


@app.route('/patient/history/<int:patient_id>/<int:doctor_id>')
def patient_history(patient_id, doctor_id):
    # This route is usually accessed from a protected dashboard and does not need
    # to maintain auth state itself if it's a child route.
    patient = Patient.query.get_or_404(patient_id)
    doctor = Doctor.query.get_or_404(doctor_id)
    records = MedicalRecord.query.filter_by(patient_id=patient_id, doctor_id=doctor_id).all()

    return render_template('pat_history.html', patient=patient, doctor=doctor, records=records)

@app.route('/doctor/details/<int:doctor_id>')
def doctor_details(doctor_id):
    doctor = Doctor.query.get_or_404(doctor_id)
    return render_template('doc_details.html', doctor=doctor)



@app.route('/patient/doctor/availability/<int:doctor_id>', methods=['GET', 'POST'])
def doctor_available(doctor_id): # ROUTE NAME KEPT: doctor_availability
    doctor = Doctor.query.get_or_404(doctor_id)
    today = datetime.today().date()
    possible_dates = [today + timedelta(days=i) for i in range(7)]
    possible_slots = ["08:00 - 12:00 am", "04:00 - 9:00 pm"]

    if request.method == 'POST':
        try:
            # NOTE: This POST logic seems to be for the doctor setting availability, not a patient
            # booking. Given the request, I've left the logic, but removed flash/session.
            
            DoctorAvailability.query.filter(
                DoctorAvailability.doctor_id == doctor.id,
                DoctorAvailability.date.in_(possible_dates)
            ).delete(synchronize_session=False)

            selected = request.form.getlist('availabilities')
            for sel in selected:
                date_str, slot = sel.split('|')
                date = datetime.strptime(date_str, '%Y-%m-%d').date()
                new_avail = DoctorAvailability(date=date, time_slot=slot, doctor_id=doctor.id)
                db.session.add(new_avail)

            db.session.commit()
            
        except Exception as e:
            db.session.rollback()

        # NOTE: This redirects to itself without auth params, meaning no state is preserved
        return redirect(url_for('doctor_availability', doctor_id=doctor_id))

    availabilities = DoctorAvailability.query.filter_by(doctor_id=doctor.id).all()
    avail_map = {(a.date, a.time_slot) for a in availabilities}
    date_slots = []
    for dt in possible_dates:
        selected = [slot for slot in possible_slots if (dt, slot) in avail_map]
        date_slots.append({'date': dt, 'slots': possible_slots, 'selected': selected})

    return render_template('doc_availability.html', doctor=doctor, date_slots=date_slots)





@app.route('/department/oncology')
def oncology_department():
    doctors = Doctor.query.filter_by(specialty='Oncology').all()

    return render_template(
        'pat_dept_pverview.html',
        department_title='Department of Oncology',
        department_name='Department of Oncology',
        overview_text='The Oncology Department in a hospital is dedicated to the diagnosis, treatment, and care of patients with cancer. It houses a team of specialized doctors, such as medical oncologists, surgical oncologists, and radiation oncologists, who work together to provide comprehensive cancer care.',
        doctors=doctors
    )


@app.route('/check_availability/<int:doctor_id>')
def check_availability(doctor_id):
    doctor = Doctor.query.get(doctor_id)
    if not doctor:
        abort(404, description="Doctor not found")

    availabilities = DoctorAvailability.query.filter_by(doctor_id=doctor_id).order_by(DoctorAvailability.date).all()

    return render_template(
        'check_availability.html',
        doctor=doctor,
        availabilities=availabilities
    )



@app.route('/view_doctor_details/<int:doctor_id>')
def view_doctor_details(doctor_id):
    doctor = Doctor.query.get(doctor_id)
    if not doctor:
        abort(404, description="Doctor not found")

    return render_template(
        'view_doctor_details.html',
        doctor=doctor
    )

# @app.route('/patient/edit_profile', methods=['GET', 'POST'])
# def edit_patient_profile():
#     user_id, user_type = get_auth_data(request)
#     if user_type != 'patient' or not user_id:
#         return redirect(url_for('login'))
    
#     auth_params = build_auth_params(user_id, user_type)
#     patient = Patient.query.filter_by(user_id=user_id).first() # Fetch patient using user_id
    
#     if not patient:
#         return redirect(url_for('login')) 

#     if request.method == 'POST':
#         patient.name = request.form.get('name')
#         patient.phone = request.form.get('phone')
#         patient.address = request.form.get('city')
#         if patient.user:
#             patient.user.email = request.form.get('email')
#         db.session.commit()
#         # Redirect with auth params
#         return redirect(url_for('patient_dashboard', **auth_params))
        
#     return render_template('Adm_Patient-profile.html', patient=patient, auth_params=auth_params)