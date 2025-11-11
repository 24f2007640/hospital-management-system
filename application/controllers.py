
from flask import Flask , render_template, redirect, request
from flask import current_app as app
from .models import *





@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        
        username = request.form.get("username") 
        pwd = request.form.get('pwd')
        
        this_user = User.query.filter_by(username=username).first()

        if this_user:
            if this_user.password == pwd:
                
                if this_user.type == "manager":
                    return redirect('/Adm_Admin-Welcome.html')
                    
                elif this_user.type == "doctor":
                    return redirect('/Doc_Welcome-doc.html')
                    
                elif this_user.type == "patient":
                    return redirect('/Pat_Welcome.html')

            else:
                return render_template("login.html", error="Incorrect password")
        else:
            return render_template("login.html", error="User not found")
            
    return render_template("login.html")



@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        name = request.form.get('name')
        
        username_exists = User.query.filter_by(username=username).first()
        

        if username_exists:
            return render_template("already.html", error="Username already taken")

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
            
            return redirect('/login')

    return render_template("register.html")



# --- You will need to define these routes elsewhere in your app ---

# @app.route('/manager/dashboard')
# def manager_dashboard():
#     return "Welcome Manager"

# @app.route('/doctor/dashboard')
# def doctor_dashboard():
#     return "Welcome Doctor"

# @app.route('/patient/dashboard')
# def patient_dashboard():
#     return "Welcome Patient"

