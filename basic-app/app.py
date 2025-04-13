# %% Preamble
# Shiny related
import faicons as fa
import plotly.express as px
from shinywidgets import render_plotly

from shiny import reactive, render, req
from shiny.express import input, ui

# Pandas/plotly
import matplotlib.pyplot as plt
import pandas as pd

# NetworkX
import networkx as nx
import plotly.graph_objects as go


# OS
import os
os.chdir(os.path.dirname(os.path.abspath(__file__)))

#%% Load data

ergm = pd.read_csv('ergm_results.csv')

ergm = ergm[['term', 'congress', 'estimate', 'std.error']]
keep_estimates = ['absdiff.sum.nominate_dim1', 'nodematch.sum.party']
ergm = ergm.loc[ergm['term'].isin(keep_estimates)]

# Pivot to wide based on term
ergm = ergm.pivot(index=['congress'], columns='term', values=['estimate', 'std.error'])
ergm.columns = ['_'.join(map(str, col)).strip() for col in ergm.columns.values]
ergm = ergm.reset_index()

# Rename columns
ergm.rename(columns = {'estimate_absdiff.sum.nominate_dim1': 'absdiff_dw',
                       'estimate_nodematch.sum.party': 'same_party',
                       'std.error_absdiff.sum.nominate_dim1': 'absdiff_dw_se',
                       'std.error_nodematch.sum.party': 'same_party_se'},
            inplace=True)
ergm['year'] = ergm['congress'] * 2 + 1787

# errors
ergm['absdiff_dw_95'] = 1.96*ergm['absdiff_dw_se']
ergm['same_party_95'] = 1.96*ergm['absdiff_dw_95']




##### Network #####

# Load network data from GEXF file
G = nx.read_gexf('network.gexf')

# Node positions
pos = nx.spring_layout(G, seed=42)  # positions for all nodes
for node in G.nodes():
    G.nodes[node]['pos'] = pos[node]



# %% Shiny app


# Encourage fill screen
ui.page_opts(title="Senate networks dashboard", fillable=True)

##### Sidebar #####

with ui.sidebar():
    # Variable selecter
    ui.input_selectize(
        "var", "Select variable",
        ["same_party", "absdiff_dw"],
    )
    # Input for custom x-axis range
    ui.input_slider(
        "x_range", "Select year range",
        min(ergm['year']), max(ergm['year']),
        value=(min(ergm['year']), max(ergm['year'])),
        sep = ""
    )


##### Regression time series #####

# Line plots of estimates
with ui.card(full_screen=True):
    ui.card_header("ERGM point estimates")
    @render_plotly
    def hist():
        # Filter data based on selected year range
        filtered_data = ergm[(ergm['year'] >= input.x_range()[0]) & (ergm['year'] <= input.x_range()[1])]
        
        # Plot selected variable with error bars
        error_y = f"{input.var()}_95"
        return px.line(filtered_data, y=input.var(), x='year', error_y=error_y)    


##### Network #####

with ui.card(full_screen=True):
    ui.card_header("Network visualization")
    @render_plotly
    def network():
        # Extract node positions
        node_x = [G.nodes[node]['pos'][0] for node in G.nodes()]
        node_y = [G.nodes[node]['pos'][1] for node in G.nodes()]

        # Create edge traces
        edge_x = []
        edge_y = []
        for edge in G.edges():
            x0, y0 = G.nodes[edge[0]]['pos']
            x1, y1 = G.nodes[edge[1]]['pos']
            edge_x.extend([x0, x1, None])
            edge_y.extend([y0, y1, None])

        edge_trace = go.Scatter(
            x=edge_x, y=edge_y,
            line=dict(width=0.5, color='#888'),
            hoverinfo='none',
            mode='lines'
        )

        # Create node trace
        node_trace = go.Scatter(
            x=node_x, y=node_y,
            mode='markers',
            marker=dict(
            size=10,
            color='blue',
            line_width=2
            ),
            text=list(G.nodes()),
            hoverinfo='text'
        )
        # Add labels to nodes
        node_trace.text = [G.nodes[node].get('name', node) for node in G.nodes()]
        
        # Create figure
        fig = go.Figure(data=[edge_trace, node_trace],
                layout=go.Layout(
                    showlegend=False,
                    hovermode='closest',
                    margin=dict(b=0, l=0, r=0, t=0),
                    xaxis=dict(showgrid=False, zeroline=False),
                    yaxis=dict(showgrid=False, zeroline=False)
                ))
        return fig
