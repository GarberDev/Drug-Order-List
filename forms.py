from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, SubmitField, DateField, SelectField
from wtforms.validators import DataRequired


class RegistrationForm(FlaskForm):
    username = StringField('Username', validators=[DataRequired()])
    password = PasswordField('Password', validators=[DataRequired()])
    email = StringField('Email', validators=[DataRequired()])
    first_name = StringField('First Name', validators=[DataRequired()])
    last_name = StringField('Last Name', validators=[DataRequired()])
    submit = SubmitField('Register')


class LoginForm(FlaskForm):
    username = StringField('Username', validators=[DataRequired()])
    password = PasswordField('Password', validators=[DataRequired()])
    submit = SubmitField('Login')


class TimeOffRequestForm(FlaskForm):
    start_date = DateField('Start Date', validators=[
                           DataRequired()], format='%Y-%m-%d')
    end_date = DateField('End Date', validators=[
                         DataRequired()], format='%Y-%m-%d')
    covering_user = SelectField('Covering Person', coerce=int, choices=[])
    submit = SubmitField('Submit')


class EditBlacklistedClientForm(FlaskForm):
    client_name = StringField('Client Name', validators=[DataRequired()])
    reason = StringField('Reason', validators=[DataRequired()])
    blacklisting_person = StringField(
        'Person Blacklisting Client', validators=[DataRequired()])
    submit = SubmitField('Update Blacklisted Client')
