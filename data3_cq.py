#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Reads and cleans CQ data -- some biographical data of congressmen
"""

# %% Preamble

import numpy as np
import pandas as pd
import os
import datetime as dt

os.chdir(os.path.dirname(os.path.abspath(__file__)))

'''
Note: If a person shows up multiple times, district or party changed. Start and end years are for each spell
'''

'''
Known data issues:
- mil2 and mil3 sometimes popualated if mil1 is 'did not serve' -- this seems to be a mistake, and mil1 is correct
- Dates of services sometimes wrong, especially for multi-stint legislators
- Use DW-nominate dates as canon (comes up in matching w/ ICPSRs)
'''

# %% Read data 

cq = pd.read_csv('./data/cq_congress/senate.csv', skiprows=2)


# variable names lowercase/underscores
cq.columns = [x.lower() for x in cq.columns]
cq.columns = [x.replace(' ', '_') for x in cq.columns]


# Drop those who ended before the 93rd congress 
cq['end'] = pd.to_datetime(cq['end'])
cq = cq[cq['end'] > pd.to_datetime('1973-01-03')]




# %% Create names

# Replace middle nan with empty string
cq['middle'] = cq['middle'].fillna('')

# Create full name from first + middle + last
cq['name_cq'] = cq['last'] + ", " + cq['first'] + ' ' + cq['middle']

cq.drop(columns=['first', 'middle', 'last', 'suffix', 'nickname'], inplace=True)

# Drop if name is nan
cq = cq[cq['name_cq'].notna()]



# %%  Create categorical vars (mostly from string data)


##### Military services #####

cq['military'] = 1
cq.loc[cq['mil1'] == 'Did not serve', 'military'] = 0

cq.drop(columns = ['mil1', 'mil2', 'mil3'], inplace=True)


##### Education #####

educ = cq['educational_attainment'].unique() # Unique values of educational_attainment

cq['educ'] = ""
cq.loc[cq['educational_attainment'].isin(['High School graduate', 'Unknown']), 'educ'] = "HS"
cq.loc[cq['educational_attainment'].isin(["Bachelor's degree", "Associate degree"]), 'educ'] = "College"
cq.loc[cq['educational_attainment'].isin(["Master's degree", "Doctorate degree", "Professional degree"]), 'educ'] = "Higher"

cq.drop(columns = ['educational_attainment'], inplace=True)



##### Job types #####

# job types
job_cols = [col for col in cq if col.startswith('jobtype')]

# Clean jobtype# strings
for c in job_cols:
    cq[c] = cq[c].fillna('')
    cq[c] = cq[c].str.lower()
    cq[c] = cq[c].str.replace(r'[\(\)\,\.\/]', '', regex=True)

# Unique job types
jobtypes = np.array("")
for c in job_cols:
    jobtypes = np.append(jobtypes, cq[c].unique())
jobtypes = np.unique(jobtypes)

# Create dummies for each job from jobtype1 - jobtype5 (so a person can have multiple 1s)
for job in jobtypes:
    cq['job_' + job] = 0

    for c in job_cols:
        cq.loc[cq[c].str.contains(job), 'job_' + job] = 1

cq.drop(columns = job_cols, inplace=True)



##### Religion #####

religions = cq['religion'].unique()

christian = ['Baptist',  'Methodist', 'Eastern Orthodox', 'Episcopalian', 
             'Protestant', 'Congregationalist', 'Christian', 'Presbyterian', 
             'Disciples of Christ', 'Lutheran', 'Evangelical', 'Unitarian',
             'Southern Baptist', 'Evangelical Lutheran',  'Nondenominational', 
             'Independent Christian', 'Church of Christ', 'Christian Reformed',
             'Seventh-Day Adventist', 'United Church of Christ', 'Serbian Orthodox',
             'Greek Orthodox', 'Non-denominational Prostestant',
             'Independent Bible Church', 'Quaker', 'Nazarene', 'Reformed Church',
             'Christian Missionary Alliance', 'African Methodist Episcopalian',
             'United Methodist', 'Non-denominational Christian', 'Assembly of God', 
             'Christian Scientist', 'Pentecostal', 'Associated Reform Presbyterian',
             'Church of God', 'Society of Friends', 'Apostolic Christian',
             'Unitarian Universalist', 'French Huguenot', 'Anglican',
             'Central Schwenkfelder']

catholic = ['Roman Catholic',  'Eastern Catholic', 'Maronite Catholic']


# make religion indicators
cq['relig'] = ""
cq.loc[cq['religion'].isin(christian), 'relig'] = "Christ."
cq.loc[cq['religion'].isin(catholic), 'relig'] = "Catholic"
cq.loc[~cq['religion'].isin(catholic + christian), 'relig'] = "Other"


##### Sex #####

cq['male'] = 0
cq.loc[cq['sex']==2, 'male'] = 1


##### Race #####
cq['white'] = 0
cq.loc[cq['race']=='White', 'white'] = 1


##### Party #####
cq['party'] = cq['party'].str.slice(0,1)



# %% Clean and save needed data 
# Note: currently drops job variables and party variable

job_cols = [col for col in cq if col.startswith('job_')]
keep_cols = ['name_cq', 'state', 'relig', 'white', 'male', 'educ', 'military'] # + job_cols

cq = cq[keep_cols]
cq = cq.drop_duplicates()

# Save
cq.to_parquet('./data/temp/cq.parquet')
