# -*- coding: utf-8 -*-
"""
Read the data on bills & cosponsoring relationships

1. Open files on legislation (downloaded from Congressional library database)
2. Create copsonsor df (edge/long form)
3. Clean bills file
4. Create & clean list of observations (Congress/State/District/Name) for matching w/ ICPSRs
"""

'''
Known issues -
1. Data entry errors in the congressional downloaded data. Some bills nonsensical, or column shifts
    These should be dropped in the process as ICPSR ids are nan
2. Delegates, resident commissioners ,etc. are dropped -- this should be fine
'''

# %% Preamble

import numpy as np
import pandas as pd
import os

os.chdir(os.path.dirname(os.path.abspath(__file__)))

###############
# %% 1. Read congress data + light cleaning
###############

bills = []
# Read data
# list of all csv files in directory
filelist = os.listdir('./data/congress/')
# read in all csv files
for file in filelist:
    if file.endswith('.csv'):
        print(file)
        bills.append(pd.read_csv('./data/congress/' + file, skiprows=3, low_memory=False))

# append all dataframes
bills = pd.concat(bills)
bills = bills.copy()

del file, filelist

#bills = pd.read_csv('./data/congress/115_d.csv', skiprows=3)

# Rename columns
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


# Clean Congress number: keep first digits
bills['congress'] = bills['congress'].str.extract(r'(\d+)')
bills['congress'] = bills['congress'].astype(int)


###############
# %% 2. Create cosponsor df  - edges of the network, potentially multiple edges per pair of nodes
###############

# Only use bills with 25 or fewer cosponsors for historical reasons
bills_cosponsors = bills[bills['number_cosponsors'] <= 25]

# Keep bill ID numbers and cosponsor columns
cosponsor_col = [col for col in bills_cosponsors if col.startswith('Cosponsor')]
keep_col = ['legislation_id', 'congress', 'sponsor'] + cosponsor_col
cosponsors = bills_cosponsors[keep_col]

# Create long df with cosponsor names (note this drops any bills without cosponsors)
cosponsors = pd.melt(bills_cosponsors, id_vars = ['legislation_id', 'congress', 'sponsor'], 
                                       value_vars = cosponsor_col, value_name ='cosponsor')
cosponsors.drop(columns='variable', inplace=True)
cosponsors.dropna(subset='cosponsor', inplace=True)
del cosponsor_col, bills_cosponsors


###############
# %% 3. Clean bills file
###############

# Drop unneeded vars
keep_col = ['legislation_id', 'congress', 'sponsor', 
            'number_cosponsors', 'title', 'latest_summary',
            'committees']
bills = bills[keep_col]
del keep_col

# Bill subject areas
bill_subjects = pd.read_csv('./data/congress_policyareas/policyareas.csv')
bills = bills.merge(bill_subjects,
                    how='left',
                    left_on=['legislation_id', 'congress'],
                    right_on=['legislation_id', 'congress'])
del bill_subjects


###############
# %% 4. Prepare a list of names from Congressional data for matching, along with info from square brackets
###############

# Create list of unique names-congress
names_congress = pd.melt(cosponsors, id_vars='congress', 
                         value_name='name_info', 
                         value_vars=['sponsor', 'cosponsor'])
names_congress.drop(columns='variable', inplace=True)
names_congress = names_congress.drop_duplicates()          # remove duplicates

# Make new column from name with inside square brackets
names_congress['info'] = names_congress['name_info'].str.extract(r'\[(.*?)\]')

# create new column with name without inside square brackets
names_congress['name_congress'] = names_congress['name_info'].str.replace(r'\[.*?\]', '', regex=True)

# separate square bracket info on '-' into new columns
names_congress[['position', 'party', 'state', 'district']] = names_congress['info'].str.split('-', expand=True)
names_congress['district'] = names_congress['district'].str.replace(r'At Large', '1')
names_congress['district'] = names_congress['district'].str.replace(r'None', '0')
names_congress['district'] = names_congress['district'].astype(int)

# make name_clean lowercase
names_congress['name_congress'] = names_congress['name_congress'].str.lower()

# drop non representatives (delegates, resident comiss, senators)
names_congress= names_congress[names_congress['position']=='Rep.']


# %% 5. Save files
bills.to_parquet('./data/temp/bills_pre.parquet')
cosponsors.to_parquet('./data/temp/cosponsors_pre.parquet')
names_congress.to_parquet('./data/temp/names_congress_pre.parquet')
