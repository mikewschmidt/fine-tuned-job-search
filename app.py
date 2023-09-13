from flask import Flask, render_template, request, redirect, url_for
from flask_bootstrap import Bootstrap5, Bootstrap4
from flask_wtf import FlaskForm, CSRFProtect
from wtforms import SubmitField, StringField, PasswordField, IntegerRangeField, SelectField
from wtforms.validators import DataRequired, length
import pandas as pd
import db


app = Flask(__name__)
app.config['SECRET_KEY'] = 'KMHKQa!3seZ^PShQg!m@QPhWkYCSrKr2hG_WQ8nq=@w4_n6x#C$aSE=6$BVB_$G*S_#YaGE=sJLrLn*=CRQS!r_sjxhd%XquM8KJQ9BYw4&Up$XeMHw^MYH&2#YT*ayFuzKtvg@M?3y6$R*U#_k&_dE!286!6reds#2aRHq%nPy2v__Vp9Cx#eb%^eq&5?fpzt8GaUh=a9_b5w%4UwU%Rz*6LV7TG4jVU_mqHSKLhRB-yyxmLTvwntUye&r-@J$3'
app.config['BOOTSTRAP_BOOTSWATCH_THEME'] = 'cosmo'

bootstrap = Bootstrap5(app)
formData = {}


class SearchForm(FlaskForm):
    in_jobtitle = StringField('Job Title',
                              validators=[DataRequired(), length(min=4)],
                              render_kw={"placeholder": "Job Title"})
    in_location = StringField('Location',
                              validators=[DataRequired(), length(min=4)],
                              render_kw={"placeholder": "Location"})
    # integerslider = IntegerRangeField(render_kw={'min': '1', 'max': '10'})
    max_years = SelectField('Max Years', choices=[1, 2, 3, 4, 5])
    submit_btn = SubmitField('Submit')


# Variables that should probably be taken from user input on webpage
# title = "Data Engineer"
# location = "Chicago, IL"


@app.route('/', methods=['Post', 'Get'])
def index():
    form = SearchForm()
    if form.validate_on_submit():
        title = form.in_jobtitle.data
        location = form.in_location.data
        max_years = form.max_years.data
        jobs = db.query_db(title, location)
        return render_template('results.html', job_list=jobs, title=title, location=location, max_years=max_years)
    else:
        return render_template('index.html', form=form)

    # if request.method == 'POST':
    #    formData['title'] = request.form['inlineFormInputJobTitle']
    #    formData['location'] = request.form['inlineFormInputLocation']
    #    return redirect(url_for('results'))

    jobs = db.query_db(title, location)
    # return render_template("index.html", tables=[df_jobs.to_html(classes='card')], titles=df_jobs.columns.values)
    return render_template("index.html", job_list=jobs)


@app.route('/results')
def results():
    return render_template('results.html', title=formData['title'], location=formData['location'])


@app.route('/stats')
def stats():
    return render_template("stats.html")


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
    app.run(host='0.0.0.0', debug=True)