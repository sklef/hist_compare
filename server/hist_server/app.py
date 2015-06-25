#!/usr/bin/env python

import os
import flask_admin as admin
from flask_admin.contrib import sqla
from flask import Flask
from flask_sqlalchemy import SQLAlchemy

# Create Flask application
app = Flask(__name__)
app.config.from_envvar('HISTCOMPARE_CONFIG')
# Loads data base
db = SQLAlchemy(app)


import utils
import db_models
from views import AdminIndexView, compare


admin = admin.Admin(app, 'Anomaly Detection', index_view=AdminIndexView(), base_template='my_master.html')

# Add view
app.view_functions['compare'] = compare
app.add_url_rule('/compare', 'compare', compare)
admin.add_view(sqla.ModelView(db_models.Request, db.session))
admin.add_view(sqla.ModelView(db_models.Histogram, db.session))
admin.add_view(sqla.ModelView(db_models.File, db.session))


if __name__ == '__main__':
    # Build a sample db on the fly, if one does not exist yet.
    app_dir = os.path.realpath(os.path.dirname(__file__))
    database_path = os.path.join(app_dir, app.config['DATABASE_FILE'])
    if not os.path.exists(database_path):
        utils.build_sample_db()
    # Start app
    app.run(debug=True)
