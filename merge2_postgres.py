#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Sat Apr  5 10:04:08 2025

@author: andrewtai
"""

'''
IMPORTANT:
In terminal, run
    conda activate postgres
else it won't properly work
Afterwards:
    conda deactivate
'''

#%% Premble

import psycopg2
import sqlalchemy as sa
import pandas as pd

import os

os.chdir(os.path.dirname(os.path.abspath(__file__)))

# %% SQL

# Read data
bills = pd.read_parquet('./data/bills.parquet')
biographical = pd.read_parquet('./data/biographical.parquet')
cosponsors = pd.read_parquet('./data/cosponsors.parquet')

# Connect to local database
engine = sa.create_engine(
    'postgresql://postgres:teased*REVEALS8storing@localhost:5432/senate_network')


biographical.to_sql('biographical', engine, if_exists='replace')
cosponsors.to_sql('cosponsors', engine, if_exists='replace')
bills.to_sql('bills', engine, if_exists='replace')

# Querying for the list of table names
with engine.connect() as connection:
    tables = connection.execute(sa.text("SELECT table_name FROM information_schema.tables WHERE table_schema='public'"))
    for table in tables:
        print(table[0])

# disconnect
engine.dispose()

