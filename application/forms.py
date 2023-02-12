from flask_wtf import FlaskForm
from flask_login import current_user
from wtforms import StringField, PasswordField, SubmitField, BooleanField, SelectField, IntegerField
from wtforms.validators import DataRequired, Length, Email, EqualTo, ValidationError, NumberRange
import sqlite3


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
    title = SelectField(u'Chess Title', choices=[('None'), ('WCM'), ('WFM'), ('WIM'), ('WGM'), ('CM'), ('FM'), ('IM'), ('GM')], validators=[DataRequired()])

    submit = SubmitField('Sign Up')
    

    def validate_username(self, username):
        conn = sqlite3.connect("instance/chessdb.db")
        curs = conn.cursor()
        curs.execute("SELECT * FROM user WHERE username = (?)", [username.data])
        user = curs.fetchone()
        conn.commit()
        conn.close()
        if user:
            raise ValidationError('That username is taken. Please choose a different one.')


    def validate_email(self, email):
        conn = sqlite3.connect("instance/chessdb.db")
        curs = conn.cursor()
        curs.execute("SELECT * FROM user WHERE email = (?)", [email.data])
        user = curs.fetchone()
        conn.commit()
        conn.close()
        if user:
            raise ValidationError('That email is taken. Please choose a different one.')


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
    elo = IntegerField('Elo',
                        validators=[NumberRange(1000,4000)])

    title = SelectField(u'Chess Title', 
    choices=[('None'), ('WCM'), ('WFM'), ('WIM'), ('WGM'), ('CM'), ('FM'), ('IM'), ('GM')], 
    validators=[DataRequired()])

    submit = SubmitField('Update')

    def validate_username(self, username):
        if username.data != current_user.username:
            conn = sqlite3.connect("instance/chessdb.db")
            curs = conn.cursor()
            curs.execute("SELECT * FROM user WHERE username = (?)", [username.data])
            user = curs.fetchone()
            conn.commit()
            conn.close()
            if user:
                raise ValidationError('That username is taken. Please choose a different one.')

    def validate_email(self, email):
        if email.data != current_user.email:
            conn = sqlite3.connect("instance/chessdb.db")
            curs = conn.cursor()
            curs.execute("SELECT * FROM user WHERE email = (?)", [email.data])
            user = curs.fetchone()
            conn.commit()
            conn.close()
            if user:
                raise ValidationError('That email is taken. Please choose a different one.')


class PlayerForm(FlaskForm):
    player = StringField('Nickname',
                    validators=[DataRequired(), Length(min=3, max=50)])
    submit = SubmitField('Search')

class SelectCountry(FlaskForm):
    country1 = SelectField('First Country',
                    validators=[DataRequired(), Length(min=3, max=100)])
    country2 = SelectField('Second Country',
                    validators=[DataRequired(), Length(min=3, max=100)])

    submit = SubmitField('Compare Selected Countries')

    def __init__(self):
        super(SelectCountry, self).__init__()
        con = sqlite3.connect("instance/rating.db")
        cur = con.cursor()
        cur.execute("Select code, name From federation")
        countries = cur.fetchall()
        con.commit()
        con.close()
        self.country1.choices = [(c[0], c[1]) for c in countries]
        self.country2.choices = [(c[0], c[1]) for c in countries]