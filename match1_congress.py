#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Uses the ICPSR & names file (from the DW-nominate data) to match to congressionald ata sources
"""

# %% Preamble

import numpy as np
import pandas as pd
import os

from fuzzywuzzy import fuzz
from fuzzywuzzy import process

os.chdir(os.path.dirname(os.path.abspath(__file__)))


# %% Match names from Congress data (bills, cosponsors) to ICPSR ID numbers

# Open data to match (from previous steps)
congress_names = pd.read_parquet('./data/temp/congress_names_pre.parquet')
icpsr_ids = pd.read_parquet('./data/temp/icpsr_ids.parquet')


# Fuzzy match name in congress_names to the closest name in icpsr_ids (using thefuzz)
def fuzzy_match(name, state, choices, threshold=60):
    match_choices = choices[choices['state'] == state]['name_dw']
    match = process.extractOne(name, match_choices)       # best name, score, index
    if match[1]>= threshold:
        return match[0], match[1], match[2] 
    else:
        return None, None
    
congress_names[['name_dw', 'match_closeness', 'match_index']] = congress_names.apply(
    lambda row: pd.Series(fuzzy_match(row['name_congress'], row['state'], icpsr_ids)), 
    axis=1
    )


# Merge in ICPSR ID numbers from index
congress_names = pd.merge(congress_names, icpsr_ids['icpsr'], 
                          how='left', 
                          left_on='match_index', 
                          right_index=True)

congress_names = congress_names[['name_info', 'icpsr']]

'''
The congress_names df now has:
    name_info (the identifiers for the congress bills data)
    icpsr (the canonical identifier for individuals)
It can be used to match ICPSR numbers into the congressional bills data
Recommend checking diagnostics (closeness and spot checking names)
'''



# %% Match ICPSR IDs back to cosponsors df and party df

# Open data to be matched
cosponsors = pd.read_parquet('./data/temp/cosponsors_pre.parquet')
congress_parties = pd.read_parquet('./data/temp/congress_parties_pre.parquet')

# Merge ICPSR IDs for sponsors
cosponsors = pd.merge(cosponsors, congress_names, 
                      how='left',
                      left_on=['sponsor'], 
                      right_on=['name_info'] )
cosponsors.rename(columns = {'icpsr': 'sponsor_icpsr'}, inplace=True)
cosponsors.drop(columns=['name_info'], inplace=True)

# Merge ICPSR IDs for cosponsors
cosponsors = pd.merge(cosponsors, congress_names, 
                      how='left',
                      left_on=['cosponsor'], 
                      right_on=['name_info'] )
cosponsors.rename(columns = {'icpsr': 'cosponsor_icpsr'}, inplace=True)
cosponsors.drop(columns=['name_info'], inplace=True)


# Merge ICPSR IDs for party data
congress_parties = pd.merge(congress_parties, congress_names,
                            how='left',
                            right_on=['name_info'],
                            left_on=['name_info'] )
congress_parties.drop_duplicates()


# %% Save data
cosponsors.to_parquet('./data/cosponsors.parquet')
congress_parties.to_parquet('./data/temp/congress_parties.parquet')
