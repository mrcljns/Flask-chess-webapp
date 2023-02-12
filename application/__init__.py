from flask import Flask
from flask_bcrypt import Bcrypt
from flask_login import LoginManager

app = Flask(__name__)
app.config['SECRET_KEY'] = 'bce2711492820cc80963590f8c93953c'
<<<<<<< HEAD
=======
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///chessdb.db'
>>>>>>> 541bba07f035b699ccbcce133fd5098240c8b29d
bcrypt = Bcrypt(app)
login_manager = LoginManager(app)
login_manager.login_view = 'login'
login_manager.login_message_category = 'info'

from application import routes