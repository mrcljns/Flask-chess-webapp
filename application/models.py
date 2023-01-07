from application import app, db, login_manager
from flask_login import UserMixin


@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))


class User(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(20), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password = db.Column(db.String(60), nullable=False)

    def __repr__(self):
        return f"User('{self.username}', '{self.email}')"


class Game(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key=True)
    player = db.Column(db.String(20), unique=False, nullable=False)
    piece_color = db.Column(db.String(20), unique=False, nullable=False)
    result = db.Column(db.String(20), unique=False, nullable=False)
    moves = db.Column(db.String(20), unique=False, nullable=False)

    def __repr__(self):
        return f"User('{self.player}', '{self.piece_color}', '{self.result}', '{self.moves}')"

with app.app_context():
    db.create_all()