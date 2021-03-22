import os
import mysql.connector
import json
from discord.ext import commands
from dotenv import load_dotenv
from datetime import date

# Create global variables
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
sql_ins_tourney = 'INSERT INTO tournament (date, num_of_players, num_of_rounds) VALUES (%s, %s, %s,)'
sql_ins_player_tourney = 'INSERT INTO player_tourney (tourney_date, player_id, name) VALUES (%s, %s, %s)'

# Create player class
class Player:
    def __init__(self, sql_id, name, points):
        self.sql_id = sql_id
        self.name = name
        self.points = points

class Player_tourney:
    def __init__(self, date, sql_id, name, points, rounds_played, bye_rounds, win_percent):
        self.date = date
        self.sql_id = sql_id
        self.name = name
        self.points = points
        self.rounds_played = rounds_played
        self.bye_rounds = bye_rounds
        self.win_percent = win_percent

class Tourney:
    def __init__(self, date, sql_num_of_players, num_of_rounds, first_place, second_place):
        self.date = date
        self.sql_num_of_players = sql_num_of_players
        self.num_of_rounds = num_of_rounds
        self.first_place = first_place
        self.second_place = second_place

def update_player_tourney(date, play_id, points, bye, rounds, winpct):
    sql_points = "UPDATE player_tourney SET points = %s WHERE player_id = %s and tourney_date = %s"
    val_points = (points, play_id, date,)
    sql_bye = "UPDATE player_tourney SET bye_rounds = %s WHERE player_id = %s and tourney_date = %s"
    val_bye = (bye, play_id, date,)
    sql_rounds = "UPDATE player_tourney SET rounds_played = %s WHERE player_id = %s and tourney_date = %s"
    val_rounds = (rounds, play_id, date,)
    sql_winpct = "UPDATE player_tourney SET win_percent = %s WHERE player_id = %s and tourney_date = %s"
    val_winpct = (winpct, play_id, date,)

    cursor.execute(sql_points, val_points)
    db.commit()
    cursor.execute(sql_bye, val_bye)
    db.commit()
    cursor.execute(sql_rounds, val_rounds)
    db.commit()
    cursor.execute(sql_winpct, val_winpct)
    db.commit()

def get_player_info(name):
    sql_sel_from_player = 'SELECT * FROM player WHERE name = %s'
    cursor.execute(sql_sel_from_player, (name,))
    player_info = cursor.fetchall()
    player = Player(player_info[0][0], player_info[0][1], player_info[0][2])
    return player

def get_player_tourney_info(name, date):
    sql_sel_player_tourney = 'SELECT * from player_tourney WHERE name = %s and tourney_date = %s'
    player_tourney_val = (name, date,)
    cursor.execute(sql_sel_player_tourney, player_tourney_val)
    player_tourney_info = cursor.fetchall()
    player_tourney = Player_tourney(player_tourney_info[0][0], player_tourney_info[0][1], player_tourney_info[0][2], player_tourney_info[0][3], player_tourney_info[0][4], player_tourney_info[0][5], 0.0)
    return player_tourney

@bot.command(name='add_player', help='add a player to the database')
async def player_add(ctx, player_name):
    sql_player_insert = "INSERT INTO player (name) VALUES (%s)"
    cursor.execute(sql_player_insert, (str(player_name),))
    db.commit()

    await ctx.send('Player added to database!')

@bot.command(name='start_tournament', help='begin a new tournament')
async def tourney_start(ctx, number_of_players, number_of_rounds, *args):
    sql_start_tourney = 'INSERT INTO tournament (date, num_of_players, num_of_rounds) VALUES (%s, %s, %s)'
    tourney_start_val= (today_fmt,number_of_players,number_of_rounds,)
    cursor.execute(sql_start_tourney, tourney_start_val)
    db.commit()

    for player in args:
        new_player = get_player_info(player)
        player_tourney_val = (today_fmt, new_player.sql_id, new_player.name,)
        cursor.execute(sql_ins_player_tourney, player_tourney_val)
        db.commit()
        
    await ctx.send('Tournament created!')

@bot.command(name='bye_round', help='record bye round for player')
async def bye(ctx, player_name):
    bye_player = get_player_info(player_name)
    bye_player_tourney = get_player_tourney_info(bye_player.name, today_fmt)
    bye_player_tourney.points += 3
    bye_player_tourney.bye_rounds += 1
    bye_player_tourney.rounds_played += 1
    bye_player_tourney.win_percent = ((bye_player_tourney.points / 3) - bye_player_tourney.bye_rounds) / bye_player_tourney.rounds_played

    update_player_tourney(today_fmt, bye_player_tourney.sql_id, bye_player_tourney.points, bye_player_tourney.bye_rounds, bye_player_tourney.rounds_played, bye_player_tourney.win_percent)

    await ctx.send('Bye round recorded')  

@bot.command(name='round_results', help='record winner and loser of a round')
async def round_results(ctx, winner, loser):
    winner_player = get_player_info(winner)
    loser_player = get_player_info(loser)

    round_winner = get_player_tourney_info(winner_player.name, today_fmt)

    round_winner.points += 3
    round_winner.rounds_played += 1
    round_winner.win_percent = ((round_winner.points / 3) - round_winner.bye_rounds) / round_winner.rounds_played
    
    round_loser = get_player_tourney_info(loser_player.name, today_fmt)
    round_loser.rounds_played += 1
    round_loser.win_percent = ((round_loser.points / 3) - round_loser.bye_rounds) / round_loser.rounds_played
    
    update_player_tourney(today_fmt, round_winner.sql_id, round_winner.points, round_winner.bye_rounds, round_winner.rounds_played, round_winner.win_percent)
    update_player_tourney(today_fmt, round_loser.sql_id, round_loser.points, round_loser.bye_rounds, round_loser.rounds_played, round_loser.win_percent)

    await ctx.send('Round recorded')

@bot.command(name='round_results_tie', help="record a tie for each player")
async def round_results_tie(ctx, player1, player2):
    round_player1 = get_player_info(player1)
    round_player2 = get_player_info(player2)
    player_tourney1 = get_player_tourney_info(round_player1.name, today_fmt)
    player_tourney2 = get_player_tourney_info(round_player2.name, today_fmt)

    player_tourney1.points += 1
    player_tourney1.rounds_played += 1
    player_tourney1.win_percent = ((player_tourney1.points / 3) - player_tourney1.bye_rounds) / player_tourney1.rounds_played

    player_tourney2.points += 1
    player_tourney2.rounds_played += 1
    player_tourney2.win_percent = ((player_tourney2.points / 3) - player_tourney2.bye_rounds) / player_tourney2.rounds_played

    update_player_tourney(today_fmt, player_tourney1.sql_id, player_tourney1.points, player_tourney1.bye_rounds, player_tourney1.rounds_played, player_tourney1.win_percent)
    update_player_tourney(today_fmt, player_tourney2.sql_id, player_tourney2.points, player_tourney2.bye_rounds, player_tourney2.rounds_played, player_tourney2.win_percent)

    await ctx.send('Tie recorded')

@bot.command(name='standings', help='display the rankings and points of each player')
async def standings(ctx):
    sql = 'SELECT * from player_tourney WHERE tourney_date = %s ORDER BY points DESC, win_percent DESC'
    cursor.execute(sql, (today_fmt,))
    player_standings = cursor.fetchall()
    standings_str = ''

    for player in player_standings:
        standings_str += player[2]
        standings_str += ' Points: '
        standings_str += str(player[3])
        standings_str += ' Win Percent: '
        standings_str += str(player[6])
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