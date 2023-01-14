from application import app, db, bcrypt
from flask import render_template, request, url_for, flash, redirect
from application.forms import RegistrationForm, LoginForm, GameForm, UpdateAccountForm, PlayerForm
from flask_login import login_user, current_user, logout_user, login_required
from application.models import User, Game
import pandas as pd
import json
import plotly
import plotly_express as px
import chess.svg
import chess.pgn
from io import StringIO
import sqlite3

@app.route("/")
@app.route("/home")
def index():
    return render_template("index.html", title = "Home")


@app.route("/register", methods=['GET', 'POST'])
def register():
    if current_user.is_authenticated:
        return redirect(url_for("home"))

    form = RegistrationForm()

    if form.validate_on_submit():
        hashed_password = bcrypt.generate_password_hash(form.password.data).decode('utf-8')
        user = User(username=form.username.data, email=form.email.data, year_of_birth=form.year_of_birth.data, elo=form.elo.data, title=form.title.data, password=hashed_password)
        db.session.add(user)
        db.session.commit()
        flash("Your account has been created! Welcome to ChesStats!", "success")
        return redirect(url_for("login"))

    return render_template('register.html', title='Register', form=form)


@app.route("/login", methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for("index"))

    form = LoginForm()

    if form.validate_on_submit():
        user = User.query.filter_by(email=form.email.data).first()
        if user and bcrypt.check_password_hash(user.password, form.password.data):
            login_user(user, remember=form.remember.data)
            next_page = request.args.get('next')
            return redirect(next_page) if next_page else redirect(url_for('index'))
        else:
            flash('Login Unsuccessful. Please check email and password', 'danger')

    return render_template('login.html', title='Login', form=form)

@app.route("/logout")
def logout():
    logout_user()
    return redirect(url_for('index'))

@app.route("/callback")
def cb():
    return graph(request.args.get('data'))


@app.route("/dashboard")
@login_required
def dashboard():
    return render_template('dashboard.html', title='Dashboard', graphJSON=graph())


def graph():
    df = pd.DataFrame(px.data.gapminder())

    fig = px.line(df[df['country']=='United Kingdom'], x='year', y='gdpPercap')

    graphJSON = json.dumps(fig, cls=plotly.utils.PlotlyJSONEncoder)

    return graphJSON


@app.route("/account", methods=['GET', 'POST'])
@login_required
def account():
    form = UpdateAccountForm()
    if form.validate_on_submit():
        current_user.username = form.username.data
        current_user.email = form.email.data
        current_user.elo = form.elo.data
        current_user.title = form.title.data
        db.session.commit()
        flash('Your account has been updated!', 'success')
        return redirect(url_for('account'))
    elif request.method == 'GET':
        form.username.data = current_user.username
        form.email.data = current_user.email
        form.elo.data = current_user.elo
        form.title.data = current_user.title
    return render_template('account.html', title='Account', form=form)


@app.route("/game/new", methods=['GET', 'POST'])
@login_required
def add_game():
    form = GameForm()
    if form.validate_on_submit():
        game = Game(player=current_user.username, piece_color=form.piece_color.data, result=form.result.data, moves=form.moves.data)
        db.session.add(game)
        db.session.commit()
        flash('You have added a game!', 'success')
        return redirect(url_for('index'))
    return render_template('add_game.html', title='Add Game', form=form, legend='Add Game')


@app.route("/game/view", methods=['GET', 'POST'])
@login_required
def view_game():
    games = Game.query.filter_by(player=current_user.username).all()

    return render_template('game_table.html', data=games)

@app.route("/test", methods=['GET', 'POST'])
def test():

    moves = ['rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR']

    pgn = request.form.get('view')

    pgn = StringIO(pgn)
    
    game = chess.pgn.read_game(pgn)

    while game.next():
        game=game.next()
        moves.append(game.board().fen())
    
    pgn_list = []

    for move in moves:
        board = chess.Board(move)
        svg = chess.svg.board(board, size=350)
        pgn_list.append(svg.encode("utf-8").decode("utf-8")[:-2])


    return render_template("test.html", pgn_list=pgn_list, length=len(pgn_list))


@app.route("/board", methods=['GET', 'POST'])
@login_required
def board():
    form = PlayerForm()
    player = ''
    if form.validate_on_submit():
        player = form.player.data.upper()
    con = sqlite3.connect("/Users/polaparol/Documents/DS/Python/Flask-chess-webapp-main/instance/chessgames.db")
    cur = con.cursor()
    games = cur.execute(f'SELECT * FROM games WHERE To_show is not null AND (upper(White) like "{player}%" or  upper(Black) like "{player}%") LIMIT 20')
    return render_template('board.html', title='Chessboard', form=form, player=player, games=games)
