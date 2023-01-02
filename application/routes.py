from application import app
from flask import render_template, request, url_for
import pandas as pd
import json
import plotly
import plotly_express as px
import sqlite3

@app.route("/")
def index():
    return render_template("index.html", title = "Home")

@app.route("/dashboard", methods=['GET', 'POST'])
def dashboard():
    with open('data/query1.sql', 'r') as sql_file:
        sql_script = sql_file.read()

    connection = sqlite3.connect('data/rating_ver2.db')

    openings_df = pd.read_sql_query(sql_script, connection)

    names = sorted(list(set(openings_df['name'])))

    selected_gm = request.form.get('selected-gm')

    # Graphs
    fig1 = px.bar(openings_df.query('name == @selected_gm'), x="Name:1", y='opening_count', title=f"{selected_gm} openings")

    graphlJSON = json.dumps(fig1, cls=plotly.utils.PlotlyJSONEncoder)

    connection.commit()
    connection.close()

    return render_template("index.html", title = "Dashboard", names=names, graphlJSON=graphlJSON, selected_gm=selected_gm)