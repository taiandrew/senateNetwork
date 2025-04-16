#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Tue Apr 15 22:52:44 2025

@author: andrewtai
"""

# %% Preamble

import numpy as np
import pandas as pd
import networkx as nx

import statsmodels.api as sm

import matplotlib.pyplot as plt

import os
os.chdir(os.path.dirname(os.path.abspath(__file__)))


# %% Open data and delcare network

edges = pd.read_parquet('./data/edges.parquet')
biographical = pd.read_parquet('./data/biographical.parquet')

# Create network
network = nx.from_pandas_edgelist(edges, 
                                  source='cosponsor_icpsr', target='sponsor_icpsr', 
                                  edge_attr = 'weight', 
                                  create_using=nx.DiGraph())  # Use nx.Graph() for undirected


# Flatten bio data with ICPSR as index, keep last values of everything
biographical = biographical.groupby('icpsr', as_index=True).last()

biographical['lname'] = biographical['name_dw'].str.split(',').str[0]
biographical['fname'] = biographical['name_dw'].str.split(',').str[1].str[1]
biographical['name'] = biographical['fname'] + ". " + biographical['lname']




# %% Analysis

# Weighted Degree Centrality
weighted_degree = network.degree(weight='weight')
weighted_degree = dict(weighted_degree)

# Clustering coefficients
clustering_coeffs = nx.clustering(network, weight='weight')

# Google pagerank
pagerank_centrality = nx.pagerank(network, weight='weight')

# Combine using key as index
centralities = pd.DataFrame.from_dict(weighted_degree, orient='index').reset_index()
centralities.columns = ['icpsr', 'degree']
centralities['clustering'] = centralities['icpsr'].map(clustering_coeffs)
centralities['pagerank'] = centralities['icpsr'].map(pagerank_centrality)
centralities['name'] = centralities['icpsr'].map(biographical['name'])

del weighted_degree, clustering_coeffs, pagerank_centrality



# %% Get data to visualize

'''
Edge weight only >= 10 connections
Node size by pagerank centrality
Top 20 senators by name
'''

# Edges
edges_graph = edges.copy()

# Reweight edges
edges_graph['weight'] = np.log(edges_graph['weight'])/2     # Make edges logarithmic proportional to bills sum




network_graph = nx.from_pandas_edgelist(edges_graph, 
                                        source='cosponsor_icpsr', target='sponsor_icpsr', 
                                        edge_attr = 'weight', 
                                        create_using=nx.DiGraph())  # Use nx.Graph() for undirected

# Remove if original weight < 10 (need to do this after forming network to make sure nodes are still there)
edges_to_remove = [(u, v) for u, v, d in network_graph.edges(data=True) if d['weight'] < np.log(10)/2]    
network_graph.remove_edges_from(edges_to_remove)


# Node sizes and names and parties ; only top 20 by name
nodes_graph = centralities[['icpsr', 'pagerank', 'name']]

nodes_graph['size'] = (nodes_graph['pagerank']*3000 + 1)

nodes_graph = pd.merge(nodes_graph, biographical[['party']],
                       how='left',
                       left_on='icpsr',
                       right_index = True
                       )
nodes_graph['color'] = 'blue'
nodes_graph.loc[nodes_graph['party']=='R', 'color'] = 'red'
                       

node_attr_dict = nodes_graph.set_index('icpsr').to_dict('index')  # Convert DataFrame to dictionary
nx.set_node_attributes(network_graph, node_attr_dict)

# Save
nx.write_gexf(network_graph, './graphs/network.gexf')

