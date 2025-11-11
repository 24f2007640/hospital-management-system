from .database import db 
from datetime import datetime



class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password = db.Column(db.String(200), nullable=False)
    type = db.Column(db.String(20), nullable=False, default='patient')

    # Relationships
    # link to their profile
    doctor_profile = db.relationship('Doctor', back_populates='user', uselist=False)
    patient_profile = db.relationship('Patient', back_populates='user', uselist=False)


class Doctor(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    specialty = db.Column(db.String(100), nullable=False)
    phone = db.Column(db.String(20))
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), unique=True, nullable=False)
    
    # Back-reference to the User model
    user = db.relationship('User', back_populates='doctor_profile')
    
    # Relationships
    appointments = db.relationship('Appointment', back_populates='doctor')
    medical_records = db.relationship('MedicalRecord', back_populates='doctor')


class Patient(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    dob = db.Column(db.Date) 
    address = db.Column(db.String(255))
    phone = db.Column(db.String(20))
    
    # nullable=True means a patient
    # can exist in the system without having a login account
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), unique=True, nullable=True)
    
 
    user = db.relationship('User', back_populates='patient_profile')

    appointments = db.relationship('Appointment', back_populates='patient')
    medical_records = db.relationship('MedicalRecord', back_populates='patient')
    bills = db.relationship('Billing', back_populates='patient')




class Appointment(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    reason = db.Column(db.Text)
    appt_date = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    

    # Status can be 'pending', 'confirmed', 'cancelled', 'completed'
    status = db.Column(db.String(20), nullable=False, default='pending') 
    
    patient_id = db.Column(db.Integer, db.ForeignKey('patient.id'), nullable=False)
    doctor_id = db.Column(db.Integer, db.ForeignKey('doctor.id'), nullable=False)
    
    patient = db.relationship('Patient', back_populates='appointments')
    doctor = db.relationship('Doctor', back_populates='appointments')


class MedicalRecord(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    diagnosis = db.Column(db.Text, nullable=False)
    treatment = db.Column(db.Text)
    notes = db.Column(db.Text)
    record_date = db.Column(db.Date, nullable=False, default=datetime.utcnow)
    
    patient_id = db.Column(db.Integer, db.ForeignKey('patient.id'), nullable=False)
    doctor_id = db.Column(db.Integer, db.ForeignKey('doctor.id'), nullable=False) # Doctor who wrote the record
    
    patient = db.relationship('Patient', back_populates='medical_records')
    doctor = db.relationship('Doctor', back_populates='medical_records')


class Billing(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    amount = db.Column(db.Float, nullable=False)
    status = db.Column(db.String(20), nullable=False, default='pending') # 'pending', 'paid', 'overdue'
    date_issued = db.Column(db.Date, nullable=False, default=datetime.utcnow)
    patient_id = db.Column(db.Integer, db.ForeignKey('patient.id'), nullable=False)

    patient = db.relationship('Patient', back_populates='bills')