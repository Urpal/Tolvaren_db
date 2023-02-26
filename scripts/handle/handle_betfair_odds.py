import pandas as pd
import json
import pprint
import difflib
import statistics

######################################
#   Load frames
######################################
with open("data/gameDayInfo.json", 'r') as f:
    gameday_dict = json.load(f)
# pprint.pprint(gameday_dict)
f.close()

with open("data/odds_events.json", 'r') as f:
    odds = json.load(f)
# pprint.pprint(odds)
f.close()

# Set json info into pamndas df
# json_df = pd.DataFrame(columns=["data","odds"],index=[0])
# json_df.at[0, "odds"] = {"odds_cell" : odds} 
# json_df.at[0, "data"] = {"gd_dict_cell" : gameday_dict}
# print(json_df)

# # get json info from df
# gameday_dict2 = json_df["data"].iloc[0]["gd_dict_cell"]
# odds2 = json_df["odds"].iloc[0]["odds_cell"]


# Some chosen country name mappings where the norwegian names does NOT correspond with the english ones.
# TODO: Find something that is usable directly. Also move this to utils or something
country_mapping = {
    "Frankrike" : "France",
    "Østerrike" : "Austria",
    "Kroatia" : "Croatia",
    "Danmark" : "Denmark",
    "Polen" : "Poland",
    "Nederland": "Netherlands",
    "Litauen" : "Lithuania",
    "Færøyene" : "Faroe Islands",
    "Aserbajdsjan" : "Azerbaijan",
    "Tyskland" : "Germany",
    "Ungarn" : "Hungary",
    "Belgia" : "Belgium",
    "Norge" : "Norway",
    "Spania" : "Spain",
    "Sveits" : "Switzerland",
    "Tsjekkia" : "Czech Republic" ,
    "Skottland" : "Scotland",
    "Kypros" : "Cyprus",
    "Hellas" : "Greece",
    "Kasakhstan": "Kazakhstan",
    "Tyrkia": "Turkey",
    "Liechtenstein": "Liechtenstein", 
    "Ukraina" : "Ukraine",
    "Irland" : "Republic of Ireland",
    "Sverige": "Sweden"
}

# Add a list of stop words that makes it hard to connect NT team names to their respective full names..
stopwords = ["fc", "fk", "athletic", "city", "united", "bk", "hotspur", "albion", "milano"] # Will this actually help? 


######################################
#   Update data json with new odds data.
######################################
# Find related odds to the matches.
# days = ["MIDWEEK", "SATURDAY", "SUNDAY"]
closest_matchday = "MIDWEEK" #TODO;: Remove ones merged with other part
for gameName, game in gameday_dict[closest_matchday]["games"].items():

    # Check if game is international, then change from Norwegian to english if necessary in order to pinpoint better the correct match!
    ##### IF INTERNATIONAL GAME ##################
    heime = game["home"]
    borte = game["away"]
    print(f"{heime} - {borte}")
    if ("nations league" in game["arrangementName"].lower()) or ("mesterskap" in game["arrangementName"].lower()): #TODO: Check this for the World cup! 
        if (game["home"] in country_mapping):
            heime = country_mapping[game["home"]]
        if (game["away"] in country_mapping):
            borte = country_mapping[game["away"]]
    ###############################################

    # Strip and refine NT game
    heime_words = heime.split()
    heime_stripped_list  = [word for word in heime_words if word.lower() not in stopwords]
    heime_team_stripped = ' '.join(heime_stripped_list)

    borte_words = borte.split()
    borte_stripped_list  = [word for word in borte_words if word.lower() not in stopwords]
    borte_team_stripped = ' '.join(borte_stripped_list)
    NT_game = heime_team_stripped + " - " + borte_team_stripped

    # Loop through the odds matches and try to find the correct fit (Norwegian to english if internationak games at least..)
    for match in odds: # TODO: Refine this cuz now it sucks.

        #Strip and refine odds game
        home_words = odds[match]['home']['name'].split()
        home_stripped_list  = [word for word in home_words if word.lower() not in stopwords]
        home_team_stripped = ' '.join(home_stripped_list)

        away_words = odds[match]['away']['name'].split()
        away_stripped_list  = [word for word in away_words if word.lower() not in stopwords]
        away_team_stripped = ' '.join(away_stripped_list)

        odds_game = home_team_stripped + " - " + away_team_stripped
        
        ratios = [difflib.SequenceMatcher(None, odds_game.lower(), NT_game.lower()).ratio(), 
                        difflib.SequenceMatcher(None, home_team_stripped.lower(), heime_team_stripped.lower()).ratio(), 
                        difflib.SequenceMatcher(None, away_team_stripped.lower(), borte_team_stripped.lower()).ratio()]
        ratio = statistics.mean(ratios)
        
        if (ratio > 0.65): 
            # print(f"Odds game: {odds_game} and NT game: {NT_game} with ratio: {ratio}")

            if "odds" not in game:
                game["odds"] = [odds[match]['home']['odds'],odds[match]['draw']['odds'],odds[match]['away']['odds']]
                game["odds_original"] = [odds[match]['home']['odds'],odds[match]['draw']['odds'],odds[match]['away']['odds']]
                game["odds_diff"] = [0,0,0]
            
            else:
                game["odds"] = [odds[match]['home']['odds'],odds[match]['draw']['odds'],odds[match]['away']['odds']]
                game["odds_diff"] = [a_i - b_i for a_i, b_i in zip(game["odds"], game["odds_original"])]
                    
            # These values are better of in the actual front-end right? Better placed there such that missing values can be added similar as above
            # Can then have a spinning script updating the values in the background depending on the updated values either from odds or the NT distributions
            # pprint.pprint(game["odds"])
            break #Break if the correct match has been found.
            # print("----")        
        
######################################
#   Save the updated data
######################################
# pprint.pprint(gameday_dict)
with open("data/gameDayInfo.json", 'w') as f:
    json.dump(gameday_dict, f)
f.close()