#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Computes basic network stats on Senators
- centrality measures
Uses cleaned data from previous steps
Also plots a graph of the Senate network across all congresses
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

# Find the top 20 senators by pagerank centrality
quantile = 1 - 20 / centralities.shape[0]
pagerank_20 = centralities['pagerank'].quantile(quantile)


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

nodes_graph['size'] = (nodes_graph['pagerank']*10000 + 1)

nodes_graph.loc[nodes_graph['pagerank'] < pagerank_20, 'name'] = " "

nodes_graph = pd.merge(nodes_graph, biographical[['party']],
                       how='left',
                       left_on='icpsr',
                       right_index = True
                       )
nodes_graph['color'] = 'blue'
nodes_graph['color'].loc[nodes_graph['party']=='R'] = 'red'
                       

node_attr_dict = nodes_graph.set_index('icpsr').to_dict('index')  # Convert DataFrame to dictionary
nx.set_node_attributes(network_graph, node_attr_dict)

node_sizes = [network_graph.nodes[n]['size'] for n in network_graph.nodes()]
edge_weights = [network_graph[u][v]['weight'] for u, v in network_graph.edges()]
node_labels = {n: network_graph.nodes[n].get('name', n) for n in network_graph.nodes()}
node_colors = [network_graph.nodes[n]['color'] for n in network_graph.nodes()]

    
# save network
nx.write_gexf(network_graph, './graphs/network.gexf')


# %% Plot

plt.figure(figsize=(6.5, 6.5))


# Set node positions
default_k = (nodes_graph.shape[0])**0.5
pos = nx.spring_layout(network_graph, k=5/default_k, seed=42)      


# Draw nodes
nx.draw_networkx_nodes(network_graph, pos, 
                       node_size = node_sizes, 
                       node_color = node_colors, edgecolors='black')

# Draw edges with thickness based on weight
nx.draw_networkx_edges(network_graph, pos, 
                       width=edge_weights, arrowsize=6, 
                       edge_color='gray', alpha=0.7)

# Draw labels
label_offset = 0.03  # Adjust this value to control the offset amount
pos_labels = {node: (x, y + label_offset) for node, (x, y) in pos.items()}
nx.draw_networkx_labels(network_graph, pos_labels, labels=node_labels, font_size=10)

# Export figure
plt.savefig('./graphs/graph_network.png', bbox_inches='tight', dpi=300)
plt.show()



# %% Evaluate centrality measures

centrality_vars = ['clustering', 'degree', 'pagerank']

# Regression
X = centralities[['pagerank']]
X = sm.add_constant(X)
Y = centralities[['clustering']]

model = sm.OLS(Y, X).fit(cov_type='HC0')
model.summary()

# Cross-correlations
corr_matrix = centralities[centrality_vars].corr()
corr_matrix.to_csv('./tables/centrality_correlations.csv')

# Export raw data
centralities = pd.merge(centralities, biographical[['name_dw', 'party', 'state']],
                        how='left',
                        left_on = 'icpsr',
                        right_index=True)
centralities.to_csv('./tables/centralities.csv')