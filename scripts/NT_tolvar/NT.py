
from asyncio import events
from pprint import pprint
import requests
import pandas as pd
from bs4 import BeautifulSoup as bs
import json
import re
from pathlib import Path
import datetime


######################################
#   Check if data file exist
######################################
newFile = False
my_file = Path("data/gameDayInfo.json")
if my_file.is_file():
    #If file already exist, update it.
    with open("data/gameDayInfo.json", 'r') as f:
        gameday_dict = json.load(f)
        # pprint.pprint(gameDayInfo)
        f.close()
else:
    newFile = True
    #Assemble all gameday datas into a dictionary of dictionaries for every day.
    gameday_dict = {}




######################################
#   Get NT data
######################################
# day_list = [1,2,3] #Where day 1 = Saturday, day 2 = sunday and day 3 is midweek, typically wednesday.
url = f'https://www.norsk-tipping.no/sport/tipping/spill?day={3}' #The day might as well be 1 or 2, does not matter ssince all info is preloaded to the webpage.
headers = {
    "User-Agent": "Mozilla/5.0 (X11; Ubuntu; Linux x86_64; rv:89.0) Gecko/20100101 Firefox/89.0",
}
r = requests.get(url, headers=headers)
soup = bs(r.content.decode('utf-8'),features="html.parser") #, "lxml" , parser="html.parser"
selected = soup.find(lambda tag:tag.name=='script' and 'PRELOADED_STATE' in tag.get_text())
selected_text = selected.get_text()
data = re.search(r'window\.__PRELOADED_STATE__ = ({.*});',selected_text).group(1)
data = json.loads(data)

sports_data_list = data["sport"]["sportGameInfo"]["tippingProduct"]["gameList"] # Returns a list of the three game days
for game_day in sports_data_list:
    # print(game_day)
    # print()
    ##### Get general data for the game day
    gameDayNo = game_day["gameDayNo"]
    gameDay = game_day["gameDay"]
    
    # Use the saleStop information as a trigger to check if there is any data available for the gameday
    try:
        saleStop = game_day["betObject"]["saleStop"]
    except KeyError as e:
        #Catch the error and just break the for loop for this day, hence keeping the old information.
        print(f"There is no data for day: {gameDay}")
        break
    
    sale_amount_full = game_day["betObject"]["saleAmount"]["fullTime"]
    sale_amount_half = game_day["betObject"]["saleAmount"]["halfTime"]
    try:
        bonus = game_day["bonusPot"][0]
    except:
        bonus = "No bonus found."
    # TODO: Add jackpot

    # Get betting distribution for each game, does not matter if the games are new or old.
    # TODO: What happens if this is empty? Will it throw an error? 
    for dists in game_day["betObject"]["tips"]["fullTime"]:
        if dists["tipType"] == "PEOPLE":
            people_tip_dict = dists["distribution"]   
    

    # Get games info
    newGames = {}
    game_counter = 1
    for event in game_day["betObject"]["events"]:
        # # Add game to pandas dataframe 
        # gd_df.loc[game_counter] = [event["eventName"], people_tip_dict[str(game_counter)][0], people_tip_dict[str(game_counter)][1], people_tip_dict[str(game_counter)][2]]
        # gd_info_df.loc[game_counter] = [game_day["gameDay"], event["sportName"], event["arrangementName"], event["eventName"], event["eventNo"], event["teamNames"]["home"]["name"], event["teamNames"]["away"]["name"], people_tip_dict[str(game_counter)][0], people_tip_dict[str(game_counter)][1], people_tip_dict[str(game_counter)][2]]
        game_dict = {
                "gameNr": event["eventNo"], 
                "game": event["eventName"],
                "arrangementName": event["arrangementName"],
                "home": event["teamNames"]["home"]["name"],
                "away": event["teamNames"]["away"]["name"],
                "eventTime": event["eventTime"],
                "SportName": event["sportName"],
                "dist": people_tip_dict[str(game_counter)],
                "diff": [0, 0, 0],
                "dist_original": people_tip_dict[str(game_counter)],
                "odds": {},
                "odds_original": {},
                "odds_diff": {},
                "status": event["matchStatus"]["status"]
        }
        newGames[event["eventName"]] = game_dict
        game_counter += 1



    # Do initial checks if data is already placed to see if it needs to be updated, changed or removed.
    if not newFile: #Hence, data is already in store
        # if saleStop != gameday_dict[gameDay]["saleStop"]: # If the sale stop of the day is different, then all info needs to be changed.
        #     # If salestop is new, overwrite current entry with the new data.
        #     gameday_dict[gameDay] = {
        #         "saleStop": saleStop,
        #         "saleAmountFullTime": sale_amount_full,
        #         "bonus": bonus,
        #         "games" : newGames
        #     }
        #     # TODO: Store the old data somewhere??
        # else:
        #     # If salestop is NOT new, then the data should be updated and not overwritten, actually it is betterto update/check and then overwrite such that new keys are added!
        #     gameday_dict[gameDay]["saleAmountFullTime"] = sale_amount_full
        #     game_count = 0 #Game counter to iterate through
        #     for idx, game in enumerate(newGames):                
        #         # print(f"Game from index: {gameday_dict[gameDay]['games'][idx]} and actual newGame: {newGames[game]['game']}")
        #         # gameday_dict[gameDay]["games"][game]["diff"] = [a_i - b_i for a_i, b_i in zip(newGames[game]["dist"], gameday_dict[gameDay]["games"][game]["dist_original"])]
        #         # gameday_dict[gameDay]["games"][game]["dist"] = newGames[game]["dist"]

        #         newGames[game]["diff"] = [a_i - b_i for a_i, b_i in zip(newGames[game]["dist"], gameday_dict[gameDay]["games"][game]["dist_original"])]
        #         newGames[game]["dist_original"] = gameday_dict[gameDay]["games"][game]["dist_original"]
            
        #     gameday_dict[gameDay] = {
        #         "saleStop": saleStop,
        #         "saleAmountFullTime": sale_amount_full,
        #         "bonus": bonus,
        #         "games" : newGames
        #     }

        if saleStop == gameday_dict[gameDay]["saleStop"]:
            for idx, game in enumerate(newGames):                
                # print(f"Game from index: {gameday_dict[gameDay]['games'][idx]} and actual newGame: {newGames[game]['game']}")
                # gameday_dict[gameDay]["games"][game]["diff"] = [a_i - b_i for a_i, b_i in zip(newGames[game]["dist"], gameday_dict[gameDay]["games"][game]["dist_original"])]
                # gameday_dict[gameDay]["games"][game]["dist"] = newGames[game]["dist"]

                newGames[game]["diff"] = [a_i - b_i for a_i, b_i in zip(newGames[game]["dist"], gameday_dict[gameDay]["games"][game]["dist_original"])]
                newGames[game]["dist_original"] = gameday_dict[gameDay]["games"][game]["dist_original"]
            
        gameday_dict[gameDay] = {
            "saleStop": saleStop,
            "saleAmountFullTime": sale_amount_full,
            "bonus": bonus,
            "games" : newGames
        }
    else:
        # If there is not a file to load, overload the whole gameday dictionary
        gameday_dict[gameDay] = {
                "saleStop": saleStop,
                "saleAmountFullTime": sale_amount_full,
                "bonus": bonus,
                "games" : newGames
            }
        

    # # Pandas data frame for GW.
    # gd_df = pd.DataFrame(columns=["Game", "H", "U", "B"])
    # gd_info_df = pd.DataFrame(columns=["Day", "Sport", "Arrangement", "Game", "GameNr", "HomeTeam", "AwayTeam", "H", "U", "B"])
    # print(gd_df)
    # print(gd_info_df)

######################################
#   Store updated data
######################################
with open("data/gameDayInfo.json", 'w') as f:
    json.dump(gameday_dict, f)
f.close()
# pprint(gameday_dict)

    # Gameday data to remote db.
    # gd_info_df.to_csv("data/"+gameDay+".csv", index=False)
    # db.storage.dataframes.put(gd_df, gameDay+"_print")
    # db.storage.dataframes.put(gd_info_df, gameDay+"_info")