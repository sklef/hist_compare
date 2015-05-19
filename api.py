import os
import flask_admin as admin
from flask_admin.contrib import sqla

from flask import Flask
from flask_sqlalchemy import SQLAlchemy

# Create Flask application
app = Flask(__name__)

# Create dummy secrey keyfro- so we can use sessions
app.config['SECRET_KEY'] = 'L46EIDJ2VX'

# Create in-memory database
app.config['DATABASE_FILE'] = 'db.sqlite'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///' + app.config['DATABASE_FILE']
app.config['SQLALCHEMY_ECHO'] = True
db = SQLAlchemy(app)


import logic
import db_models
from views import AdminIndexView

#
# Create admin
admin = admin.Admin(app, 'Anomaly Detection', index_view=AdminIndexView(), base_template='my_master.html')

# Add view
admin.add_view(sqla.ModelView(db_models.Request, db.session))
admin.add_view(sqla.ModelView(db_models.Histogram, db.session))
admin.add_view(sqla.ModelView(db_models.File, db.session))


if __name__ == '__main__':
    # Build a sample db on the fly, if one does not exist yet.
    app_dir = os.path.realpath(os.path.dirname(__file__))
    database_path = os.path.join(app_dir, app.config['DATABASE_FILE'])
    if not os.path.exists(database_path):
        logic.build_sample_db()
    # Start app
    app.run(debug=True)
