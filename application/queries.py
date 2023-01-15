def group_on_all():
    return '''
    SELECT *, Count(*) as count 
    FROM game
    GROUP BY player, piece_color, result
    '''

def group_on_opening():
    return '''
    SELECT player, piece_color, result, name, COUNT(*) as count
    FROM (
        SELECT id, player, piece_color, result, name, y.moves, RANK() OVER (PARTITION BY ID ORDER BY LENGTH(y.moves) DESC) as oprank
        From game as x
        LEFT JOIN openings as y
        ON x.moves LIKE y.moves || '%'
        )
    WHERE oprank==1 AND name not null
    GROUP BY player, piece_color, result, name
    '''