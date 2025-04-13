#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Wed Mar  5 11:33:44 2025

@author: andrewtai


Reads the data on bills from congress.gov.
Creates:
    1. congress_names -- unique names to be matched later to ICPSR IDs 
    2. bills -- data on bills; e.g. data on edges of the network
    3. cosponsors -- each pair is a sponsor X cosponsor in a congress; e.g. edges of the network
    4. Party "time series" since some senators switch
"""

# %% Preamble

import numpy as np
import pandas as pd
import os

os.chdir(os.path.dirname(os.path.abspath(__file__)))


###############
# %% 1. Read congress data + light cleaning
###############

bills = []

# list of all csv files in directory
filelist = os.listdir('./data/congress/')

# read in all csv files then append them together
for file in filelist:
    if file.endswith('.csv'):
        print(file)
        bills.append(pd.read_csv('./data/congress/' + file, skiprows=5, low_memory=False))

bills = pd.concat(bills)
bills = bills.copy()

del file, filelist

#bills = pd.read_csv('./data/congress/115_d.csv', skiprows=3)

# Rename important columns
bills.rename(columns = {'Legislation Number': 'legislation_id',
                             'Congress': 'congress',
                             'Title': 'title',
                             'Amends Bill': 'amends_bill',
                             'Sponsor': 'sponsor',
                             'Date Offered': 'date_offered',
                             'Date of Introduction': 'date_introduction',
                             'Number of Cosponsors': 'number_cosponsors',
                             'Date Submitted': 'date_submitted',
                             'Date Proposed': 'date_proposed',
                             'Committees': 'committees',
                             'Latest Action': 'latest_action',
                             'Latest Action Date': 'date_latest_action',
                             'Latest Summary': 'latest_summary',
                             }, inplace=True)


# Drop nan
bills.dropna(subset='legislation_id', inplace=True)

# Clean Congress number: keep first digits
bills['congress'] = bills['congress'].str.extract(r'(\d+)')
bills['congress'] = bills['congress'].astype(int)

# Clean the name lightly -- remove (Introduced XX/XX/XX) from name
bills['sponsor'] = bills['sponsor'].str.replace(r'\(.*?\)', "", regex=True)

# Legislation id
bills['legislation_id'] = bills['legislation_id'].str.extract(r'(\d+)', expand=False)
bills['legislation_id']  = bills['legislation_id'].astype(int)



###############
# %% 2. Get names to match to CQ/DW data later
###############

# Get unique names from Congress files (note also unique by party -- some switch)
cosponsor_cols = [col for col in bills if col.startswith('Cosponsor')]
keep_col = ['sponsor'] + cosponsor_cols

congress_names = bills[keep_col]

'''
# Create long version of name X congress
congress_names = bills[keep_col]                    # Keep only congress + name columns
congress_names = pd.melt(congress_names,            # Make long version
                         id_vars='congress', 
                         value_vars = ['sponsor'] + cosponsor_cols
                         )
congress_names.drop(columns=['variable'], inplace=True)
congress_names.rename(columns = {'value' : 'name_info'},
                      inplace=True)
congress_names['name_info'] = congress_names['name_info'].str.strip()
congress_names = congress_names.drop_duplicates()
congress_names = congress_names.dropna()

'''
congress_names = congress_names.values.ravel()      # Stack to single column
congress_names = pd.DataFrame(congress_names, columns=['name_info'])
congress_names = congress_names.dropna()
congress_names['name_info'] = congress_names['name_info'].str.strip()
congress_names = congress_names.drop_duplicates()
congress_names.reset_index(inplace=True, drop=True)

# Extract info in the square brackets
congress_names['info'] = congress_names['name_info'].str.extract(r'\[(.*?)\]')
congress_names['name_congress'] = congress_names['name_info'].str.replace(r'\[.*?\]', '', regex=True)
congress_names[['position', 'party', 'state']] = congress_names['info'].str.split('-', expand=True)

# make name lowercase for matching
congress_names['name_congress'] = congress_names['name_congress'].str.lower()


drop_col = ['info', 'position']
congress_names.drop(columns=drop_col, inplace=True)


###############
# %% 3. Get party time series
###############

# Create panel data
congress_parties = bills[['congress', 'sponsor'] + cosponsor_cols]
congress_parties = pd.melt(congress_parties,
                           id_vars = 'congress',
                           value_vars = ['sponsor'] + cosponsor_cols
                           )
congress_parties.drop(columns=['variable'], inplace=True)
congress_parties.rename(columns = {'value': 'name_info'},
                        inplace=True)

# Clean up
congress_parties['name_info'] = congress_parties['name_info'].str.strip()
congress_parties = congress_parties.drop_duplicates()
congress_parties = congress_parties.dropna()

# Extract info
congress_parties['info'] = congress_parties['name_info'].str.extract(r'\[(.*?)\]')
congress_parties['name_congress'] = congress_parties['name_info'].str.replace(r'\[.*?\]', '', regex=True)
congress_parties[['position', 'party', 'state']] = congress_parties['info'].str.split('-', expand=True)

congress_parties = congress_parties[['congress', 'name_info', 'party']]

# Hand code independents
congress_parties.loc[congress_parties['name_info'] == 'Smith, Bob [Sen.-I-NH]', 'party'] = "R"  # Bob Smith caucased with Reps
congress_parties.loc[congress_parties['party'].isin(["I", "ID"]), 'party'] = "D"                # All other independents as of 2025 have been D



###############
# %% 3. Create cosponsor df  - edges of the network, each is Bill X sponsor X cosponsor
###############

# Only use bills with 25 or fewer cosponsors for historical reasons
cosponsors = bills[bills['number_cosponsors'] <= 25]

# keep only legislation ID and the sponsor/cosponsor columns
keep_col = ['legislation_id', 'congress', 'sponsor'] + cosponsor_cols
cosponsors = cosponsors[keep_col]

# Melt to long df of edges
cosponsors = pd.melt(cosponsors,
                     id_vars=['legislation_id', 'congress', 'sponsor'], 
                     value_vars = cosponsor_cols, value_name='cosponsor')

cosponsors.drop(columns='variable', inplace=True)
cosponsors.dropna(subset='cosponsor', inplace=True)     # Drop if no cosponsor

cosponsors['sponsor'] = cosponsors['sponsor'].str.strip()
cosponsors['cosponsor'] = cosponsors['cosponsor'].str.strip()

# Drop duplicates & mistakes
cosponsors = cosponsors.drop_duplicates()
cosponsors = cosponsors[cosponsors['cosponsor'] != cosponsors['sponsor']]

del keep_col, cosponsor_cols



###############
# %% 4. Clean bills file
###############

# Drop unneeded vars
keep_col = ['legislation_id', 'congress', 'sponsor', 
            'number_cosponsors', 'title', 'latest_summary',
            'committees']
bills = bills[keep_col]
del keep_col



###############
# %% 5. Save
###############

bills.to_parquet('./data/bills.parquet')
cosponsors.to_parquet('./data/temp/cosponsors_pre.parquet')
congress_names.to_parquet('./data/temp/congress_names_pre.parquet')
congress_parties.to_parquet('./data/temp/congress_parties_pre.parquet')

