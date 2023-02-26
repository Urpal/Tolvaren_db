
# from asyncio import runners
import betfairlightweight
from betfairlightweight import filters
import requests
import datetime
import pandas as pd # Is this of interest maybe? https://github.com/pretrehr/Sports-betting/blob/master/sportsbetting/bookmakers/unibet.py 

# from calendar import different_locale
from cmath import nan
from pprint import pprint as pp
import json
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
accepted_time_diffs = [48*60*60,22*60*60,12*60*60, 3*60*60, 1*60*60, 0.5*60*60]
get_data = True
interval = 29*60 # 29 minutes
for t in accepted_time_diffs:
    if t-interval/2 <= time_diff <= t+interval/2: # Check if the time difference from the closest gameday is within the threshold
        get_data = True

# If the time is right, update odds data! 
if get_data:

    ######################################
    #   API session info
    ######################################
    session = requests.session()
    U_NAME = "Username" 
    PW = "Password" 
    API_KEY = "API Key" 

    #NB: To run this remotely, a betfair cert is necessary to function ass a "bot" TODO
    

    trading = betfairlightweight.APIClient(username=U_NAME, password=PW, app_key=API_KEY) #, lightweight=True)
    # trading.login_interactive()
    trading.login()

    # I need the autorization to work from  remote location
    # in requests.Session
    #     response = session.post(
    #         self.url,
    #         data=self.data,
    #         headers=self.client.login_headers,
    #         cert=self.client.cert,
    #         timeout=(self.connect_timeout, self.read_timeout),
    #     )
    # I need the cert part to work, in other owrds, I actually need the .key and .cert files, or maybe .pem file in order to autorize

    
    ## Get active sport keys from NT arrangement values. # TODO: Check the rest of the keys and see if all of them are available..
    NT_to_betfair_mapping = {
        "nations league" : 11984200, #CHECKED
        # "norsk tipping" : nan,
        # "postnord" : nan,
        "toppserien" : 11517816,
        "eliteserien" : 11068551, #CHECKED
        "NM cup" : 4051,
        "2. divisjon" : 891106, #12224917 or these? or both??
        "3. divisjon" : 920858, #12224979
        "Norwegian league (W)" : 7126020, #Norwegian league? 
        "1. div (W)": 10371778,
        "obos" : 12209546,
        "premier league" : 10932509, #CHECKED
        "championship" : 7129730, #CHECKED
        "league 1" : 35,
        "league 2" : 37,
        "laliga" : 117,
        "laliga 2" : 12204313,
        "1. bundesliga" : 59,
        "2. bundesliga" : 61,
        "serie a" : 81, #CHECKED
        "serie b" : 12199689,
        "ligue 1" : 55,
        "ligue 2" : 57, 
        "allsvenskan" : 129,
        "superettan" : 131,
        "superliga" : 23,
        "eredivise" : 11,
        "premiership" : 105,
        "primeira" : 99,
        "champ. league" : 228, #CHECKED
        "europa league" : 2005,
        "MLS" : 141,
        "ligacup" : 2134, #engelsk
        "NM" : 4051,
        "FA cup" : 30558,
        "VM kvinne" : 12220485,
        "VM 22" : 11997262,
        "conference league" : 12375833
    }

    # days = ["MIDWEEK", "SATURDAY", "SUNDAY"]
    ######################################
    #   Get NT Arrangement keys and map to available markets in the odds API.
    ######################################
    # # Check if NT arrangement key values can be found in the mapping and then set up the odds query.
    accepted_keys = []
    for gameName, game in gameday_dict[closest_matchday]["games"].items():
        for key,value in NT_to_betfair_mapping.items():
            if key in game["arrangementName"].lower() and value not in accepted_keys:
                accepted_keys.append(value)
    print(accepted_keys)

    ######################################
    #   Get Odds data from the mapped keys list before mapping these to the matches themselves.
    ######################################
    odds_data = []
    # for betfair_sport_key in accepted_keys: # Instead of querieng every key at once, lets go for all of the keys in one query. TODO: What is the maximum limit?

    # Set filter for defined competitions of football event types
    competition_filter = filters.market_filter(
        event_type_ids=[1], #Soccer since we are only interested in that at the moment.
        competition_ids=accepted_keys
        )
    # Get event IDs that fit the filter
    results = trading.betting.list_events(
            filter=competition_filter
        )
    # Get event IDs, names etc of the matches found in list_events
    event_ID_list = []
    event_dict = {} #Use this instead as a direct dictionary similar as the odds?
    for i in results:
        # print(f"ID: {i.event.id} name: {i.event.name} market count:  {i.market_count}")
        try:
            teams = i.event.name.split(' v ') 
            #TODO: Might be better of comparing games here rather than handling the odds data later on.
            home_team = teams[0]
            away_team = teams[1]
            event_dict[i.event.name] = {
                'event_id': i.event.id,
                'teams' : i.event.name,
                'market_count' : i.market_count,
                'home': {'name':home_team, 'runner_id': 0, 'odds':0},
                'away': {'name':away_team, 'runner_id': 0, 'odds':0},
                'draw': {'runner_id':0, 'odds':0}
            }
            # TODO: Add check here to find the correct matches before querying any other additional information.
            event_ID_list.append(i.event.id)
        except: #TODO: Add type of error, value?
            print(f'This is not a match. Id is: {teams} which is typically a competition or something..')

    # Find Home, away and draw IDs for the events already found
    # Set market filter for the already found events to try and get the match odds
    market_filter = filters.market_filter(
        event_ids = event_ID_list, #[:10],
        market_type_codes=["MATCH_ODDS"]
    )

    # Get market catalogues for the events using the market filter
    market_catalogues = trading.betting.list_market_catalogue(
        filter = market_filter,
        max_results = 500, # Max size is 1k but should be equal to the number of matches anyways
        market_projection=[
                "COMPETITION", 
                "EVENT", 
                "EVENT_TYPE", 
                "MARKET_DESCRIPTION", 
                "MARKET_START_TIME",
                "RUNNER_DESCRIPTION",
                "RUNNER_METADATA"
            ],
    )

    market_id_list = []
    for catalogue in market_catalogues:
        #Maybe it is best to not get any information from this part afterall.. Do it in the next step instead.
        event_dict[catalogue.event.name]['market_id'] = catalogue.market_id
        event_dict[catalogue.event.name]['start_time'] = catalogue.market_start_time
        event_dict[catalogue.event.name]['total_matched'] = catalogue.total_matched
        event_dict[catalogue.event.name]['home']['runner_id'] = catalogue.runners[0].selection_id
        event_dict[catalogue.event.name]['away']['runner_id'] = catalogue.runners[1].selection_id
        event_dict[catalogue.event.name]['draw']['runner_id'] = catalogue.runners[2].selection_id

        market_id_list.append(catalogue.market_id)
        # print(f"Market ID: {catalogue.market_id} name: {catalogue._data['event']['name']}")
        # for runner in catalogue.runners:
        #     print(f"Name: {runner.runner_name} and id: {runner.selection_id} \n")
            
    # TODO:  IF matching is solved before, then there should not be more that 12 games so that should be the best option imo:P
    sublist_length = 30
    market_id_sublists = [market_id_list[x:x+sublist_length] for x in range(0, len(market_id_list), sublist_length)]
    print(market_id_sublists)

    # Get book, i.e. odds for the market catalogues.
    for sublist in market_id_sublists:
        market_books = trading.betting.list_market_book(
            market_ids=sublist, #Must be less that 40 market books..
            # market_type_codes="MATCH_ODDS",
            price_projection={
                "priceData":["EX_BEST_OFFERS"] # BEST OR ALL?
                }
        )
        for book in market_books:
            for event_key in event_dict:
                if event_dict[event_key]['market_id'] == book.market_id:
                    event_dict[event_key]['last_updated'] = book.last_match_time

                    for runner in book.runners:
                        # print(f"Runner: {runner.selection_id} last price: {runner.last_price_traded}")
                        for hub in ['home', 'away','draw']:
                            if runner.selection_id == event_dict[event_key][hub]['runner_id']:
                                if runner.last_price_traded != 0:
                                    event_dict[event_key][hub]['odds'] = runner.last_price_traded 
                                    break
                                else:
                                    event_dict[event_key][hub]['odds'] = (runner.ex.available_to_back[0].price + runner.ex.available_to_back[1].price + runner.ex.available_to_back[2].price)/3
                                    break #TODO: Check out if this is always three, and wtf are they actually representing? 
                    # print(f"Odds for game {event_key} is: {event_dict[event_key]['home']['odds']} - {event_dict[event_key]['draw']['odds']} - {event_dict[event_key]['away']['odds']}")
    # pp(event_dict)

    # Temporary store the data
    with open("data/odds_events.json", 'w') as f:
        json.dump(event_dict, f, default=str)
    f.close()







# # Function for handling runner books, returning values in a handy df.
# def process_runner_books(runner_books):
#     '''
#     This function processes the runner books and returns a DataFrame with the best back/lay prices + vol for each runner
#     :param runner_books:
#     :return:
#     '''
#     best_back_prices = [runner_book.ex.available_to_back[0].price
#         if runner_book.ex.available_to_back.price
#         else 1.01
#         for runner_book
#         in runner_books]
#     best_back_sizes = [runner_book.ex.available_to_back[0].size
#         if runner_book.ex.available_to_back.size
#         else 1.01
#         for runner_book
#         in runner_books]

#     best_lay_prices = [runner_book.ex.available_to_lay[0].price
#         if runner_book.ex.available_to_lay.price
#         else 1000.0
#         for runner_book
#         in runner_books]
#     best_lay_sizes = [runner_book.ex.available_to_lay[0].size
#         if runner_book.ex.available_to_lay.size
#         else 1.01
#         for runner_book
#         in runner_books]

#     selection_ids = [runner_book.selection_id for runner_book in runner_books]
#     last_prices_traded = [runner_book.last_price_traded for runner_book in runner_books]
#     total_matched = [runner_book.total_matched for runner_book in runner_books]
#     statuses = [runner_book.status for runner_book in runner_books]
#     scratching_datetimes = [runner_book.removal_date for runner_book in runner_books]
#     adjustment_factors = [runner_book.adjustment_factor for runner_book in runner_books]

#     df = pd.DataFrame({
#         'Selection ID': selection_ids,
#         'Best Back Price': best_back_prices,
#         'Best Back Size': best_back_sizes,
#         'Best Lay Price': best_lay_prices,
#         'Best Lay Size': best_lay_sizes,
#         'Last Price Traded': last_prices_traded,
#         'Total Matched': total_matched,
#         'Status': statuses,
#         'Removal Date': scratching_datetimes,
#         'Adjustment Factor': adjustment_factors
#     })
#     return df
