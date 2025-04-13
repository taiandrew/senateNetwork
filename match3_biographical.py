#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Merges the files from previous two programs into a biographical dataset of Senators
"""

# %% Preamble

import numpy as np
import pandas as pd
import os

from fuzzywuzzy import fuzz
from fuzzywuzzy import process

os.chdir(os.path.dirname(os.path.abspath(__file__)))

# %% Open data

cq = pd.read_parquet('./data/temp/cq_icpsr.parquet')
congress_parties = pd.read_parquet('./data/temp/congress_parties.parquet')
dw_nominate = pd.read_parquet('./data/temp/dw_nominate.parquet')


# %% Merge together; DW Nominate is the base

biographical = dw_nominate.copy()

# Merge in CQ data
cq_cols = ['icpsr', 'relig', 'white', 'male', 'educ', 'military']
biographical = pd.merge(biographical, cq[cq_cols],
                        how='left',
                        left_on='icpsr',
                        right_on='icpsr',
                        )

# Merge in party data
party_cols = ['congress', 'icpsr', 'party']
biographical = pd.merge(biographical, congress_parties[party_cols],
                        how='left',
                        left_on = ['congress', 'icpsr'],
                        right_on = ['congress', 'icpsr']
                        )

biographical.to_parquet('./data/biographical.parquet')