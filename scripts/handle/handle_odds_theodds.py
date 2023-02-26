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

with open("data/odds.json", 'r') as f:
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
    "Sverige": "Sweden",
}

# Add a list of stop words that makes it hard to connect NT team names to their respective full names..
stopwords = ["fc", "fk", "athletic", "city", "united", "bk", "hotspur", "albion", "milano"] # Will this actually help? 


######################################
#   Update data json with new odds data.
######################################
# Find related odds to the matches.
# days = ["MIDWEEK", "SATURDAY", "SUNDAY"]
closest_matchday = "SUNDAY" #TODO;: Remove ones merged with other part
for gameName, game in gameday_dict[closest_matchday]["games"].items():

    # Check if game is international, then change from Norwegian to english if necessary in order to pinpoint better the correct match!
    ##### IF INTERNATIONAL GAME ##################
    heime = game["home"]
    borte = game["away"]
    print(f"{heime} - {borte}")
    if ("nations league" in game["arrangementName"].lower()) or ("mesterskap" in game["arrangementName"].lower()) or ("vm" in game["arrangementName"].lower()): #TODO: Check this for the World cup! 
        if (game["home"] in country_mapping):
            heime = country_mapping[game["home"]]
        if (game["away"] in country_mapping):
            borte = country_mapping[game["away"]]
    ###############################################

    # Loop through the odds matches and try to find the correct fit (Norwegian to english if internationak games at least..)
    for market in odds:
        # TODO: Fix this such that it only checks the relevant market
        # Check if market is relevant
        for match in market: 
            # Map home and away since this is directly linked to the odds placement from the API calls
            home = 0
            away = 1
            if (match["teams"][0] != match["home_team"]):
                home = 1
                away = 0

            heime_words = heime.split()
            heime_stripped_list  = [word for word in heime_words if word.lower() not in stopwords]
            heime_team_stripped = ' '.join(heime_stripped_list)

            borte_words = borte.split()
            borte_stripped_list  = [word for word in borte_words if word.lower() not in stopwords]
            borte_team_stripped = ' '.join(borte_stripped_list)

            home_words = match["teams"][home].split()
            home_stripped_list  = [word for word in home_words if word.lower() not in stopwords]
            home_team_stripped = ' '.join(home_stripped_list)

            away_words = match["teams"][away].split()
            away_stripped_list  = [word for word in away_words if word.lower() not in stopwords]
            away_team_stripped = ' '.join(away_stripped_list)

            odds_game = home_team_stripped + " - " + away_team_stripped
            NT_game = heime_team_stripped + " - " + borte_team_stripped

            
            ratios = [difflib.SequenceMatcher(None, odds_game.lower(), NT_game.lower()).ratio(), 
                            difflib.SequenceMatcher(None, home_team_stripped.lower(), heime_team_stripped.lower()).ratio(), 
                            difflib.SequenceMatcher(None, away_team_stripped.lower(), borte_team_stripped.lower()).ratio()]
            ratio = statistics.mean(ratios)
            
            if (ratio > 0.65): 
                print(f"Odds game: {odds_game} and NT game: {NT_game} with ratio: {ratio}")
                for site in match["sites"]:
                    # If there is no Odds entries in game at all, add empty keys that can be filled.
                    if "odds" not in game:
                        game["odds"] = {}
                        game["odds_original"] = {}
                        game["odds_diff"] = {}

                    if site['site_nice'] not in game["odds"]:
                        game["odds"][site['site_nice']] = [site['odds']['h2h'][home], site['odds']['h2h'][2], site['odds']['h2h'][away]]
                        game["odds_original"][site['site_nice']] = [site['odds']['h2h'][home], site['odds']['h2h'][2], site['odds']['h2h'][away]] 
                        game["odds_diff"][site['site_nice']] = [0,0,0]
                    else:
                        game["odds"][site['site_nice']] = [site['odds']['h2h'][home], site['odds']['h2h'][2], site['odds']['h2h'][away]]
                        game["odds_diff"][site['site_nice']] = [a_i - b_i for a_i, b_i in zip(game["odds"][site['site_nice']], game["odds_original"][site['site_nice']])]
                        
                        # gameday_dict[gameDay]["games"][game]["diff"] = [a_i - b_i for a_i, b_i in zip(newGames[game]["dist"], gameday_dict[gameDay]["games"][game]["dist_original"])]
                        # gameday_dict[gameDay]["games"][game]["dist"] = newGames[game]["dist"]

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