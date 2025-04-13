#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Uses the ICPSR & names file (from the DW-nominate data) to match to CQ data
"""

# %% Preamble

import numpy as np
import pandas as pd
import os

from fuzzywuzzy import fuzz
from fuzzywuzzy import process

os.chdir(os.path.dirname(os.path.abspath(__file__)))


# %% Fuzzy match CQ data to ICPSRs

# Open data (from previous steps)
icpsr_ids = pd.read_parquet('./data/temp/icpsr_ids.parquet')
cq = pd.read_parquet('./data/temp/cq.parquet')

# Fuzzy match name in congress_names to the closest name in icpsr_ids (using thefuzz)
def fuzzy_match(name, state, choices, threshold=50):
    match_choices = choices[choices['state'] == state]['name_dw']
    match = process.extractOne(name, match_choices)       # best name, score, index
    if match[1]>= threshold:
        return match[0], match[1], match[2] 
    else:
        return None, None

# Apply the match function by row
cq[['name_dw', 'match_closeness', 'match_index']] = cq.apply(
    lambda row: pd.Series(fuzzy_match(row['name_cq'], row['state'], icpsr_ids)), 
    axis=1
    )

# Merge in ICPSR ID numbers using index
cq = pd.merge(cq, icpsr_ids['icpsr'], 
              how='left', 
              left_on='match_index', 
              right_index=True)



# %% Clean and save

# Move icpsr column to the front
cols = cq.columns.tolist()
cols = cols[-1:] + cols[:-1]
cq = cq[cols]

cq.drop(columns = ['name_dw', 'match_index', 'match_closeness'], inplace=True)
cq.reset_index(inplace=True, drop=True)

cq.to_parquet('./data/temp/cq_icpsr.parquet')