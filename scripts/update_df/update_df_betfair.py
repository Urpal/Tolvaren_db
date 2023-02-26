import json
import pandas as pd
import numpy as np
import datetime
from dateutil import parser
import pprint

# # Utilities:
# def clamp(n, minn, maxn):
#     return max(min(maxn, n), minn)

######################################
#   Load data from json and get closest match day TODO: Move this to a variable? 
######################################
with open("data/gameDayInfo.json", 'r') as f:
    gameday_dict = json.load(f)
# pprint.pprint(gameday_dict)
f.close()

closest_matchday = "MIDWEEK"
time_diff = 60*60*24*7
time_now = datetime.datetime.utcnow().replace(tzinfo=datetime.timezone.utc)
for game_day in gameday_dict:
    difference = (parser.parse(gameday_dict[game_day]["saleStop"]) - time_now).total_seconds()
    # print(f"time Diff: {difference}")
    if difference < time_diff and parser.parse(gameday_dict[game_day]["saleStop"]) > time_now:
        closest_matchday = game_day
        time_diff = difference

columns=["GameNr","Game", "H_folk", "U_folk", "B_folk","H_folk_change", "U_folk_change", "B_folk_change",
         "H_mean", "U_mean", "B_mean", "H_mean_change", "U_mean_change", "B_mean_change" , "H_valu", "U_valu", "B_valu",
         "tip"]

data = []
# game_counter = 0
for gameName, game in gameday_dict[closest_matchday]["games"].items():
    
    h_mean, h_imp,  u_mean, u_imp, b_mean, b_imp, h_diff, u_diff, b_diff = [0] * 9 #Init datafram variables to zero.

    # Check if there is any odds at all.
    if 'odds' in game.keys():
       
        # Find the mean and implied value of the entries
        h_mean = game['odds'][0]
        h_imp = (1/h_mean)*100
        u_mean = game['odds'][1]
        u_imp = (1/u_mean)*100
        b_mean = game['odds'][2]
        b_imp = (1/b_mean)*100

        h_mean_old = game['odds_original'][0]
        h_diff = h_mean - h_mean_old
        u_mean_old = game['odds_original'][1]
        u_diff = u_mean - u_mean_old
        b_mean_old = game['odds_original'][2]
        b_diff = b_mean - b_mean_old

    # If no odds is available, then set implied values equal to the distribution of the people.
    else:
        h_imp = game["dist"][0]
        u_imp = game["dist"][1]
        b_imp = game["dist"][2]
    
    # Get values:
    h_valu = h_imp-game["dist"][0]
    u_valu = u_imp-game["dist"][1]
    b_valu = b_imp-game["dist"][2]

    # Calculate tip TODO: This was just something quick and dirty :P This should be properly defined in a formula ;) 
    if b_valu >= 10 and b_mean <= 3:
        tip = "B"
    elif u_valu >= 10 and u_mean <= 3.65:
        tip = "U"
    elif h_valu >= 10 and h_mean <= 3:
        tip = "H"
    else:
        tip = "B"
        best_valu = b_valu
        if u_valu > best_valu:
            tip = "U"
            best_valu = u_valu
        if h_valu > best_valu:
            tip = "H"

    # data[game_counter] = [game["gameNr"], game["game"], game["dist"][0], game["dist"][1], game["dist"][2],
    #                     h_mean, u_mean, b_mean, h_imp-game["dist"][0], u_imp-game["dist"][1], b_imp-game["dist"][2]]
    data.append([game["gameNr"], game["game"], game["dist"][0], game["dist"][1], game["dist"][2],
                game["diff"][0], game["diff"][1], game["diff"][2], h_mean, u_mean, b_mean,
                h_diff, u_diff, b_diff, h_valu, u_valu, b_valu, tip])
df = pd.DataFrame(data=data,columns=columns)#, index = "GameNr")
print(df)
# TODO: Decide on how this should be shared. Should this one spin in the background? Be triggered? Or on input.

