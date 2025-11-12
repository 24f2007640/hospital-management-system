from flask import render_template, request, redirect, url_for, flash, session
from flask import current_app as app
from datetime import datetime, timedelta
from .models import db, User, Doctor, Patient, Appointment, MedicalRecord, Billing, DoctorAvailability



@app.route('/')
def home():
    return redirect(url_for('login'))

@app.route('/login', methods=['GET', 'POST'])
def login():
    session.clear() 
    message = None
    if request.method == 'POST':
        username = request.form.get("username") 
        pwd = request.form.get('pwd')   

        this_user = User.query.filter_by(username=username).first()

        if this_user and this_user.password == pwd:
            session['user_id'] = this_user.id
            session['username'] = this_user.username
            session['user_type'] = this_user.type

            if this_user.type == "manager":
                return redirect(url_for('manager_dashboard'))
            elif this_user.type == "doctor":
                return redirect(url_for('doctor_dashboard'))
            elif this_user.type == "patient":
                return redirect(url_for('patient_dashboard'))
        else:
            message = "Invalid username or password"

    return render_template("login.html", message=message)

@app.route('/logout')
def logout():
    session.clear()
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



#---------------------------------------------Admin------------------------------------------------


@app.route('/manager/dashboard')
def manager_dashboard():
    if session.get('user_type') != 'manager':
        return redirect(url_for('login'))
    doctors_list = Doctor.query.all()
    patients_list = Patient.query.all()
    appointments_list = Appointment.query.all()
    return render_template(
        "Adm_Admin-Welcome.html",
        manager_name=session.get('username', 'Manager'),
        doctors=doctors_list,
        patients=patients_list,
        appointments=appointments_list
    )

@app.route('/manager/add_doctor', methods=['GET', 'POST'])
def add_doctor():
    if session.get('user_type') != 'manager':
        return redirect(url_for('login'))

    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        name = request.form.get('name')

        
        if User.query.filter_by(username=username).first():
            return render_template("Adm_Add-New-Doctor.html", message="Username already exists")

    
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

        return redirect(url_for('manager_dashboard'))

    return render_template("Adm_Add-New-Doctor.html")


@app.route('/doctor/delete/<int:doctor_id>')
def delete_doctor(doctor_id):
    if session.get('user_type') != 'manager':
        return redirect(url_for('login'))
    doctor = Doctor.query.get(doctor_id)
    if doctor:
        Appointment.query.filter_by(doctor_id=doctor.id).delete()
        MedicalRecord.query.filter_by(doctor_id=doctor.id).delete()
        db.session.delete(doctor)
        User.query.filter_by(id=doctor.user_id).delete()
        db.session.commit()
    return redirect(url_for('manager_dashboard'))

@app.route('/patient/delete/<int:patient_id>')
def delete_patient(patient_id):
    if session.get('user_type') != 'manager':
        return redirect(url_for('login'))
    patient = Patient.query.get(patient_id)
    if patient:
        Appointment.query.filter_by(patient_id=patient.id).delete()
        MedicalRecord.query.filter_by(patient_id=patient.id).delete()
        Billing.query.filter_by(patient_id=patient.id).delete()
        db.session.delete(patient)
        if patient.user_id:
            User.query.filter_by(id=patient.user_id).delete()
        db.session.commit()
    return redirect(url_for('manager_dashboard'))

@app.route('/patient/edit_profile', methods=['GET', 'POST'])
def edit_patient_profile():
    patient = Patient.query.filter_by(user_id=session['user_id']).first()
    if request.method == 'POST':
        patient.name = request.form.get('name')
        patient.phone = request.form.get('phone')
        patient.address = request.form.get('city')
        if patient.user:
            patient.user.email = request.form.get('email')
        db.session.commit()
        return redirect(url_for('patient_dashboard'))
    return render_template('Adm_Patient-profile.html', patient=patient)


@app.route('/doctor/edit_profile', methods=['GET', 'POST'])
def edit_doctor_profile():
    doctor = Doctor.query.filter_by(user_id=session['user_id']).first()
    if request.method == 'POST':
        doctor.name = request.form.get('name')
        doctor.specialty = request.form.get('specialty')
        doctor.phone = request.form.get('phone')
        if doctor.user:
            doctor.user.email = request.form.get('email')
        db.session.commit()
        return redirect(url_for('doctor_dashboard', doctor_id=doctor.id))
    return render_template('Adm_Doctor-profile.html', doctor=doctor)





#----------------------------------------------Doctor------------------------------------------


@app.route('/doctor/dashboard/<int:doctor_id>')
def doctor_dashboard(doctor_id):
    doctor = Doctor.query.get_or_404(doctor_id)
    appointments = Appointment.query.filter_by(doctor_id=doctor.id, status='pending').all()
    patients = Patient.query.join(Appointment).filter(Appointment.doctor_id == doctor.id).distinct().all()
    return render_template('Doc_Welcome-doc.html', doctor=doctor, appointments=appointments, patients=patients)


@app.route('/doctor/availability/<int:doctor_id>', methods=['GET', 'POST'])
def doctor_availability(doctor_id):
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
        return redirect(url_for('doctor_availability', doctor_id=doctor_id))

    availabilities = DoctorAvailability.query.filter_by(doctor_id=doctor.id).all()
    avail_map = {(a.date, a.time_slot) for a in availabilities}
    date_slots = []
    for dt in possible_dates:
        selected = [slot for slot in possible_slots if (dt, slot) in avail_map]
        date_slots.append({'date': dt, 'slots': possible_slots, 'selected': selected})
    return render_template('doc_docs-avail-Doc.html', doctor=doctor, date_slots=date_slots)


@app.route('/doctor/update_history/<int:doctor_id>/<int:patient_id>', methods=['GET', 'POST'])
def update_patient_history(doctor_id, patient_id):
    patient = Patient.query.get_or_404(patient_id)
    doctor = Doctor.query.get_or_404(doctor_id)
    if request.method == 'POST':
        diagnosis = request.form.get('diagnosis')
        treatment = request.form.get('medicines')
        notes = request.form.get('prescription')
        record = MedicalRecord(
            diagnosis=diagnosis,treatment=treatment,notes=notes,patient_id=patient.id,doctor_id=doctor.id)
        db.session.add(record)
        db.session.commit()
        flash('Patient history updated.')
        return redirect(url_for('doctor_dashboard', doctor_id=doctor_id))
    return render_template('Doc_Update-Pat-Hist.html', patient=patient, doctor=doctor)

@app.route('/doctor/appointment/complete/<int:appt_id>')
def complete_appointment(appt_id):
    appointment = Appointment.query.get_or_404(appt_id)
    appointment.status = 'completed'
    db.session.commit()
    flash('Appointment marked as completed.')
    return redirect(url_for('doctor_dashboard', doctor_id=appointment.doctor_id))

@app.route('/doctor/appointment/cancel/<int:appt_id>')
def cancel_appointment(appt_id):
    appointment = Appointment.query.get_or_404(appt_id)
    appointment.status = 'cancelled'
    db.session.commit()
    flash('Appointment cancelled.')
    return redirect(url_for('doctor_dashboard', doctor_id=appointment.doctor_id))



#------------------------------------------------------Patient--------------------------------------

@app.route('/patient/dashboard')
def patient_dashboard():
    patient = Patient.query.filter_by(user_id=session['user_id']).first()
    departments = ["Cardiology", "Oncology", "General"]  
    appointments = Appointment.query.filter_by(patient_id=patient.id).join(Doctor).all()
    return render_template('pat_welcome.html', patient=patient, departments=departments, appointments=appointments)

@app.route('/patient/history/<int:patient_id>/<int:doctor_id>')
def patient_history(patient_id, doctor_id):
    patient = Patient.query.get_or_404(patient_id)
    doctor = Doctor.query.get_or_404(doctor_id)
    records = MedicalRecord.query.filter_by(patient_id=patient_id, doctor_id=doctor_id).all()

    return render_template('pat_history.html', patient=patient, doctor=doctor, records=records)

@app.route('/doctor/details/<int:doctor_id>')
def doctor_details(doctor_id):
    doctor = Doctor.query.get_or_404(doctor_id)
    return render_template('doc_details.html', doctor=doctor)



@app.route('/doctor/availability/<int:doctor_id>', methods=['GET', 'POST'])
def doctor_availability(doctor_id):
    doctor = Doctor.query.get_or_404(doctor_id)
    today = datetime.today().date()
    possible_dates = [today + timedelta(days=i) for i in range(7)]
    possible_slots = ["08:00 - 12:00 am", "04:00 - 9:00 pm"]

    if request.method == 'POST':
        try:
            
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
            flash('Availability updated successfully.', 'success')
        except Exception as e:
            db.session.rollback()
            flash(f'An error occurred: {e}', 'danger')

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




