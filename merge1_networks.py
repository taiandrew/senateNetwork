#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Produces files for ERGM regressions in R
Edges and biographical data files (two) by Congress
"""

# %% Preamble

import numpy as np
import pandas as pd
import os

os.chdir(os.path.dirname(os.path.abspath(__file__)))


# %% Open data

# Open data (from previous steps)
bills = pd.read_parquet('./data/bills.parquet')
biographical = pd.read_parquet('./data/biographical.parquet')
cosponsors = pd.read_parquet('./data/cosponsors.parquet')


# %% Drop duplicates

# Print duplicates; check!
print('Bills duplicates:')
print(bills[bills.duplicated(subset=['congress', 'legislation_id'])])
print('Cosponsors duplicates:')
print(cosponsors[cosponsors.duplicated(subset=['congress', 'legislation_id', 'cosponsor_icpsr'])])
print('Biographical duplicates:')
print(biographical[biographical.duplicated(subset=['congress', 'icpsr'])])


#Drop duplicates in bills data by congress and legislation_id
bills = bills.drop_duplicates(
    subset=['congress', 'legislation_id']
    )

# Drop duplicates in cosponsors data by congress, legislation_id and cosponsor_icpsr
cosponsors = cosponsors.drop_duplicates(
    subset=['congress', 'legislation_id', 'cosponsor_icpsr']
    )

# Drop duplicates in biographical data by congress and icpsr_id
biographical = biographical.drop_duplicates(
    subset=['congress', 'icpsr']
    )

bills.to_parquet('./data/bills.parquet')
biographical.to_parquet('./data/biographical.parquet')
cosponsors.to_parquet('./data/cosponsors.parquet')



# %% Process data for weighted network analysis in Python networkx

edges = pd.merge(cosponsors, bills[['number_cosponsors', 'congress', 'legislation_id']],
                 how = 'left',
                 left_on = ['congress', 'legislation_id'], 
                 right_on = ['congress', 'legislation_id']
                 )
edges['weight'] = 1/edges['number_cosponsors']
edges = edges.drop_duplicates()

# Calculate weights
keys = ['cosponsor_icpsr', 'sponsor_icpsr']
edges = edges.groupby(keys)['weight'].sum().reset_index()

edges.to_parquet('./data/edges.parquet')


# %% Process data for ERGMs in R; some cleaning

# cosponsors data (edges), with counts per congress 
cosponsors = cosponsors[['congress', 'cosponsor_icpsr', 'sponsor_icpsr']]
keys = ['congress', 'cosponsor_icpsr', 'sponsor_icpsr']
cosponsors['weight'] = 1
cosponsors = cosponsors.groupby(keys)['weight'].sum().reset_index()

# Keep desired attributes for bio data
keep_col = ['icpsr', 'congress', 'state', 'party', 'born', 'nominate_dim1', 'relig', 'military', 'educ', 'white']
biographical = biographical[keep_col]

# Drop if either sponsor or cosponsor is missing
cosponsors = cosponsors.dropna(subset=['cosponsor_icpsr', 'sponsor_icpsr'])

# Drop duplicates in biographical data by congress and icpsr_id
biographical = biographical.drop_duplicates(subset=['congress', 'icpsr'])

# Drop cosponsor if sponsor ID is same as cosponsor ID
cosponsors = cosponsors[cosponsors['sponsor_icpsr'] != cosponsors['cosponsor_icpsr']]
                        


# %% Save files for networks by congress

# Save data by congress
for congress in cosponsors['congress'].unique():
    cosponsors[cosponsors['congress'] == congress].to_parquet(f'./data/cosponsors_{congress}.parquet')
    biographical[biographical['congress'] == congress].to_parquet(f'./data/biographical_{congress}.parquet')
    print(f'Congress {congress} saved')
    