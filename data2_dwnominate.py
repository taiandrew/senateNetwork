#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Reads in DW-Nominate data file -- contains political position scale and ICPSR IDs
Also creates the ICPSR ID and name correspondence, which we use to fuzzymatch
Want to attach the IDs to the other data sources of legislators later

"""

###############
# %% Preamble
###############

import numpy as np
import pandas as pd
import os

os.chdir(os.path.dirname(os.path.abspath(__file__)))


###############
# %% Read DW nominate data and prepare list of names with ICPSR IDs
###############

# Read data
dw_nominate = pd.read_csv('./data/voteview/HSall_members.csv', low_memory=False)

# Keep only data from relevant congresses: 93+, and only House, select variables
dw_nominate = dw_nominate[dw_nominate['congress']>=93]
dw_nominate = dw_nominate[dw_nominate['chamber']=='Senate']

keep_col = ['congress', 'icpsr', 'state_abbrev', 'bioname', 'born', 'nominate_dim1', 'nokken_poole_dim1']
dw_nominate = dw_nominate[keep_col]
dw_nominate.rename(columns = {'icpsr': 'icpsr',
                              'state_abbrev': 'state',
                              'district_code': 'district',
                              'bioname': 'name_dw'
                              }, inplace=True)


# If there are multiple ICPSR IDs for the same name, replace the later ones with the first
dw_nominate = dw_nominate.sort_values(['name_dw', 'state', 'congress'])
dw_nominate.reset_index(inplace=True, drop=True)

for i in range(1,dw_nominate.shape[0]):
    same_name = (dw_nominate['name_dw'][i] == dw_nominate['name_dw'][i-1])
    diff_icpsr = (dw_nominate['icpsr'][i] != dw_nominate['icpsr'][i-1])
    if same_name & diff_icpsr:
        dw_nominate.loc[i, 'icpsr'] = dw_nominate['icpsr'][i-1]
        print(dw_nominate['name_dw'][i])
        


'''
If a senator switches parties, he gets a new ICPSR number. This impedes matching to CQ data.
We'll just replace with the first. The party time series data comes from congress bills anyway.
'''

###############
# %% Create key to merge names with ICPSR IDs 
###############

# ICPSR ID dataframe
icpsr_ids = dw_nominate[['name_dw', 'icpsr', 'state']].copy()
icpsr_ids['name_dw'] = icpsr_ids['name_dw'].str.lower()
icpsr_ids.drop_duplicates(inplace=True)
icpsr_ids = icpsr_ids[['icpsr', 'name_dw', 'state']]
icpsr_ids.reset_index(drop=True, inplace=True)

'''
icpsr_ids is each unique name X state
Most merges can be done on these
then use fuzzy match to pick best name
'''

###############
# %% Save
###############

icpsr_ids.to_parquet('./data/temp/icpsr_ids.parquet')
dw_nominate.to_parquet('./data/temp/dw_nominate.parquet')
