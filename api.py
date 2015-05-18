import os
import json
import hashlib

from rootpy.io import root_open
from wtforms import form, fields, validators
from werkzeug.security import generate_password_hash, check_password_hash

from flask import Flask, url_for, redirect, render_template, request
from flask_sqlalchemy import SQLAlchemy
import flask_admin as admin
import flask_login as login
from flask_admin.contrib import sqla
from flask_admin import helpers, expose

HASH_CHUNK_SIZE = 128

# Create Flask application
app = Flask(__name__)

# Create dummy secrey keyfro- so we can use sessions
app.config['SECRET_KEY'] = 'L46EIDJ2VX'

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
    pattern = db.Column(db.Integer, db.ForeignKey('histogram.id'))
    exemplar = db.Column(db.Integer, db.ForeignKey('histogram.id'))
    result = db.Column(db.Float)
    time = db.Column(db.DateTime)
    request_source = db.Column(db.String(64), db.ForeignKey('RequestType.id'))
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

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    md5_hash = db.Column(db.String(64))
    path = db.Column(db.String(255))
    hist = db.relationship('Histogram', backref='file_name', lazy='dynamic')

    def __unicode__(self):
        return self.path


class RequestType(db.Model):

    __tablename__ = 'RequestType'
    id = db.Column(db.Integer, primary_key=True)
    type = db.Column(db.String(64))
    requests_type_relation = db.relationship('Request', backref='request_typ', lazy='dynamic')

    def __unicode__(self):
        return self.type


class Technique(db.Model):

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(64))
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

        if not check_password_hash(user.password, self.password.data):
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


def md5_sum_calculation(file_name):
    hash_values = hashlib.md5()
    with open(file_name, 'r') as file_object:
        # Iterating over small chunks of file
        for chunk in iter(lambda: file_object.read(HASH_CHUNK_SIZE), ''):
            hash_values.update(chunk)
    return hash_values.hexdigest()


def get_file_id(file_path):
        file_query = File.query.filter_by(path=file_path).all()
        if not file_query:
            new_hist_file = File(path=file_path,
                                 md5_hash=md5_sum_calculation(file_path))
            db.session.add(new_hist_file)
            db.session.flush()
            file_id= new_hist_file.id
        elif len(file_query) > 1:
            raise ValueError('Two identical files in database')
        else:
            file_id = file_query[0].id
        return file_id


def get_histogram_id(hist_path, file_id):
    histogram_query = Histogram.query.filter_by(file_id=file_id, path=hist_path).all()
    if not histogram_query:
        new_hist_object = Histogram(path=hist_path, file_id=file_id)
        db.session.add(new_hist_object)
        db.session.flush()
        histogram_id = new_hist_object.id
    elif len(file_id) > 1:
        raise ValueError('Two identical histograms in database')
    else:
        histogram_id = histogram_query[0].id
    return histogram_id


def get_request_type_id(request_type):
    request_type = RequestType.query.filter_by(type=request_type).all()
    if not request_type:
        raise ValueError('No Such Request Type')
    elif len(request_type) > 1:
        raise ValueError('Two identical request types')
    else:
        request_type_id = request_type[0].id
    return request_type_id


def get_technique_id(technique_name):
    request_technique = Technique.query.filter_by(name=technique_name).all()
    if not request_technique:
        raise ValueError("No such technique")
    elif len(request_technique) > 1:
        raise ValueError("Two identical techniques")
    else:
        technique_id = request_technique[0].id
    return technique_id


def hist_checking(base_hist_location, cur_hist_location, path, technique):
    with root_open(base_hist_location) as base_file, \
            root_open(cur_hist_location) as cur_file:
        cur_hist = cur_file.get(path.encode('ascii','ignore'))
        base_hist = base_file.get(path.encode('ascii','ignore'))
        if technique == 'Kolmogorov-Smirnov':
            p_value = cur_hist.KolmogorovTest(base_hist)
        elif technique == 'Chi2Test':
            p_value = cur_hist.Chi2Test(base_file)
    return p_value


def save_request_result(first_histogram_id, second_histogram_id,
                        request_type_id, technique_id, p_value):
    new_request = Request()
    new_request.pattern = first_histogram_id
    new_request.exemplar = second_histogram_id
    new_request.time = db.func.now()
    new_request.request_source = request_type_id
    new_request.technique = technique_id
    new_request.result = p_value
    db.session.add(new_request)
    db.session.commit()


def previous_request_processing(last_request):
    first_hist = Histogram.query.get(last_request.pattern)
    second_hist = Histogram.query.get(last_request.exemplar)
    technique_id = last_request.technique
    technique = Technique.query.get(technique_id)
    first_file_id = first_hist.file_id
    second_file_id = second_hist.file_id
    first_file = File.query.get(first_file_id)
    second_file = File.query.get(second_file_id)
    base_hist_location = first_file.path
    cur_hist_location = second_file.path
    path = first_hist.path

    pattern_file = File.query.filter_by(id=first_file_id).first()
    pattern_file_location = pattern_file.path
    pattern_file_hash = pattern_file.md5_hash
    pattern_current_hash = md5_sum_calculation(pattern_file_location)
    exemplar_file = File.query.filter_by(id=second_file_id).first()
    exemplar_hash = exemplar_file.md5_hash
    exemplar_file_location = exemplar_file.path
    exemplar_current_hash = md5_sum_calculation(exemplar_file_location)
    # Update hashes if they have changed
    if (exemplar_hash == exemplar_current_hash and
        pattern_file_hash == pattern_current_hash):
        p_value = last_request.result
    else:
        hist_checking(base_hist_location, cur_hist_location, path, technique)
        p_value = last_request.result
    return p_value


@app.route('/compare')
def compare():
    try:
        # Request Parameters Reading
        base_hist_location = request.args['base_hist']
        cur_hist_location = request.args['cur_hist']
        all_paths = request.args['paths']
        request_type = request.args['type']
        technique = request.args['technique']

        request_type_id = get_request_type_id(request_type)
        technique_id = get_technique_id(technique)
        first_file_id = get_file_id(base_hist_location)
        second_file_id = get_file_id(cur_hist_location)
        first_histogram_id = get_histogram_id(first_file_id, all_paths)
        second_histogram_id = get_histogram_id(second_file_id, all_paths)
        # Check if query already exists
        previous_request = Request.query.filter_by(pattern=first_histogram_id,
                                                   exemplar=second_histogram_id).all()
        if previous_request:
            previous_request_processing(previous_request[-1])
        else:
            p_value = hist_checking(base_hist_location, cur_hist_location, all_paths, technique)
        save_request_result(first_histogram_id, second_histogram_id,
                             request_type_id, technique_id, p_value)
        return json.dumps({'rc': 0, 'message': '', 'distance': 1. - p_value})
    except Exception, error_message:
        return json.dumps({'rc': 1, 'distance': None, 'message': error_message})


@app.route('/check')
def check():
    try:
        base_hist_location = request.args['base_hist']
        cur_hist_location = request.args['cur_hist']
        all_paths = request.args['paths']
        request_type = request.args['type']
        technique = request.args['technique']
        previous_request = Request.query.filter_by(pattern=first_histogram_id,
                                                   exemplar=second_histogram_id).all()




def build_sample_db():
    db.create_all()
    db.drop_all()
    db.create_all()
    user = User()
    user.first_name = 'admin'
    user.last_name = 'admin'
    user.login = 'admin'
    user.email = user.login + "@example.com"
    user.password = generate_password_hash('admin')
    db.session.add(user)
    db.session.add(RequestType(type='User'))
    db.session.add(RequestType(type='Bot'))
    db.session.add(Technique(name='chi_square'))
    db.session.add(Technique(name='Kolmogorov-Smirnov'))
    db.session.commit()


# Initialize flask-login
init_login()

# Create admin
admin = admin.Admin(app, 'Anomaly Detection', index_view=AdminIndexView(), base_template='my_master.html')

# Add view
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
