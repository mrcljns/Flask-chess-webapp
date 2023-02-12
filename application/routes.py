from application import app, bcrypt
from application.queries import group_on_all, group_on_opening, elo_timeline
from application.forms import RegistrationForm, LoginForm, GameForm, UpdateAccountForm, PlayerForm, SelectCountry
from application.models import User, Game
from flask import render_template, request, url_for, flash, redirect
from flask_login import login_user, current_user, logout_user, login_required
import json
import plotly
import plotly_express as px
import chess.svg
import chess.pgn
from io import StringIO
import sqlite3
import numpy as np

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
        conn = sqlite3.connect('instance/chessdb.db')
        curs = conn.cursor()
        curs.execute(f"INSERT INTO user (username, email, password, year_of_birth, elo, title) VALUES {user}")
        conn.commit()
        conn.close()
        flash("Your account has been created! Welcome to ChesStats!", "success")
        return redirect(url_for("login"))

    return render_template('register.html', title='Register', form=form)


@app.route("/login", methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for("index"))

    form = LoginForm()

    if form.validate_on_submit():
        conn = sqlite3.connect('instance/chessdb.db')
        curs = conn.cursor()
        curs.execute("SELECT * FROM user WHERE email = (?)", [form.email.data])
        query = curs.fetchone()
        conn.commit()
        conn.close()
        if query:
            user = User(username=query[1], email=query[2], password=query[3], year_of_birth=query[4], elo=query[5], title=query[6])
            if user and bcrypt.check_password_hash(user.password, form.password.data):
                login_user(user, remember=form.remember.data)
                next_page = request.args.get('next')
                return redirect(next_page) if next_page else redirect(url_for('index'))
            else:
                flash('Login Unsuccessful. Please check email and password', 'danger')
        else:
            flash('Login Unsuccessful. No such email', 'danger')
    return render_template('login.html', title='Login', form=form)


@app.route("/logout")
def logout():
    logout_user()
    return redirect(url_for('index'))


@app.route("/callback", methods = ['POST', 'GET'])
def cb():
    return graph(chosen_user=request.args.get('user'), graph_type=request.args.get('graph_type'))


@app.route("/dashboard")
@login_required
def dashboard():
    return render_template('dashboard.html', title='Dashboard', 
    graphJSON=graph(chosen_user=current_user.username, graph_type="general"),
    logged_user=current_user.username)


def graph(chosen_user, graph_type="general"):

    if graph_type == "general":
        df = group_on_all(chosen_user = chosen_user)

        fig = px.bar(df, x='piece_color', y='count', color='result',
        labels={"piece_color": "Color of the pieces", "count": "Count", "result": "Result"}, title=f"{chosen_user} game stats",
        category_orders={"result": ["won", "lost", "draw"]})
        fig.update_xaxes(categoryorder='array', categoryarray= ['white', 'black'])
        fig.update_yaxes(fixedrange=False)
        fig.update_xaxes(categoryorder='total descending')
        
    elif graph_type == "opening":
        df = group_on_opening(chosen_user = chosen_user)

        fig = px.bar(df.sort_values('count', ascending=False), x='name', y='count', color='result',
        labels={"name": "Opening name", "count": "Count", "result": "Result"}, title=f"{chosen_user} opening stats",
        category_orders={"result": ["won", "lost", "draw"]})
        fig.update_yaxes(fixedrange=False)
        fig.update_xaxes(categoryorder='total descending')
    
    else:
        df = elo_timeline(chosen_user = chosen_user).reset_index(drop=True)
        df.index += 1

        fig = px.line(df.tail(10), y='elo', text='elo', markers=True,
        labels={"index": "Game", "elo": "Elo after game"}, 
        title=f"{chosen_user} elo timeline")

        fig.update_traces(textposition="top right")
        fig.update_layout(xaxis=dict(dtick = 1))
        fig.update_xaxes(rangemode="nonnegative")
        fig.update_layout(yaxis_range=[900, 4100])
        fig.update_layout(yaxis=dict(dtick = 500))

    graphJSON = json.dumps(fig, cls=plotly.utils.PlotlyJSONEncoder)

    return graphJSON


@app.route("/account", methods=['GET', 'POST'])
@login_required
def account():
    form = UpdateAccountForm()
    if form.validate_on_submit():
        conn = sqlite3.connect('instance/chessdb.db')
        curs = conn.cursor()
        curs.execute(f'''UPDATE game
        SET player = "{form.username.data}"
        WHERE player = "{current_user.username}"
        ''')
        curs.execute(f'''UPDATE user
        SET username = "{form.username.data}", email = "{form.email.data}", 
        elo = "{form.elo.data}", title = "{form.title.data}" 
        WHERE id = "{current_user.get_id()}"''')
        conn.commit()
        conn.close()
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
        pgn = StringIO(form.moves.data)
        pgn = chess.pgn.read_game(pgn)
        game_result = pgn.headers.get('Result')
        pgn = str(pgn[0])
        if game_result == "1-0":
            if form.piece_color.data=="white":
                current_user.elo += 100
                game = Game(player=current_user.username, piece_color="white", result="won", moves=pgn, 
                elo = np.clip(current_user.elo, 1000, 4000))
            else:
                current_user.elo -= 100
                game = Game(player=current_user.username, piece_color="black", result="lost", moves=pgn, 
                elo = np.clip(current_user.elo, 1000, 4000))
        elif game_result == "0-1":
            if form.piece_color.data=="white":
                current_user.elo -= 100
                game = Game(player=current_user.username, piece_color="white", result="lost", moves=pgn, 
                elo = np.clip(current_user.elo, 1000, 4000))
            else:
                current_user.elo += 100
                game = Game(player=current_user.username, piece_color="black", result="won", moves=pgn, 
                elo = np.clip(current_user.elo, 1000, 4000))
        elif game_result == "1/2-1/2":
            game = Game(player=current_user.username, piece_color=form.piece_color.data, result="draw", moves=pgn, 
            elo = np.clip(current_user.elo, 1000, 4000))
        elif form.result.data == "won":  
            current_user.elo += 100 
            game = Game(player=current_user.username, piece_color=form.piece_color.data, result=form.result.data, moves=pgn, 
            elo = np.clip(current_user.elo, 1000, 4000))
        elif form.result.data == "lost":
            current_user.elo -= 100 
            game = Game(player=current_user.username, piece_color=form.piece_color.data, result=form.result.data, moves=pgn, 
            elo = np.clip(current_user.elo, 1000, 4000))
        else:
            game = Game(player=current_user.username, piece_color=form.piece_color.data, result="draw", moves=pgn, 
            elo = np.clip(current_user.elo, 1000, 4000))


        conn = sqlite3.connect('instance/chessdb.db')
        curs = conn.cursor()
        curs.execute(f"INSERT INTO game (player, piece_color, result, moves, elo) VALUES {game}")
        curs.execute(f'''UPDATE user 
        SET elo = {np.clip(current_user.elo, 1000, 4000)}
        WHERE email = '{current_user.email}'
        ''')
        conn.commit()
        conn.close()
        flash('You have added a game!', 'success')
        return redirect(url_for('index'))
    return render_template('add_game.html', title='Add Game', form=form, legend='Add Game')


@app.route("/game/view", methods=['GET', 'POST'])
@login_required
def view_game():
    conn = sqlite3.connect('instance/chessdb.db')
    curs = conn.cursor()
    curs.execute(f"SELECT *, ROW_NUMBER() OVER (ORDER BY id ASC) FROM game WHERE player = '{current_user.username}'")
    games = curs.fetchall()
    conn.commit()
    conn.close()

    return render_template('game_table.html', data=games)


@app.route("/game/board", methods=['GET', 'POST'])
def game_board():

    moves = ['rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR']

    pgn = request.form.get('view')
    color = request.form.get('color')

    pgn = StringIO(pgn)
    
    game = chess.pgn.read_game(pgn)

    while game.next():
        game=game.next()
        moves.append(game.board().fen())
    
    pgn_list = []

    if color == "black":
        for move in moves:
            board = chess.Board(move)
            svg = chess.svg.board(board, flipped=True, size=350)
            pgn_list.append(svg.encode("utf-8").decode("utf-8")[:-2])
    else:
        for move in moves:
            board = chess.Board(move)
            svg = chess.svg.board(board, size=350)
            pgn_list.append(svg.encode("utf-8").decode("utf-8")[:-2])


    return render_template("game_board.html", pgn_list=pgn_list, length=len(pgn_list))


@app.route("/board", methods=['GET', 'POST'])
@login_required
def board():
    form = PlayerForm()
    player = ''
    if form.validate_on_submit():
        player = form.player.data.upper()
    con = sqlite3.connect("instance/chessgames.db")
    cur = con.cursor()
    games = cur.execute(f'SELECT * FROM games WHERE To_show is not null AND (upper(White) like "{player}%" or  upper(Black) like "{player}%") LIMIT 20')
    return render_template('board.html', title='Chessboard', form=form, player=player, games=games)


@app.route("/stats", methods=['GET', 'POST'])
@login_required
def stats():
    con = sqlite3.connect("instance/rating.db")
    cur = con.cursor()
    form = SelectCountry()
    country1 = 'POL'
    country2 = 'GER'
    statsData1 = []
    statsData2 = []

    if form.validate_on_submit():
        country1 = form.country1.data.upper()
        country2 = form.country2.data.upper()
    else:
        form.country1.data = country1
        form.country2.data = country2


    statsData1.append(['Best 3 players (classical rating)',
        list(cur.execute(f"SELECT id_number, name, standard_rating FROM player WHERE fed = '{country1}'  ORDER BY standard_rating DESC LIMIT 3")),
        list(cur.execute(f"SELECT id_number, name, standard_rating FROM player WHERE fed = '{country2}'  ORDER BY standard_rating DESC LIMIT 3"))])
    statsData1.append(['Best 3 female players (classical rating)',
        list(cur.execute(f"SELECT id_number, name, standard_rating FROM player WHERE fed = '{country1}' AND sex = 'F' ORDER BY standard_rating DESC LIMIT 3")),
        list(cur.execute(f"SELECT id_number, name, standard_rating FROM player WHERE fed = '{country2}' AND sex = 'F' ORDER BY standard_rating DESC LIMIT 3"))])
    statsData1.append(['Best 3 junior players (classical rating)',
        list(cur.execute(f"SELECT id_number, name, standard_rating FROM player WHERE fed = '{country1}' AND born_year >= 2005 ORDER BY standard_rating DESC LIMIT 3")),
        list(cur.execute(f"SELECT id_number, name, standard_rating FROM player WHERE fed = '{country2}' AND born_year >= 2005 ORDER BY standard_rating DESC LIMIT 3"))])
    statsData1.append(['Best 3 female junior players (classical rating)',
        list(cur.execute(f"SELECT id_number, name, standard_rating FROM player WHERE fed = '{country1}' AND sex = 'F' AND born_year >= 2005 ORDER BY standard_rating DESC LIMIT 3")),
        list(cur.execute(f"SELECT id_number, name, standard_rating FROM player WHERE fed = '{country2}' AND sex = 'F' AND born_year >= 2005 ORDER BY standard_rating DESC LIMIT 3"))])

    statsData1.append(['Best 3 players (rapid rating)',
        list(cur.execute(f"SELECT id_number, name, standard_rating FROM player WHERE fed = '{country1}'  ORDER BY rapid_rating DESC LIMIT 3")),
        list(cur.execute(f"SELECT id_number, name, standard_rating FROM player WHERE fed = '{country2}'  ORDER BY rapid_rating DESC LIMIT 3"))])
    statsData1.append(['Best 3 female players (rapid rating)',
        list(cur.execute(f"SELECT id_number, name, standard_rating FROM player WHERE fed = '{country1}' AND sex = 'F' ORDER BY rapid_rating DESC LIMIT 3")),
        list(cur.execute(f"SELECT id_number, name, standard_rating FROM player WHERE fed = '{country2}' AND sex = 'F' ORDER BY rapid_rating DESC LIMIT 3"))])
    statsData1.append(['Best 3 junior players (rapid rating)',
        list(cur.execute(f"SELECT id_number, name, standard_rating FROM player WHERE fed = '{country1}' AND born_year >= 2005 ORDER BY rapid_rating DESC LIMIT 3")),
        list(cur.execute(f"SELECT id_number, name, standard_rating FROM player WHERE fed = '{country2}' AND born_year >= 2005 ORDER BY rapid_rating DESC LIMIT 3"))])
    statsData1.append(['Best 3 female junior players (rapid rating)',
        list(cur.execute(f"SELECT id_number, name, standard_rating FROM player WHERE fed = '{country1}' AND sex = 'F' AND born_year >= 2005 ORDER BY rapid_rating DESC LIMIT 3")),
        list(cur.execute(f"SELECT id_number, name, standard_rating FROM player WHERE fed = '{country2}' AND sex = 'F' AND born_year >= 2005 ORDER BY rapid_rating DESC LIMIT 3"))])
    
    statsData1.append(['Best 3 players (blitz rating)',
        list(cur.execute(f"SELECT id_number, name, standard_rating FROM player WHERE fed = '{country1}'  ORDER BY blitz_rating DESC LIMIT 3")),
        list(cur.execute(f"SELECT id_number, name, standard_rating FROM player WHERE fed = '{country2}'  ORDER BY blitz_rating DESC LIMIT 3"))])
    statsData1.append(['Best 3 female players (blitz rating)',
        list(cur.execute(f"SELECT id_number, name, standard_rating FROM player WHERE fed = '{country1}' AND sex = 'F' ORDER BY blitz_rating DESC LIMIT 3")),
        list(cur.execute(f"SELECT id_number, name, standard_rating FROM player WHERE fed = '{country2}' AND sex = 'F' ORDER BY blitz_rating DESC LIMIT 3"))])
    statsData1.append(['Best 3 junior players (blitz rating)',
        list(cur.execute(f"SELECT id_number, name, standard_rating FROM player WHERE fed = '{country1}' AND born_year >= 2005 ORDER BY blitz_rating DESC LIMIT 3")),
        list(cur.execute(f"SELECT id_number, name, standard_rating FROM player WHERE fed = '{country2}' AND born_year >= 2005 ORDER BY blitz_rating DESC LIMIT 3"))])
    statsData1.append(['Best 3 female junior players (blitz rating)',
        list(cur.execute(f"SELECT id_number, name, standard_rating FROM player WHERE fed = '{country1}' AND sex = 'F' AND born_year >= 2005 ORDER BY blitz_rating DESC LIMIT 3")),
        list(cur.execute(f"SELECT id_number, name, standard_rating FROM player WHERE fed = '{country2}' AND sex = 'F' AND born_year >= 2005 ORDER BY blitz_rating DESC LIMIT 3"))])
 
    statsData2.append(['Number of Females',
        list(cur.execute(f"SELECT count(*) FROM player WHERE fed = '{country1}' AND sex = 'F'  ORDER BY standard_rating DESC ")),
        list(cur.execute(f"SELECT count(*) FROM player WHERE fed = '{country2}' AND sex = 'F'  ORDER BY standard_rating DESC "))
        ])
    statsData2.append(['Number of Males',
        list(cur.execute(f"SELECT count(*) FROM player WHERE fed = '{country1}' AND sex = 'M'  ORDER BY standard_rating DESC ")),
        list(cur.execute(f"SELECT count(*) FROM player WHERE fed = '{country2}' AND sex = 'M'  ORDER BY standard_rating DESC "))
        ])
    statsData2.append(['Number of junior Females',
        list(cur.execute(f"SELECT count(*) FROM player WHERE fed = '{country1}' AND sex = 'F' AND born_year >= 2005 ORDER BY standard_rating DESC ")),
        list(cur.execute(f"SELECT count(*) FROM player WHERE fed = '{country2}' AND sex = 'F' AND born_year >= 2005 ORDER BY standard_rating DESC "))
        ])
    statsData2.append(['Number of junior Males',
        list(cur.execute(f"SELECT count(*) FROM player WHERE fed = '{country1}' AND sex = 'M' AND born_year >= 2005 ORDER BY standard_rating DESC ")),
        list(cur.execute(f"SELECT count(*) FROM player WHERE fed = '{country2}' AND sex = 'M' AND born_year >= 2005 ORDER BY standard_rating DESC "))
        ])

    statsData2.append(['Number of GM',
        list(cur.execute(f"SELECT count(*) FROM player WHERE fed = '{country1}' AND title = 'GM'  ORDER BY standard_rating DESC ")),
        list(cur.execute(f"SELECT count(*) FROM player WHERE fed = '{country2}' AND title = 'GM'  ORDER BY standard_rating DESC "))
        ])
    statsData2.append(['Number of IM',
        list(cur.execute(f"SELECT count(*) FROM player WHERE fed = '{country1}' AND title = 'IM'  ORDER BY standard_rating DESC ")),
        list(cur.execute(f"SELECT count(*) FROM player WHERE fed = '{country2}' AND title = 'IM'  ORDER BY standard_rating DESC "))
        ])
    statsData2.append(['Number of FM',
        list(cur.execute(f"SELECT count(*) FROM player WHERE fed = '{country1}' AND title = 'FM'  ORDER BY standard_rating DESC ")),
        list(cur.execute(f"SELECT count(*) FROM player WHERE fed = '{country2}' AND title = 'FM'  ORDER BY standard_rating DESC "))
        ])
    statsData2.append(['Number of CM',
        list(cur.execute(f"SELECT count(*) FROM player WHERE fed = '{country1}' AND title = 'IM'  ORDER BY standard_rating DESC ")),
        list(cur.execute(f"SELECT count(*) FROM player WHERE fed = '{country2}' AND title = 'IM'  ORDER BY standard_rating DESC "))
        ])
    
    statsData2.append(['Number of WGM',
        list(cur.execute(f"SELECT count(*) FROM player WHERE fed = '{country1}' AND title = 'GM'  ORDER BY standard_rating DESC ")),
        list(cur.execute(f"SELECT count(*) FROM player WHERE fed = '{country2}' AND title = 'GM'  ORDER BY standard_rating DESC "))
        ])
    statsData2.append(['Number of WIM',
        list(cur.execute(f"SELECT count(*) FROM player WHERE fed = '{country1}' AND title = 'IM'  ORDER BY standard_rating DESC ")),
        list(cur.execute(f"SELECT count(*) FROM player WHERE fed = '{country2}' AND title = 'IM'  ORDER BY standard_rating DESC "))
        ])
    statsData2.append(['Number of WFM',
        list(cur.execute(f"SELECT count(*) FROM player WHERE fed = '{country1}' AND title = 'FM'  ORDER BY standard_rating DESC ")),
        list(cur.execute(f"SELECT count(*) FROM player WHERE fed = '{country2}' AND title = 'FM'  ORDER BY standard_rating DESC "))
        ])
    statsData2.append(['Number of WCM',
        list(cur.execute(f"SELECT count(*) FROM player WHERE fed = '{country1}' AND title = 'IM'  ORDER BY standard_rating DESC ")),
        list(cur.execute(f"SELECT count(*) FROM player WHERE fed = '{country2}' AND title = 'IM'  ORDER BY standard_rating DESC "))
        ])
   

    countries1 = list(cur.execute(f'SELECT code, name FROM federation ORDER BY name'))
    countries2 = list(cur.execute(f'SELECT code, name FROM federation ORDER BY name'))

    con.commit()
    con.close()

    return render_template('stats.html', title='Chessboard', form=form, countries1 = countries1, countries2 = countries2, statsData1=statsData1, statsData2=statsData2)