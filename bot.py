import os
from random import randint
import mysql.connector
from discord.ext import commands
from dotenv import load_dotenv
from datetime import date

load_dotenv()
TOKEN =os.getenv('DISCORD_TOKEN')
today = date.today()
todayFmt = today.strftime("%Y-%m-%d %H:%M:%S")
playerDict = {}
currentRound = 1

db = mysql.connector.connect(
    host="localhost",
    user="root",
    password=os.getenv('sqlpassword'),
    database="tournament_bot"
)

cursor = db.cursor()

bot = commands.Bot(command_prefix ='!')

def bye(name):
    playerDict[name]["byes"] += 1
    playerDict[name]["points"] += 3

def calcOppWinPct(player):
    totalRounds = 0
    totalWins = 0
    for opponent in playerDict[player]['opponents']:
        totalRounds += playerDict[opponent]['rounds']
        totalWins += ((playerDict[opponent]['points'] - (playerDict[opponent]['byes'] * 3)) / 3)

    playerDict[player]['oppWinPct'] = totalWins / totalRounds


@bot.command(name='addPlayer', help='add a player to the database')
async def playerAdd(ctx, firstName, lastName, untapName):
    sqlIns = "INSERT INTO player (firstName, lastName, untapName) VALUES (%s, %s, %s)"
    cursor.execute(sqlIns, (str(firstName),str(lastName),str(untapName),))

    db.commit()

    await ctx.send('Player added to database!')

@bot.command(name='start', help='Start the tournament by supplying players untap name')
async def startTournament(ctx, *args):
    sqlSel = "SELECT * from player where untapName = %s"
    playersStr = ""
    for player in args:
        cursor.execute(sqlSel, (str(player),))
        playerSql = cursor.fetchall()
        playerDict[playerSql[0][3]] = {"id" : playerSql[0][0], "firstName" : playerSql[0][1], "lastName" : playerSql[0][2], "untapName" : playerSql[0][3], "points" : 0, "rounds" : 0, "byes" : 0, "oppWinPct" : 0.0, "opponents" : []}
        playersStr = playersStr + playerSql[0][3] + ", "
    
    sqlIns = "INSERT INTO tournament (date, players) VALUES (%s, %s)"
    cursor.execute(sqlIns, (todayFmt, playersStr,))

    db.commit()

    await ctx.send('Tournament started! Date and players recorded in database.')

@bot.command(name='pair', help='Pair round with current players, first round is random following rounds are paired by score avoiding duplicates')
async def pairRound(ctx):
    global currentRound
    if currentRound == 1:
        playerList = list(playerDict)
        while len(playerList) != 0:
            if len(playerList) == 1:
                await ctx.send(playerList[0] + " has the bye")
                bye(playerList[0])
                playerList.remove(playerList[0])
            else:
                random1 = randint(0, len(playerList)-1)
                random2 = randint(0, len(playerList)-1)
                while random1 == random2:
                    random2 = randint(0, len(playerList)-1)

                player1 = playerList[random1]
                player2 = playerList[random2]

                playerDict[player1]["opponents"].append(player2)
                playerDict[player1]["rounds"] += 1

                playerDict[player2]["opponents"].append(player1)
                playerDict[player2]["rounds"] += 1

                await ctx.send(player1 + " vs. " + player2)

                playerList.remove(player1)
                playerList.remove(player2)
        
        currentRound += 1

    else:
        sortPlayerDict = sorted(playerDict, key=lambda x: (playerDict[x]['points']), reverse=True)
        playerList = list(sortPlayerDict)
        while len(playerList) != 0:
            index = 0
            player1 = playerList[0]

            if len(playerList) == 1:
                await ctx.send(playerList[0] + " has the bye")
                bye(playerList[0])
                playerList.remove(playerList[0])
            else:
                while(index == 0 or playerList[index] in playerDict[player1]["opponents"]):
                    index += 1

                player2 = playerList[index]
            
                playerDict[player1]["opponents"].append(player2)
                playerDict[player1]["rounds"] += 1

                playerDict[player2]["opponents"].append(player1)
                playerDict[player2]["rounds"] += 1

                await ctx.send(player1 + " vs. " + player2)

                playerList.remove(player1)
                playerList.remove(player2)
        
        currentRound += 1

@bot.command(name='record', help='record results of round pairing. Winner untap name Loser untap name yes/no for tie (order does not matter in tie)')
async def recordRound(ctx, winner, loser, tie):
    if str(tie) == 'yes' or str(tie) == 'Yes':
        playerDict[winner]["points"] += 1
        playerDict[loser]["points"] += 1
    
    else:
        playerDict[winner]["points"] += 1

    await ctx.send("Match recorded!")

@bot.command(name='standings', help='Print the current standings to discord chat')
async def standings(ctx):
    playerList = list(playerDict)

    for player in playerList:
        calcOppWinPct(player)

    sortPlayerDict = sorted(playerDict, key=lambda x: (playerDict[x]['points'], playerDict[x]['oppWinPct']), reverse=True)

    await ctx.send("The standings are as follows:")
    for player in sortPlayerDict:
        await ctx.send(player)

@bot.command(name="end", help="End the tournament and record standings to database")
async def endTournament(ctx):
    standingsStr = ""
    sortPlayerDict = sorted(playerDict, key=lambda x: (playerDict[x]['points'], playerDict[x]['oppWinPct']), reverse=True)

    for player in sortPlayerDict:
        standingsStr += player + ', '

    sqlUpdate = 'UPDATE tournament Set standings = %s WHERE date = %s'
    cursor.execute(sqlUpdate, (standingsStr, todayFmt,))

    db.commit()

    await ctx.send('Tournament standings recorded in database!')

bot.run(TOKEN)