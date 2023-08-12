# Defining dataclasses
from dataclasses import dataclass
from typing import Optional, List, Dict
import datetime


@dataclass
class Game:
    game_nr: Optional[int] = None
    game_str: Optional[str] = None
    home_team: Optional[str] = None
    away_team: Optional[str] = None
    arrangement_name: Optional[str] = None
    event_time: Optional[str] = None
    sport_name: Optional[str] = None
    status: Optional[str] = None

    dist: Optional[List[int]] = None
    dist_original: Optional[List[int]] = None
    dist_diff: Optional[List[int]] = None

    odds: Optional[List[int]] = None
    odds_original: Optional[List[int]] = None
    odds_diff: Optional[List[int]] = None

    result: Optional[List[int]] = None

    def __json__(self):
        return self.__dict__

    def update(self, other_game: "Game"):
        if not isinstance(other_game, Game):
            raise ValueError("Input must be a game")
        else:
            # Do I need try except IF game at index is not defined or something?

            # Update distribution with the new values
            self.dist_diff = [
                a_i - b_i
                for a_i, b_i in zip(
                    other_game.dist,
                    self.dist_original,
                )
            ]

            # Update original distribution
            self.dist = other_game.dist

            # # Update odds
            # self.odds = other_game.odds
            # self.odds_original = other_game.odds_original
            # self.odds_diff = other_game.odds_diff


@dataclass
class Gameday:
    day_nr: Optional[int] = None
    day_str: Optional[str] = None
    sale_stop: Optional[str] = None
    last_game_time: Optional[str] = None  # Or rather datetime?
    sale_amount_full: Optional[int] = None
    sale_amount_half: Optional[int] = None
    bonus: Optional[int] = None
    games: Optional[Dict[str, Game]] = None

    payout_total: Optional[int] = None
    prizes_halftime: Optional[Dict[int, int]] = None
    prizes_fulltime: Optional[Dict[int, int]] = None

    def __json__(self):
        gameday_dict = self.__dict__.copy()
        gameday_dict['games'] = {key: game.__json__() for key, game in self.games.items()}
        return gameday_dict



####  Databutton code
# import databutton as db
# from utils import *
import json
import requests
import pickle
import datetime
import pytz

# Try getting the info directly through the API instead of using the JS based HTML
url = f"https://api.norsk-tipping.no/SportGameInfo/v1/api/tipping/gameinfo?gameDay=ALL"
headers = {
    "User-Agent": "Mozilla/5.0 (X11; Ubuntu; Linux x86_64; rv:89.0) Gecko/20100101 Firefox/89.0",
}
r = requests.get(url, headers=headers)
data = json.loads(r.text)
# print(data)

######################################
#   Load dynamic game day dict
######################################

# Reload the pickled file and unpickle the dictionary
try:
    with open("gd_dict.pkl", "rb") as file:
        gameday_dict = pickle.load(file)
    # gdd_pickle = db.storage.binary.get("gd_dict.pkl")
    # gameday_dict = pickle.loads(gdd_pickle)
except FileNotFoundError:
    print("File does not exist.")
    gameday_dict = {}  # db.storage.json.get("gameDayInfo.json")
except pickle.PickleError as e:
    print(f"An error occurred with the pickle file: {e}")


# Returns a list of the three game days
sports_data_list = data["gameList"]


for game_day in sports_data_list:
    # # Get general data for the game day
    # gameDayNo = game_day["gameDayNo"]
    # gameDay = game_day["gameDay"]
    # Initiate gameday object
    gd = Gameday(day_str=game_day["gameDay"], day_nr=game_day["gameDayNo"])

    # Use the saleStop information as a trigger to check if there is any data available for the gameday
    try:
        # saleStop = game_day["betObject"]["saleStop"]
        gd.sale_stop = game_day["betObject"]["saleStop"]
    except KeyError as e:
        # Catch the error and just break the for loop for this day, hence keeping the old information.
        print(f"There is no data for day: {game_day['gameDay']}")
        break

    # sale_amount_full = game_day["betObject"]["saleAmount"]["fullTime"]
    # sale_amount_half = game_day["betObject"]["saleAmount"]["halfTime"]
    gd.sale_amount_half = game_day["betObject"]["saleAmount"]["halfTime"]
    gd.sale_amount_full = game_day["betObject"]["saleAmount"]["fullTime"]
    try:
        # bonus = game_day["bonusPot"][0]
        gd.bonus = game_day["bonusPot"][0]
    except:
        # bonus = "No bonus found."
        gd.bonus = "No bonus found."
    # TODO: Add jackpot ??

    # Get betting distribution for each game, does not matter if the games are new or old.
    # TODO: What happens if this is empty? Will it throw an error?
    for dists in game_day["betObject"]["tips"]["fullTime"]:
        if dists["tipType"] == "PEOPLE":
            people_tip_dict = dists["distribution"]

    # Get games of the
    newGames = {}  # Better to use a dictionary or what?
    game_counter = 1
    for event in game_day["betObject"]["events"]:
        # Use this!
        # cet_timezone = pytz.timezone('Europe/Paris')  # CET timezone
        # parsed_date_cet = parsed_date.replace(tzinfo=pytz.utc).astimezone(cet_timezone)

        # Check game time and add latest
        if gd.last_game_time == None:
            gd.last_game_time = event["eventTime"]
            # gd.last_game_time = datetime.datetime.strptime(
            #     event["eventTime"], "%Y-%m-%dT%H:%M:%SZ"
            # )
        else:
            latest_game_time = max(
                [
                    datetime.datetime.strptime(
                        gd.last_game_time, "%Y-%m-%dT%H:%M:%SZ"
                    ),
                    datetime.datetime.strptime(
                        event["eventTime"], "%Y-%m-%dT%H:%M:%SZ"
                    ),
                ]
            )
            if latest_game_time == datetime.datetime.strptime(event["eventTime"], "%Y-%m-%dT%H:%M:%SZ"):
                gd.last_game_time = event["eventTime"]


        game = Game(
            game_nr=event["eventNo"],
            game_str=event["eventName"],
            arrangement_name=event["arrangementName"],
            home_team=event["teamNames"]["home"]["name"],
            away_team=event["teamNames"]["away"]["name"],
            event_time=event["eventTime"],
            sport_name=event["sportName"],
            dist=people_tip_dict[str(game_counter)],
            dist_diff=[0, 0, 0],
            dist_original=people_tip_dict[str(game_counter)],
            odds=[],
            odds_original=[],
            odds_diff=[],
            status=event["matchStatus"]["statusForClient"],
        )
        newGames[event["eventName"]] = game
        game_counter += 1

    # Insert the games into this gameday?
    gd.games = newGames

    # Is it even possible to do something like dis?
    # If the gameday is already present and sales_stop time is equal to the one present, then update the distribution values of the gameday.

    # Check if gameday is already inside of dictionary
    if gd.day_str in gameday_dict:
        original_gd = gameday_dict[gd.day_str]
        original_games = original_gd.games

        if gd.sale_stop == original_gd.sale_stop:
            for idx, game in enumerate(newGames):
                selected_new_game = newGames[game]
                selected_old_game = original_games[game]

                # Update distributions
                selected_old_game.update(selected_new_game)

        else:
            print(
                "Need to call the other script here probably to get the results if the days have been changed."
            )
            # 1. Put the gameday into a intermediate storage location and update after X hours after last played game?
            # 2. Thereafter, when this is done, save it for later data analysis including all info.

            # And also ofc store the data with whatever is worth it such that some machine learning or whatever can be done on the results in the future.
    else:
        gameday_dict[gd.day_str] = gd

# Json string to be able to save directly as readable json or whatever. Better to stick with objects in the long run though.
json_string = json.dumps({key: gameday.__json__() for key, gameday in gameday_dict.items()}, indent=4)
# json data instead
json_data = {key: gameday.__json__() for key, gameday in gameday_dict.items()}

# Save info.
# pickled_gdd = pickle.dumps(gameday_dict)
# db.storage.binary.put("gd_dict.pkl", pickled_gdd)
with open("data.pkl", "wb") as file:
   pickle.dump(gameday_dict, file)
