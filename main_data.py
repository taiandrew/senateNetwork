#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Fri Mar  7 09:19:31 2025

@author: andrewtai
"""

import os
from subprocess import call

os.chdir(os.path.dirname(os.path.abspath(__file__)))


call(["python", "data1_congress.py"])
call(["python", "data2_dwnominate.py"])
call(["python", "data3_cq.py"])
call(["python", "match1_congress.py"])
call(["python", "match2_cq.py"])
call(["python", "match3_biographical.py"])
call(["python", "match4_network.py"])



