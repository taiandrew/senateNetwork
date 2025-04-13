
Author: Andrew Tai
Update: March 20 2025

This is the readme for the senateNetwork project.

Organization:
- Main directory contains the draft and code
- /data/ contains the raw data and cleaned data. Sources at end
- /graphs/ contains outputted graphs
- /tables/ contains outputted tables
- /tags/ is old versions, no longer used


Code: 

Overall principle to recreate: run data?, match?, then reg? in order
Outputs results in /graphs/ and /tables/

- data?_xxxxxxxx.py programs clean the raw data from original sources. Run in numeric order. Do not need to run these if data aren't updated
- match?_xxxxxx.py programs merge the cleaned data from these steps. The programs implement a fuzzy match to match on string names of Senators between sources.
- merge?_xxxxx.py merges the different datafiles to produce "database" files to use for analyses

Note: You can run main_data.py to run all the above programs in order.

- reg1_ergm.R computes ERGM network regressions in R
- reg2_network_analysis.py computes basic network statistics
- reg3_graph_ergm.py plots coefficients from the ERGMs


Data sources:
- Library of Congress for data on bills (more instructions in folder)
- DW Nominate for ideology scores and some bio data (see citation in paper)
- CQ data -- from UC Berkeley library