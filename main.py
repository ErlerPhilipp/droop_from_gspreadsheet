import requests
import pandas as pd
import numpy as np
import re
import subprocess

SPREADSHEET_ID = '1FK_fifyS8cmstNq_vlVpr5cuX-B1-1yOBq3q6NoWYpA' # ID from your public spreadsheet URL
VOTE_FILE = 'vote.csv'
BLT_FILE = 'vote.blt'
PATH_TO_DROOP = ""
PYTHON_COMMAND = "python3"
ELECTION_TITLE = "Konferenz"
LOG_FILE = 'election.log'
ELECTED_FILE = 'elected.txt'

# FETCH RESULT FROM SPREAD SHEET

url = f"https://docs.google.com/spreadsheets/d/{SPREADSHEET_ID}/export?exportFormat=csv"

response = requests.get(url)

if response.status_code != 200:
    raise Exception(f"Failed to fetch data. Status code: {response.status_code}")

with open(VOTE_FILE, 'w') as f:
    f.write(response.text)

# CONVERT BALLOTS MATRIX TO SORTED CANDIDATES ID PER BALLOT

df = pd.read_csv(VOTE_FILE)
number_of_winners = re.search(r'\d+', df.columns[0]).group()

candidates = df.values[:, 0]
ballots = df.values[:, 1:]

ballots_with_candidate_preferences = [
                                        [(candidate, pref) 
                                        for candidate, pref in enumerate(ballot) 
                                        if not np.isnan(pref)] 
                                        for ballot in ballots.T]

ballots_with_candidates_sorted_by_preference = [
                                        [candidate 
                                        for candidate, preference in sorted(ballot, key=lambda x: x[1])] 
                                        for ballot in ballots_with_candidate_preferences]

# WRITE BLT

blt_ballots = "\n".join(
    [f"1 {' '.join([str(c+1) for c in ballot])} 0 #" + ", ".join(candidates[c] for c in ballot)
     for ballot in ballots_with_candidates_sorted_by_preference])

blt_candidates = "\n".join(f'"{candidate} #{i}"' for i, candidate in enumerate(candidates,1))

with open('vote.blt', 'w') as file:
    blt_content = f"""
    {len(candidates)} {number_of_winners}
    {blt_ballots}
    0 # end marker
    {blt_candidates}
    "{ELECTION_TITLE}" #Titel
    """
    file.write(blt_content)
    print(blt_content)

# EXECUTE DROOP

result = subprocess.run([PYTHON_COMMAND, PATH_TO_DROOP, "meek", BLT_FILE], capture_output=True, text=True)
with open(LOG_FILE, 'w') as file:
    file.write(result.stdout)

rounds = result.stdout.split('Round ')
election_pattern= r'Action: Elect: (?P<candidate>.*) #'
electees_in_rounds = [(i, elected.group('candidate')) 
                      for i, r in enumerate(rounds[1:],1)
                      for elected in re.finditer(election_pattern, r) 
                       if elected ]

electees_in_round = "\n".join(f"{str(round).rjust(5)} {person}" for round, person in electees_in_rounds)
elected_text = f"""
ROUND NAME
{electees_in_round}
"""
with open(ELECTED_FILE, 'w') as file:
    file.write(elected_text)
    print(elected_text)