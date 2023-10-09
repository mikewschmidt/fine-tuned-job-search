from flask import Flask, render_template, request, session, redirect, url_for, send_from_directory
from flask_bootstrap import Bootstrap5, Bootstrap4
from flask_wtf import FlaskForm, CSRFProtect
from wtforms import SubmitField, StringField, PasswordField, IntegerRangeField, SelectField, IntegerField, HiddenField
from wtforms.validators import DataRequired, Email, length
import pandas as pd
from scraper import *
from db import *
#from flask_login import LoginManager, UserMixin
from werkzeug.security import generate_password_hash, check_password_hash
from flask_dance.contrib.google import make_google_blueprint, google
from dotenv import load_dotenv

# Loading environment variables from .env
load_dotenv()

#login_manager = LoginManager()

app = Flask(__name__)
app.config['SECRET_KEY'] = os.environ['FLASK_SECRET_KEY']
app.config['BOOTSTRAP_BOOTSWATCH_THEME'] = 'cosmo'


blueprint = make_google_blueprint(
    client_id= os.environ.get('GOOGLE_OAUTH_CLIENT_ID'),
    client_secret= os.environ.get('GOOGLE_OAUTH_CLIENT_SECRET'),
    # reprompt_consent=True,
    #offline=True,
    #scope=["profile", "email"]
    scope=["https://www.googleapis.com/auth/userinfo.profile", "https://www.googleapis.com/auth/userinfo.email", "openid"]
)
app.register_blueprint(blueprint, url_prefix="/login")


bootstrap = Bootstrap5(app)
formData = {}

#login_manager.init_app(app)
#login_manager.login_view = 'login'

# WTForm class
class SearchForm(FlaskForm):
    in_jobtitle = StringField('Job Title',
                              validators=[DataRequired(), length(min=3)],
                              render_kw={"placeholder": "Job Title"})
    in_location = StringField('Location',
                              validators=[DataRequired(), length(min=4)],
                              render_kw={"placeholder": "Location"})
    # integerslider = IntegerRangeField(render_kw={'min': '1', 'max': '10'})
    max_years = SelectField('Max Years', choices=[(1, '<= 1 year'),
                                                  (2, '<= 2 years'), (3, '<= 3 years'), (4, '<= 4 years'), (5, '<= 5 years')])
    job_count = HiddenField('')
    submit_btn = SubmitField('Submit')

@app.route('/<path:path>')
def send_report(path):
    return send_from_directory('templates', path)

@app.route('/', methods=['POST', 'GET'])
def index():
    form = SearchForm()
    if form.validate_on_submit():
        print("FORM HAS BEEN VALIDATED!!")
        title = form.in_jobtitle.data
        location = form.in_location.data
        max_years = int(form.max_years.data)
        job_count = 0
        # jobs = db.query_db(title, location)  # Direct query on database
        # print("Length of jobs: ", len(jobs))
        jobs = get_job_results_for_website(
            title, location, max_years=max_years, job_count=job_count)
        return render_template('results.html', job_list=jobs, title=title, location=location, max_years=max_years, job_count=job_count, form=form)
    else:
        return render_template('index.html', form=form)

    # if request.method == 'POST':
    #    formData['title'] = request.form['inlineFormInputJobTitle']
    #    formData['location'] = request.form['inlineFormInputLocation']
    #    return redirect(url_for('results'))

    jobs = db.query_db(title, location)
    # return render_template("index.html", tables=[df_jobs.to_html(classes='card')], titles=df_jobs.columns.values)
    return render_template("index.html", job_list=jobs)



@app.route('/welcome')
def welcome():
    resp = google.get("/oauth2/v2/userinfo")
    assert resp.ok, resp.text
    email=resp.json()["email"]

    return render_template("welcome.html",email=email)

@app.route('/login/google')
def login():
    if not google.authorized:
        return render_template(url_for('google.login'))
    resp = google.get("/oauth2/v2/userinfo")
    assert resp.ok, resp.text
    email=resp.json()["email"]

    return render_template('welcome.html', email=email)


@app.route('/results', methods=["POST", "GET"])
def results():

    # if request.method == 'POST':
    #    if request.form.get('back')
    # return render_template('results.html', title=formData['title'], location=formData['location'])
    return render_template('results.html')


@app.route('/stats')
def stats():
    form = SearchForm()
    return render_template("stats.html", form=form)


@app.route('/about')
def about():
    form = SearchForm()
    if form.validate_on_submit():
        title = form.in_jobtitle.data
        location = form.in_location.data
        return render_template('results.html', title=title, location=location)
    else:
        return render_template('about.html', form=form)
    return render_template("about.html")


# Dynamic Route
@app.route('/user/<name>')
def user(name):
    return f"<h1> This is a page for {name[10]} </h1>"

# def data():
#    return render_template('data_engineer_San_Jose,_California,_United_States.html')
if __name__ == '__main__':
    #port = input("Which port do you want to run on?  ")
    #if not port.isdigit() or not isinstance(port, int):
    #    port=5000
    app.run(host='0.0.0.0', port=5000, debug=True)
