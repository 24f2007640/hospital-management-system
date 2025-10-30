from flask import Flask

from application.database import db #3

app = None

def create_app(): #1
    app = Flask(__name__)
    app.debug=True

    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///hms.sqlite3' #3
    db.init_app(app)

    app.ap_context().push() #Consider this is as application context  #1
    return app

app = create_app()
from application.controllers import * #2
# from application.models import *

if __name__ == '__main': #run this app only when ivoked.
    app.run()

#Note: When we run this app module, it will create a proxy object as current_app which we can use later
#in the other files and it will also avoid circular impory error. mapping happen at this place

