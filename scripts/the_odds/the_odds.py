# Is this of interest maybe? https://github.com/pretrehr/Sports-betting/blob/master/sportsbetting/bookmakers/unibet.py 
from calendar import different_locale
from cmath import nan
import pprint
import json
import requests
import datetime
from dateutil import parser

######################################
#   Load gamedayJson
######################################
with open("data/gameDayInfo.json", 'r') as f:
        gameday_dict = json.load(f)
f.close()

######################################
#  Get closest game_day since that is the only one we care about atm
######################################
closest_matchday = "MIDWEEK"
time_diff = 60*60*24*7
time_now = datetime.datetime.utcnow().replace(tzinfo=datetime.timezone.utc)
for game_day in gameday_dict:
    difference = (parser.parse(gameday_dict[game_day]["saleStop"]) - time_now).total_seconds()
    # print(f"time Diff: {difference}")
    if difference < time_diff and parser.parse(gameday_dict[game_day]["saleStop"]) > time_now:
        closest_matchday = game_day
        time_diff = difference
# print(f"Gameday: {closest_matchday}")

######################################
#   Check if it is time to get new odds data:
######################################
# Hardcoded update times. This script should only run 12, 3, 1 and 0.5 hours before the deadline.
accepted_time_diffs = [12*60*60, 3*60*60, 1*60*60, 0.5*60*60]
get_data = True
interval = 29*60 # 29 minutes
for t in accepted_time_diffs:
    if t-interval/2 <= time_diff <= t+interval/2: # Check if the time difference from the closest gameday is within the threshold
        get_data = True

# If the time is right, update odds data! 
if get_data:

    ######################################
    #   API Call info
    ######################################
    API_KEY = API_KEY  #db.secrets.get("THE_ODDS_API_KEY")
    SPORT = "soccer_uefa_nations_league" #'upcoming' # use the sport_key from the /sports endpoint below, or use 'upcoming' to see the next 8 games across all sports
    REGION = 'uk' # uk | us | eu | au
    MARKET = 'h2h' # h2h | spreads | totals
    BOOKMAKERS = ['nordicbet', 'pinnacle', 'williamhill', 'sport888', 'unibet', 'betfair', 'marathonbet', 'betclic', 'paddypower', 'skybet'] #10 bookies to get the mean of, might as well just do 2 one but hey, why not if it "costs" the same :P  

    ## Get active sport keys from NT arrangement values. # TODO: Check the rest of the keys
    NT_to_theOdds_mapping = {
        "nations league": "soccer_uefa_nations_league",  # CHECKED
        # "norsk tipping" : nan,
        # "postnord" : nan,
        # "toppserien" : nan,
        "eliteserien": "soccer_norway_eliteserien",  # CHECKED
        # "obos" : nan,
        "premier league": "soccer_epl",  # CHECKED
        "championship": "soccer_efl_champ",  # CHECKED
        "league 1": "soccer_england_league1",
        "league 2": "soccer_england_league2",
        "fa-cup": "soccer_fa_cup",
        "ligacup": "soccer_england_efl_cup",
        "laliga": "soccer_spain_la_liga",
        "laliga 2": "soccer_spain_segunda_division",
        "bundesliga": "soccer_germany_bundesliga",
        "2. bundesliga": "soccer_germany_bundesliga2",
        "serie a": "soccer_italy_serie_a",
        "serie b": "soccer_italy_serie_b",
        "ligue 1": "soccer_france_league_one",
        "ligue 2": "soccer_france_league_two",
        "allsvenskan": "soccer_sweden_allsvenskan",
        "superettan": "soccer_sweden_superettan",
        "superliga": "soccer_denmark_superliga",
        "eredivise": "soccer_netherlands_eredivisie",
        "vm": "soccer_fifa_world_cup",
        "premiership": "soccer_spl",
        "primeira": "soccer_portugal_primeira_liga",
        "champ. league": "soccer_uefa_champs_league",
        "europa league": "soccer_uefa_europa_league",
        "TYR S": "soccer_turkey_super_league"
        # "conference league" : nan
    }

    # days = ["MIDWEEK", "SATURDAY", "SUNDAY"]
    ######################################
    #   Get NT Arrangement keys and map to available markets in the odds API.
    ######################################
    # # Check if NT arrangement key values can be found in the mapping and then set up the odds query.
    # test_list_keys = ["UEFA Nations League, A, Gr. 4", "UEFA Nations League, A, Gr. 1", "UEFA Nations League, A, Gr. 3", "UEFA Nations League, A, Gr. 2", "Norsk Tipping-ligaen avd1", "Norsk Tipping-ligaen avd3", "Norsk Tipping-ligaen avd5", "NOR PostNord-ligaen 2", "Toppserien, Women"]
    # TODO: Get this list of keys from the different gameweek days. Maybe also add timing such that the odds will only be checked from a couple days before the gameday?
    accepted_keys = []
    for gameName, game in gameday_dict[closest_matchday]["games"].items():
        for key,value in NT_to_theOdds_mapping.items():
            if key in game["arrangementName"].lower() and value not in accepted_keys:
                accepted_keys.append(value)
    print(accepted_keys)

    ######################################
    #   Get Odds data from the mapped keys list before mapping these to the matches themselves.
    ######################################
    odds_data = []
    for the_odds_sport_key in accepted_keys:
        odds_response = requests.get('https://api.the-odds-api.com/v3/odds', params={
            'api_key': API_KEY,
            'sport': the_odds_sport_key, #SPORT,
            'region': REGION,
            'mkt': MARKET,
            'bookmakers': BOOKMAKERS
        })

        odds_json = json.loads(odds_response.text)
        odds_data.append(odds_json["data"]) # Appending the odds data for the different keys to a list that can later be looped when searching for the available odds.
        # with open(f"odds_accepted{json_counter}.json", 'w') as fi:
        #     json.dump(odds_json, fi)
        # fi.close()

        if not odds_json['success']:
            print(odds_json['msg'])

        else:
            # print('Number of events:', len(odds_json['data']))
            # print(odds_json['data'])

            # Check your usage, this is kind of important and needs to be kept at a minimum.
            print('Remaining requests', odds_response.headers['x-requests-remaining'])
            print('Used requests', odds_response.headers['x-requests-used'])

            # TODO: Add e-mailing service to notify when there is not many requests left.

    # Temporary store the data
    with open("data/odds.json", 'w') as f:
        json.dump(odds_data, f)
    f.close()