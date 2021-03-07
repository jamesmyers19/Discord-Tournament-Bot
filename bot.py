import os
import mysql.connector
import json
from discord.ext import commands
from dotenv import load_dotenv
from datetime import date

load_dotenv()
TOKEN =os.getenv('DISCORD_TOKEN')
today = date.today()
today_fmt = today.strftime("%Y-%m-%d %H:%M:%S")

db = mysql.connector.connect(
    host="localhost",
    user="root",
    password=os.getenv('sqlpassword'),
    database="tourney_bot"
)

cursor = db.cursor()

bot = commands.Bot(command_prefix='!')

@bot.command(name='add_player', help='add a player to the database')
async def player_add(ctx, player_name):
    sql = "INSERT INTO player (name) VALUES (%s)"
    cursor.execute(sql, (str(player_name),))

    db.commit()

    await ctx.send('Player added to database!')

@bot.command(name='start_tournament', help='begin a new tournament')
async def tourney_start(ctx, number_of_players, number_of_rounds, *args):
    sql_sel = "SELECT * FROM player WHERE name = %s"

    sql2 = "INSERT INTO tournament (date, num_of_players, num_of_rounds) VALUES (%s, %s, %s)"
    val2 = (today_fmt,number_of_players,number_of_rounds,)
    cursor.execute(sql2, val2)
    db.commit()

    for player in args:
        cursor.execute(sql_sel, (player,))
        player_sql = cursor.fetchall()
        play_id = player_sql[0][0]
        play_name = player_sql[0][1]
        sql1 = "INSERT INTO player_tourney (tourney_date, player_id, name) VALUES (%s, %s, %s)"
        val1 = (today_fmt, play_id, play_name,)
        cursor.execute(sql1, val1)
        db.commit()
        
    await ctx.send('Tournament created!')

@bot.command(name='bye_round', help='record bye round for player')
async def bye(ctx, player_name):
    sql_sel1 = "SELECT * FROM player WHERE name = %s"
    cursor.execute(sql_sel1, (player_name,))
    player = cursor.fetchall()
    play_id = player[0][0]

    sql_sel2 = 'SELECT * from player_tourney WHERE name = %s and tourney_date = %s'
    val = (player_name, today_fmt,)
    cursor.execute(sql_sel2, val)
    tourney_player = cursor.fetchall()
    points = tourney_player[0][3]
    points += 3
    bye = tourney_player[0][5] 
    bye += 1
    rounds = tourney_player[0][4]
    rounds += 1
    winpct = ((points / 3) - bye) / rounds

    sql_points = "UPDATE player_tourney SET points = %s WHERE player_id = %s and tourney_date = %s"
    val_points = (points, play_id, today_fmt,)
    sql_bye = "UPDATE player_tourney SET bye_rounds = %s WHERE player_id = %s and tourney_date = %s"
    val_bye = (bye, play_id, today_fmt,)
    sql_rounds = "UPDATE player_tourney SET rounds_played = %s WHERE player_id = %s and tourney_date = %s"
    val_rounds = (rounds, play_id, today_fmt,)
    sql_winpct = "UPDATE player_tourney SET win_percent = %s WHERE player_id = %s and tourney_date = %s"
    val_winpct = (winpct, play_id, today_fmt,)

    cursor.execute(sql_points, val_points)
    db.commit()
    cursor.execute(sql_bye, val_bye)
    db.commit()
    cursor.execute(sql_rounds, val_rounds)
    db.commit()
    cursor.execute(sql_winpct, val_winpct)
    db.commit()

    await ctx.send('Bye round recorded')  

@bot.command(name='round_results', help='record winner and loser of a round')
async def round_results(ctx, winner, loser):
    sql_id = "SELECT * FROM player WHERE name = %s"
    cursor.execute(sql_id, (winner,))
    player1 = cursor.fetchall()
    winner_id = player1[0][0]
    cursor.execute(sql_id, (loser,))
    player2 = cursor.fetchall()
    loser_id = player2[0][0]

    sql_sel2 = 'SELECT * FROM player_tourney WHERE player_id = %s and tourney_date = %s'
    val_winner = (winner_id, today_fmt,)
    val_loser = (loser_id, today_fmt,)
    cursor.execute(sql_sel2, val_winner)
    round_winner = cursor.fetchall()
    winner_points = round_winner[0][3]
    winner_points += 3
    winner_rounds = round_winner[0][4]
    winner_rounds += 1
    winner_byes = round_winner[0][5]
    winner_winpct = ((winner_points / 3) - winner_byes) / winner_rounds

    cursor.execute(sql_sel2, val_loser)
    round_loser = cursor.fetchall()
    loser_points = round_loser[0][3]
    loser_rounds = round_loser[0][4]
    loser_rounds += 1
    loser_byes = round_loser[0][5]
    loser_winpct = ((loser_points / 3) - loser_byes) / loser_rounds
    
    sql_points = "UPDATE player_tourney SET points = %s WHERE player_id = %s and tourney_date = %s"
    val_points1 = (winner_points, winner_id, today_fmt,)
    val_points2 = (loser_points, loser_id, today_fmt,)
    sql_rounds = "UPDATE player_tourney SET rounds_played = %s WHERE player_id = %s and tourney_date = %s"
    val_rounds1 = (winner_rounds, winner_id, today_fmt,)
    val_rounds2 = (loser_rounds, loser_id, today_fmt,)
    sql_winpct = "UPDATE player_tourney SET win_percent = %s WHERE player_id = %s and tourney_date = %s"
    val_winpct1 = (winner_winpct, winner_id, today_fmt,)
    val_winpct2 = (loser_winpct, loser_id, today_fmt,)

    cursor.execute(sql_points, val_points1)
    db.commit()
    cursor.execute(sql_points, val_points2)
    db.commit()
    cursor.execute(sql_rounds, val_rounds1)
    db.commit()
    cursor.execute(sql_rounds, val_rounds2)
    db.commit()
    cursor.execute(sql_winpct, val_winpct1)
    db.commit()
    cursor.execute(sql_winpct, val_winpct2)
    db.commit()

@bot.command(name='round_results_tie', help="record a tie for each player")
async def round_results_tie(ctx, player1, player2):
    sql_id1 = "SELECT * from player WHERE name = %s"
    cursor.execute(sql_id1, (player1,))
    sql_player1 = cursor.fetchall()
    play_id1 = sql_player1[0][0]

    sql_id2 = "SELECT * from player WHERE name = %s"
    cursor.execute(sql_id1, (player2,))
    sql_player2 = cursor.fetchall()
    play_id2 = sql_player2[0][0]

    sql_sel1 = "SELECT * FROM player_tourney WHERE name = %s and tourney_date = %s"
    val1 = (player1, today_fmt,)
    cursor.execute(sql_sel1, val1)
    tourney_player1 = cursor.fetchall()
    points1 = tourney_player1[0][3]
    points1 += 1
    rounds1 = tourney_player1[0][4]
    rounds1 += 1
    byes1 = tourney_player1[0][5]
    winpct1 = ((points1 / 3) - byes1) / rounds1

    sql_sel2 = "SELECT * FROM player_tourney WHERE name = %s and tourney_date = %s"
    val2 = (player2, today_fmt,)
    cursor.execute(sql_sel1, val1)
    tourney_player2 = cursor.fetchall()
    points2 = tourney_player2[0][3]
    points2 += 1
    rounds2 = tourney_player2[0][4]
    rounds2 += 1
    byes2 = tourney_player2[0][5]
    winpct2 = ((points2 / 3) - byes2) / rounds2

    sql_points = "UPDATE player_tourney SET points = %s WHERE player_id = %s and tourney_date = %s"
    val_points1 = (points1, play_id1, today_fmt,)
    val_points2 = (points2, play_id2, today_fmt,)
    sql_rounds = "UPDATE player_tourney SET rounds_played = %s WHERE player_id = %s and tourney_date = %s"
    val_rounds1 = (rounds1, play_id1, today_fmt,)
    val_rounds2 = (rounds2, play_id2, today_fmt,)
    sql_winpct = "UPDATE player_tourney SET win_percent = %s WHERE player_id = %s and tourney_date = %s"
    val_winpct1 = (winpct1, play_id1, today_fmt,)
    val_winpct2 = (winpct2, play_id2, today_fmt,)

    cursor.execute(sql_points, val_points1)
    db.commit()
    cursor.execute(sql_points, val_points2)
    db.commit()
    cursor.execute(sql_rounds, val_rounds1)
    db.commit()
    cursor.execute(sql_rounds, val_rounds2)
    db.commit()
    cursor.execute(sql_winpct, val_winpct1)
    db.commit()
    cursor.execute(sql_winpct, val_winpct2)
    db.commit()

@bot.command(name='standings', help='display the rankings and points of each player')
async def standings(ctx):
    sql = 'SELECT * from player_tourney WHERE tourney_date = %s ORDER BY points DESC'
    cursor.execute(sql, (today_fmt,))
    player_standings = cursor.fetchall()
    standings_str = ''

    for player in player_standings:
        standings_str += player[2]
        standings_str += ' '
        standings_str += str(player[3])
        await ctx.send(standings_str)
        standings_str = ''

@bot.command(name='end_tournament', help='write the first place and second place players to tournament')
async def end_tourney(ctx):
    sql_sel = 'SELECT * from player_tourney WHERE tourney_date = %s ORDER BY points DESC'
    cursor.execute(sql_sel, (today_fmt,))
    player_standings = cursor.fetchall()
    sql_first = 'UPDATE tournament SET first_place = %s WHERE date = %s'
    sql_second = 'UPDATE tournament SET second_place = %s WHERE date = %s'
    val1 = (player_standings[0][2], today_fmt,)
    val2 = (player_standings[1][2], today_fmt,)

    cursor.execute(sql_first, val1)
    db.commit()

    cursor.execute(sql_second, val2)
    db.commit()  

    await ctx.send('Tournament ended! First and Second place recorded')  

bot.run(TOKEN)