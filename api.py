import os
import json
from rootpy.io import root_open
from flask import Flask, url_for, redirect, render_template, request
from flask_sqlalchemy import SQLAlchemy
from wtforms import form, fields, validators
import flask_admin as admin
import flask_login as login
from flask_admin.contrib import sqla
from flask_admin import helpers, expose
from werkzeug.security import generate_password_hash, check_password_hash


# Create Flask application
app = Flask(__name__)

# Create dummy secrey key so we can use sessions
app.config['SECRET_KEY'] = '123456790'

# Create in-memory database
app.config['DATABASE_FILE'] = 'db.sqlite'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///' + app.config['DATABASE_FILE']
app.config['SQLALCHEMY_ECHO'] = True
db = SQLAlchemy(app)


# Create user model.
class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    first_name = db.Column(db.String(100))
    last_name = db.Column(db.String(100))
    login = db.Column(db.String(80), unique=True)
    email = db.Column(db.String(120))
    password = db.Column(db.String(64))
    requests = db.relationship('Request', backref='user_name', lazy='dynamic')

    # Flask-Login integration
    def is_authenticated(self):
        return True

    def is_active(self):
        return True

    def is_anonymous(self):
        return False

    def get_id(self):
        return self.id

    # Required for administrative interface
    def __unicode__(self):
        return self.first_name


class Request(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user = db.Column(db.Integer, db.ForeignKey('user.id'))
    pattern = db.Column(db.Integer, db.ForeignKey('histogram.id'))
    exemplar = db.Column(db.Integer, db.ForeignKey('histogram.id'))
    result = db.Column(db.Float)
    time = db.Column(db.DateTime)
    technique = db.Column(db.String(100), db.ForeignKey('technique.name'))

    def __unicode__(self):
        return self.id


class Histogram(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    path = db.Column(db.String(255))
    file_id = db.Column(db.Integer, db.ForeignKey('file.id'))
    pattern = db.relationship('Request', backref='pattern_name', primaryjoin='Request.pattern == Histogram.id')
    example = db.relationship('Request', backref='exemplar_name', primaryjoin='Request.exemplar == Histogram.id')

    def __unicode__(self):
        return self.path


class File(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    path = db.Column(db.String(255))
    hist = db.relationship('Histogram', backref='file_name', lazy='dynamic')

    def __unicode__(self):
        return self.path


class Technique(db.Model):
    name = db.Column(db.String(100), primary_key=True)
    technique_relation = db.relationship('Request', backref='used_technique', lazy='dynamic')

    def __unicode__(self):
        return self.name


# Define login and registration forms (for flask-login)
class LoginForm(form.Form):
    login = fields.StringField(validators=[validators.required()])
    password = fields.PasswordField(validators=[validators.required()])

    def validate_login(self, field):
        user = self.get_user()

        if user is None:
            raise validators.ValidationError('Invalid user')

        # we're comparing the plaintext pw with the the hash from the db
        if not check_password_hash(user.password, self.password.data):
        # to compare plain text passwords use
        # if user.password != self.password.data:
            print self.password.data
            raise validators.ValidationError('Invalid password')

    def get_user(self):
        return db.session.query(User).filter_by(login=self.login.data).first()


# Initialize flask-login
def init_login():
    login_manager = login.LoginManager()
    login_manager.init_app(app)

    # Create user loader function
    @login_manager.user_loader
    def load_user(user_id):
        return db.session.query(User).get(user_id)


# Create customized model view class
class ModelView(sqla.ModelView):

    def is_accessible(self):
        return login.current_user.is_authenticated()


# Create customized index view class that handles login & registration
class AdminIndexView(admin.AdminIndexView):

    @expose('/')
    def index(self):
        if not login.current_user.is_authenticated():
            return redirect(url_for('.login_view'))
        return super(AdminIndexView, self).index()

    @expose('/login/', methods=('GET', 'POST'))
    def login_view(self):
        # handle user login
        form = LoginForm(request.form)
        if helpers.validate_form_on_submit(form):
            user = form.get_user()
            login.login_user(user)

        if login.current_user.is_authenticated():
            return redirect(url_for('.index'))
        self._template_args['form'] = form
        return super(AdminIndexView, self).index()

    

    @expose('/logout/')
    def logout_view(self):
        login.logout_user()
        return redirect(url_for('.index'))


# Flask views
@app.route('/')
def index():
    return render_template('index.html')


@app.route('/compare')
def compare():
    try:
        base_hist = request.args['base_hist']
        cur_hist = request.args['cur_hist']
        all_paths = request.args['paths']
        base_file = root_open(base_hist)
        cur_file = root_open(cur_hist)
        cur_hist = cur_file.get(all_paths.encode('ascii','ignore'))
        base_hist = base_file.get(all_paths.encode('ascii','ignore'))
        p_value = cur_hist.KolmogorovTest(base_hist)
        first_file_id = File.query.filter_by(path=base_hist).first().id
        second_file_id = File.query.filter_by(path=cur_hist).first().id
        first_histogram_id = Histogram.query.filter_by(file_id=first_file_id, path=all_paths).first().id
        second_histogram_id = Histogram.query.filter_by(file_id=second_file_id, path=all_paths).first().id
        new_request = Request()
        new_request.pattern = first_histogram_id
        new_request.exemplar = second_histogram_id
        new_request.time = db.func.now()
        new_request.exemplar = second_file_id
        # ToDo authorization
        new_request.user = 1
        new_request.technique = 'Kolmogorov-Smirnov'
        new_request.result = p_value
        db.session.add(new_request)
        db.session.commit()
        return json.dumps({'rc': 0, 'message': '', 'distance': 1 - p_value})
    except Exception, error_message:
        return json.dumps({'rc': 1, 'distance': None, 'message': error_message})



@app.route('/compare')
def compare():
    first_file = request.args['first_hist']
    second_file = request.args['second_hist']
    histogram_path = request.args['path']
    first_file_id = File.query.filter_by(path=first_file).first().id
    second_file_id = File.query.filter_by(path=second_file).first().id
    first_histogram_id = Histogram.query.filter_by(file_id=first_file_id, path=histogram_path).first().id
    second_histogram_id = Histogram.query.filter_by(file_id=second_file_id, path=histogram_path).first().id
    new_request = Request()
    new_request.pattern = first_histogram_id
    new_request.exemplar = second_histogram_id
    new_request.time = db.func.now()
    new_request.exemplar = second_file_id
    new_request.user = 1
    new_request.technique = 'chi square'
    new_request.result = 0.5
    db.session.add(new_request)
    db.session.commit()
    return request.args['path']


def build_sample_db():
    
    db.drop_all()
    db.create_all()
     
    user = User()
    user.first_name = 'admin'
    user.last_name = 'admin'
    user.login = 'admin'
    user.email = user.login + "@example.com"
    user.password = generate_password_hash('admin')
    db.session.add(user)
    db.session.commit()
    request = Request()
    db.session.add(request)
    db.session.commit()
    histogram = Histogram()
    db.session.add(histogram)
    db.session.commit()
    new_file = File()
    db.session.add(new_file)
    db.session.commit()
    technique = Technique()
    technique.name = 'chi square'
    anotherTechnique = Technique()
    anotherTechnique.name = 'Kolmogorov-Smirnov'
    db.session.add(technique)
    db.session.add(anotherTechnique)
    db.session.commit()


# Initialize flask-login
init_login()

# Create admin
admin = admin.Admin(app, 'Anomaly Detection', index_view=AdminIndexView(), base_template='my_master.html')

# Add view
admin.add_view(ModelView(User, db.session))
admin.add_view(ModelView(Request, db.session))
admin.add_view(ModelView(Histogram, db.session))
admin.add_view(ModelView(File, db.session))


if __name__ == '__main__':

    # Build a sample db on the fly, if one does not exist yet.
    app_dir = os.path.realpath(os.path.dirname(__file__))
    database_path = os.path.join(app_dir, app.config['DATABASE_FILE'])
    if not os.path.exists(database_path):
        build_sample_db()

    # Start app
    app.run(debug=True)
