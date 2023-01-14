from flask_wtf import FlaskForm
from flask_login import current_user
from wtforms import StringField, PasswordField, SubmitField, BooleanField, SelectField, IntegerField
from wtforms.validators import DataRequired, Length, Email, EqualTo, ValidationError, NumberRange
from application.models import User

class RegistrationForm(FlaskForm):
    username = StringField('Username',
                           validators=[DataRequired(), Length(min=2, max=20)])
    email = StringField('Email',
                        validators=[DataRequired(), Email()])
    password = PasswordField('Password', validators=[DataRequired()])
    confirm_password = PasswordField('Confirm Password',
                                     validators=[DataRequired(), EqualTo('password')])
    year_of_birth = StringField('Year of birth',
                        validators=[DataRequired()])
    elo = IntegerField('Rating Elo', validators=[NumberRange(1000,4000)])
    title = SelectField(u'Chess Title', choices=[(' '), ('WCM'), ('WFM'), ('WIM'), ('WGM'), ('CM'), ('FM'), ('IM'), ('GM')], validators=[DataRequired()])

    submit = SubmitField('Sign Up')
    

    def validate_username(self, username):
        user = User.query.filter_by(username=username.data).first()
        if user:
            raise ValidationError('That username is taken. Please choose a different one.')

    def validate_email(self, email):
        user = User.query.filter_by(email=email.data).first()
        if user:
            raise ValidationError('That email is taken. Please choose a different one.')

    def validate_elo(self, elo):
        user = User.query.filter_by(elo=elo.data).first()
    
    def validate_title(self, title):
        user = User.query.filter_by(title=title.data).first()

class LoginForm(FlaskForm):
    email = StringField('Email',
                        validators=[DataRequired(), Email()])
    password = PasswordField('Password', validators=[DataRequired()])
    remember = BooleanField('Remember Me')
    submit = SubmitField('Login')

class GameForm(FlaskForm):
    piece_color = SelectField(u'Piece color', choices=[('white', 'White'), ('black', 'Black')], validators=[DataRequired()])
    result = SelectField(u'Result', choices=[('won', 'Won'), ('draw', 'Draw'), ('lost', 'Lost')], validators=[DataRequired()])
    moves = StringField('Moves', validators=[DataRequired()])
    add = SubmitField('Add')

class UpdateAccountForm(FlaskForm):
    username = StringField('Username',
                        validators=[DataRequired(), Length(min=2, max=20)])
    email = StringField('Email',
                        validators=[DataRequired(), Email()])
    elo = StringField('Elo',
                        validators=[DataRequired()])

    title = SelectField(u'Chess Title', 
    choices=[(' '), ('WCM'), ('WFM'), ('WIM'), ('WGM'), ('CM'), ('FM'), ('IM'), ('GM')], 
    validators=[DataRequired()])

    submit = SubmitField('Update')

    def validate_username(self, username):
        if username.data != current_user.username:
            user = User.query.filter_by(username=username.data).first()
            if user:
                raise ValidationError('That username is taken. Please choose a different one.')

    def validate_email(self, email):
        if email.data != current_user.email:
            user = User.query.filter_by(email=email.data).first()
            if user:
                raise ValidationError('That email is taken. Please choose a different one.')
    
    def validate_elo(self, elo):
        if elo.data != current_user.elo:
            user = User.query.filter_by(elo=elo.data).first()
    
    def validate_elo(self, title):
        if title.data != current_user.title:
            pass

class PlayerForm(FlaskForm):
    player = StringField('Nickname',
                    validators=[DataRequired(), Length(min=3, max=50)])
    submit = SubmitField('Search')

class SelectCountry(FlaskForm):
    country1 = StringField('First Country',
                    validators=[DataRequired(), Length(min=3, max=100)])
    country2 = StringField('Second Country',
                    validators=[DataRequired(), Length(min=3, max=100)])
    submit = SubmitField('Compare Selected Countries')

