import sqlite3
import pandas as pd

def db_connect(func):
    def _db_connect(*args, **kwargs):
        conn = sqlite3.connect("instance/chessdb.db")
        curs = conn.cursor()
        result = func(curs, *args, **kwargs)
        conn.commit()
        conn.close()
        return result
    return _db_connect


@db_connect
def group_on_all(curs, chosen_user):
    result = curs.execute(f'''
    SELECT *, Count(*) as count 
    FROM game
    GROUP BY player, piece_color, result
    HAVING player = "{chosen_user}"
    ''')
    df = pd.DataFrame(result.fetchall(), columns = [desc[0] for desc in result.description])
    return df

@db_connect
def group_on_opening(curs, chosen_user):
    result = curs.execute(f'''
        WITH top_openings as (
        SELECT name, COUNT(*) as opening_count
        FROM (
        SELECT *, RANK() OVER (PARTITION BY x.ID ORDER BY LENGTH(y.moves) DESC) as oprank
        FROM game as x
        LEFT JOIN openings as y
        ON x.moves LIKE y.moves || '%'
        )
        WHERE player=='{chosen_user}' and oprank==1
        GROUP BY player, name
        ORDER BY opening_count DESC
        LIMIT 5
        )

        SELECT a.player, a.result, a.name, a.count
        FROM (
        SELECT player, result, name, COUNT(*) as count
        FROM (
            SELECT x.id, player, piece_color, result, name, y.moves, RANK() OVER (PARTITION BY x.ID ORDER BY LENGTH(y.moves) DESC) as oprank
            From game as x
            LEFT JOIN openings as y
            ON x.moves LIKE y.moves || '%'
        )
        WHERE oprank==1 AND name not null
        GROUP BY player, result, name
        HAVING player = '{chosen_user}'
        ) as a
        INNER JOIN top_openings as b
        ON a.name=b.name
    ''')
    df = pd.DataFrame(result.fetchall(), columns = [desc[0] for desc in result.description])
    return df

@db_connect
def elo_timeline(curs, chosen_user):
    result = curs.execute(f'''
    SELECT id, player, elo
    FROM game
    WHERE player = "{chosen_user}"
    ORDER BY id
    ''')
    df = pd.DataFrame(result.fetchall(), columns = [desc[0] for desc in result.description])
    return df