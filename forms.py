from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, SubmitField, TextAreaField, DateField, SelectField, BooleanField
from wtforms.validators import DataRequired, Length
# from wtforms.fields.html5 import DateField


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
    shift_coverage_date = DateField('Shift Coverage Date', validators=[
                                    DataRequired()], format='%Y-%m-%d')
    covering_user = SelectField('Covering Person', coerce=int, choices=[])
    reason_choices = [('vacation', 'Vacation'), ('personal_leave', 'Personal Leave'), ('funeral', 'Funeral'),
                      ('jury_duty', 'Jury Duty'), ('medical_leave', 'Medical Leave'), ('vote', 'To Vote'), ('other', 'Other')]
    reason = SelectField('Reason for Absent', validators=[
                         DataRequired()], choices=reason_choices)
    shift_time = StringField('Shift Time', validators=[DataRequired()])
    request_acknowledged = BooleanField(
        'I understand that this request is subject to approval by my employer', validators=[DataRequired()])
    manager_approval = BooleanField('Manager Approval')
    submit = SubmitField('Submit')


class BlacklistClientForm(FlaskForm):
    client_name = StringField('Client Name', validators=[
                              DataRequired(), Length(min=2, max=100)])
    reason = TextAreaField('Reason for Blacklisting', validators=[
                           DataRequired(), Length(min=2, max=500)])
    blacklisting_person = StringField('Person Blacklisting', validators=[
                                      DataRequired(), Length(min=2, max=100)])
    submit = SubmitField('Blacklist Client')


class EditBlacklistedClientForm(FlaskForm):
    client_name = StringField('Client Name', validators=[DataRequired()])
    reason = StringField('Reason', validators=[DataRequired()])
    blacklisting_person = StringField(
        'Person Blacklisting Client', validators=[DataRequired()])
    submit = SubmitField('Update Blacklisted Client')


class CreatePostForm(FlaskForm):
    content = TextAreaField('Content', validators=[DataRequired()])


class CommentForm(FlaskForm):
    content = StringField('Comment', validators=[DataRequired()])


class FeatureSuggestionForm(FlaskForm):
    suggestion = TextAreaField('Suggestion', validators=[DataRequired()])
    submit = SubmitField('Submit')
