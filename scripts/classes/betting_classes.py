# Class for every match,

# Is it worth it to make verything object oriented as long as it is stored as json, text in bin form or dataframes? 

# Maybe it is just better to make an export that will send me an e-mail og upload to an external database such that we keep the data for future use? 


class Match:
    def __init__(self, name, kickoff_time) -> None:
        self.name = name
        self.kickoff = kickoff_time

    def __str__(self) -> str:
        return print(f"NT match name: {self.name}\
        odds match name: .....")

    def update_odds(self, new_odds, from_where) -> None:
        # if (from_where in self.odds_list):
        #     #update odds
        # else:
        #     #add odds
        print("stuff")

    