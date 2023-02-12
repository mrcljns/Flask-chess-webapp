# Flask-chess-webapp
This is the final project for the Python and SQL course I did during my masters degree. It is a webapp that enables registering, adding chess games in a .png format, viewing games on a chessboard and analyzing your performance on graphs.

# Guide
* It is not necessary to download the chessdb.db file. If it is absent, running the webapp automatically creates an empty database with only the openings table filled out.
* The jupyter notebooks create two databases used for analyzing chosen games of grandmasters. Without running them, certain functionalities of the webapp will not work.

# Requirements:
* chess==1.9.3
* Flask==1.1.2
* Flask_Bcrypt==1.0.1
* Flask_Login==0.6.2
* Flask_WTF==1.0.1
* numpy==1.21.5
* pandas==1.4.4
* plotly==5.9.0
* plotly_express==0.4.1
* WTForms==3.0.1
