"""
Uses results from reg1_ergm.R to plot graphs
(Run that file first)
"""

# %% Preamble

import numpy as np
import pandas as pd
import os

import matplotlib.pyplot as plt

os.chdir(os.path.dirname(os.path.abspath(__file__)))

# %% Import data
ergm = pd.read_csv('./data/ergm_results.csv')

ergm['year'] = ergm['congress'] * 2 + 1787


# %% Plot

# Senate == President
s1 = [1979, 1987, "red"]
s2 = [1993, 1995, "blue"]
s3 = [2009, 2011, "blue"]
s4 = [2019, 2021, "red"]


# Program for recurring plot
def plot_ergm(df, var_name, human_name, file_name):
    plot_data = df.loc[df['term']==var_name]
    plt.figure(figsize=(5, 4))
    plt.errorbar(plot_data['year'], plot_data['estimate'], yerr=2*plot_data['std.error'], fmt='o')
    plt.title(human_name)
    plt.xlabel('Congress starting in year')
    
    for i in range(ergm.shape[0]-1):
        plt.plot(plot_data['year'].iloc[i:i+2], plot_data['estimate'].iloc[i:i+2], 'k-')
    
    plt.axhline(0, color='k', linestyle='--')
    plt.xticks(np.arange(plot_data['year'].min(), plot_data['year'].max()+1, 4),
               rotation=45, ha='right')
    
    # Plot Senate == President
    plt.axvspan(s1[0], s1[1], color=s1[2], alpha=0.5)
    plt.axvspan(s2[0], s2[1], color=s2[2], alpha=0.5)
    plt.axvspan(s3[0], s3[1], color=s3[2], alpha=0.5)
    plt.axvspan(s4[0], s4[1], color=s4[2], alpha=0.5)
    
    # Save
    filepath = './graphs/graph_' + file_name
    plt.savefig(filepath, bbox_inches='tight', dpi=300)




# Plots
plot_ergm(ergm, 'absdiff.sum.nominate_dim1', 'Effect of ideological gap on cosponsorship', 'dwnom')
plot_ergm(ergm, 'nodematch.sum.party', 'Effect of same party on cosponsorship', 'party')
#plot_ergm(ergm, 'nodematch.state', 'Effect of same state on cosponsorship')
# plot_ergm(ergm, 'absdiff.born', 'Effect of similar age')
plot_ergm(ergm, 'nodefactor.sum.party.R', 'Effect of Republican', 'rep')