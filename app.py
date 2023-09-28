from flask import Flask, render_template, request, redirect, url_for
from flask_bootstrap import Bootstrap5, Bootstrap4
from flask_wtf import FlaskForm, CSRFProtect
from wtforms import SubmitField, StringField, PasswordField, IntegerRangeField, SelectField, IntegerField, HiddenField
from wtforms.validators import DataRequired, length
import pandas as pd
from scraper import *
from db import *


app = Flask(__name__)
app.config['SECRET_KEY'] = os.environ['FLASK_SECRET_KEY']
app.config['BOOTSTRAP_BOOTSWATCH_THEME'] = 'cosmo'

bootstrap = Bootstrap5(app)
formData = {}

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


# def data():
#    return render_template('data_engineer_San_Jose,_California,_United_States.html')
if __name__ == '__main__':
    port = input("Which port do you want to run on?")
    if not port.isdigit() or not isinstance(port, int):
        port=5000
    app.run(host='0.0.0.0', port=port, debug=True)
