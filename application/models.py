from application import app, login_manager
from flask_login import UserMixin
import sqlite3
import csv


@login_manager.user_loader
def load_user(user_id):
     conn = sqlite3.connect("instance/chessdb.db")
     curs = conn.cursor()
     curs.execute("SELECT * from user where id = (?)", [user_id])
     query = curs.fetchone()
     conn.commit()
     conn.close()
     if query:
          return User(username=query[1], email=query[2], password=query[3], year_of_birth=query[4], elo=query[5], title=query[6])
     else:
          return None


class User(UserMixin):
     def __init__(self, username, email, password, year_of_birth, elo, title):
          self.username = username
          self.email = email
          self.password = password
          self.year_of_birth = year_of_birth
          self.elo = elo
          self.title = title

     def is_active(self):
          return True

     def is_anonymous(self):
          return False

     def is_authenticated(self):
          return True

     def is_active(self):
          return True

     def get_id(self):
          conn = sqlite3.connect('instance/chessdb.db')
          curs = conn.cursor()
          curs.execute('SELECT id from user where username = (?)', [self.username])
          id = curs.fetchone()
          conn.commit()
          conn.close()
          return id[0]

     def __repr__(self):
          return f"('{self.username}', '{self.email}', '{self.password}', '{self.year_of_birth}', '{self.elo}', '{self.title}')"


class Game():
     def __init__(self, player, piece_color, result, moves, elo):
          self.player = player
          self.piece_color = piece_color
          self.result = result
          self.moves = moves
          self.elo = elo

     def __repr__(self):
          return f"('{self.player}', '{self.piece_color}', '{self.result}', '{self.moves}', '{self.elo}')"


with app.app_context():
     conn = sqlite3.connect("instance/chessdb.db")
     curs = conn.cursor()
     curs.execute('''
          CREATE TABLE IF NOT EXISTS user
          (id INTEGER PRIMARY KEY AUTOINCREMENT,
          username TEXT,
          email TEXT,
          password TEXT,
          year_of_birth INTEGER,
          elo INTEGER,
          title TEXT)
     ''')
     curs.execute('''CREATE TABLE IF NOT EXISTS game
          (id INTEGER PRIMARY KEY AUTOINCREMENT,
          player TEXT,
          piece_color TEXT,
          result TEXT,
          moves TEXT,
          elo INTEGER)''')
     curs.execute('''CREATE TABLE IF NOT EXISTS openings
          (id INTEGER PRIMARY KEY AUTOINCREMENT,
          name TEXT,
          moves TEXT)'''
     )
     curs.execute('''SELECT * FROM openings''')
     if curs.fetchall() == []:
          with open('data/openings.csv', 'r') as opening_df:
               df = csv.DictReader(opening_df)
               to_db = [(i['name'], i['moves']) for i in df]
               curs.executemany("INSERT INTO openings (name, moves) VALUES (?, ?);", to_db)

     conn.commit()
     conn.close()