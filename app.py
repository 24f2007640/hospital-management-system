from flask import Flask

from application.database import db #3

app = None

def create_app(): #1
    app = Flask(__name__)
    app.debug=True

    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///hms.sqlite3' #3
    db.init_app(app)

    app.app_context().push() #Consider this is as application context  #1
    return app

app = create_app()
from application.controllers import * #2
# from application.models import *



if __name__ == "__main__": #run this app only when ivoked.
    

    with app.app_context():
 
        db.create_all()
        manager = User.query.filter_by(username="Manager1").first()

        if manager is None:
            print("Creating default manager user...")
                      
            manager = User(
                username="Manager1", 
                email="1234@example.com", 
                password="123", 
                type="manager"                    
            )
            
            db.session.add(manager)
            db.session.commit()
            print("Manager user created.")
        else:
            print("Manager user already exists.")

    app.run()    


#pip install flask_sqlalchemy
