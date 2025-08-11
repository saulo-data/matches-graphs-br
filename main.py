#libraries
import streamlit as st 
import pandas as pd
import numpy as np
import networkx as nx
import matplotlib.pyplot as plt
from mplsoccer.pitch import Pitch, VerticalPitch
import seaborn as sns
from pymongo import MongoClient
import networkx as nx
from colors import *

#mongodb connection
client = MongoClient(st.secrets['url_con'])
db = client.football_data
col_matches = db.matches_graph

#some constants
LEAGUE_ID = st.secrets['league_id']
IMAGE_LEAGUE = st.secrets['image_league']
BINS = 5

#function to get the data of the selected match
@st.cache_data(show_spinner=False)
def get_match(home: str, away: str) -> dict:
    match = col_matches.find_one({'league_id': LEAGUE_ID, 'home': home, 'away': away})

    return match

#function to plot a static passing network
def create_plot_field(graph: nx.DiGraph, pos: dict, coach: str, color: str, venue: str) -> plt.figure:

    if venue == 'home':
        a = 0
        b = 0
        c = 1
    if venue == 'away':
        a = 120
        b = 80
        c = -1


    weights= nx.get_edge_attributes(graph, 'passes').values()

    fig, ax = plt.subplots(figsize=(15, 12))
    pitch = Pitch(pitch_type='statsbomb', line_color=lines)
    pitch.draw(ax=ax, constrained_layout=True)
    ax.text(x=102, y=-1.8, s=f'Coach - {coach}', fontsize=13, fontweight='bold', color=highlight, ha='center', va='center')
    nx.draw(G=graph, with_labels=True, node_size=400, node_color=color, edgecolors=lines, edge_color=weights, width=[w*0.4 for w in weights], 
                edge_cmap=sequential_1, font_weight='bold', font_size=8.8,
                pos={str(p['player']).strip(): (((p['x'] - a ) * c), ((p['y']) - b) * c) for p in pos}, ax=ax)


    fig.patch.set_facecolor(background)
    for ax in fig.get_axes():
        ax.set_facecolor(background)

    return fig

#function to plot the average positions(defensive and offensive)
def create_average_pos_plot(df: pd.DataFrame) -> plt.figure:
    df_pos_ata = df[df['x'] >= 60]
    df_pos_def = df[df['x'] < 60] 


    fig, ax = plt.subplots(figsize=(6, 9))

    ax.set_title('Average Positions', c=highlight, fontsize=15, fontweight='bold')
    vpitch.draw(ax=ax, constrained_layout=True)
    vpitch.scatter(data=df_pos_ata, x=df_pos_ata['x'].mean(), y=df_pos_ata['y'].mean(), color=highlight, s=500, alpha=0.85, ax=ax)
    vpitch.scatter(data=df_pos_def, x=df_pos_def['x'].mean(), y=df_pos_def['y'].mean(), color=highlight, s=500, alpha=0.85, ax=ax)

    fig.patch.set_facecolor(background)
    for ax in fig.get_axes():
        ax.set_facecolor(background)
    
    return fig

#function to create histogram to analyze the centrality measures
def create_histogram(graph: nx.DiGraph, measure: str, color: str, bins: int) -> plt.figure:    
    if measure == 'betweenness centrality':
        func = nx.betweenness_centrality(graph)
    elif measure == 'closeness centrality':
        func = nx.closeness_centrality(graph)
    elif measure == 'eigenvector centrality':
        func = nx.eigenvector_centrality(graph)
    elif measure == 'pagerank':
        func = nx.pagerank(graph)
    else:
        return False
    fig, ax = plt.subplots(figsize=(7, 5))

    ax.spines['top'].set_visible(False)
    ax.spines['right'].set_visible(False)
    ax.spines['bottom'].set_color(text)
    ax.spines['left'].set_color(text)
    ax.set_xlabel(f"{measure.title()}", fontweight='bold', c=text)
    ax.set_ylabel(' ')
    ax.tick_params(
        axis='both', 
        which='both', 
        colors=text,
    )
    ax.set_xlabel(f'{measure.title()}', fontweight='bold', c=text)
    ax.set_ylabel(' ')
    sns.histplot(x=list(func.values()), color=color, bins=bins, ax=ax)

    fig.patch.set_facecolor(background)
    for ax in fig.get_axes():
        ax.set_facecolor(background)

    return fig

#function to plot passing network with substitutions
@st.fragment
def plot_players_pos(home_graph: nx.DiGraph, away_graph: nx.DiGraph, home: list, away: list, pos_h: dict, pos_a: dict) -> None:
    all_players_home = [k['player'] for k in home]
    first_eleven_home = [k['player'] for k in home if k['titular'] == True]

    all_players_away = [k['player'] for k in away]
    first_eleven_away = [k['player'] for k in away if k['titular'] == True]    

    col_a, col_b = st.columns(2)

    with col_a:
        options_home = st.multiselect(label="Home Players", options=all_players_home, default=first_eleven_home, max_selections=11)
    with col_b:
        options_away = st.multiselect(label="Away Players", options=all_players_away, default=first_eleven_away, max_selections=11)

    H = nx.subgraph(home_graph, options_home)
    A = nx.subgraph(away_graph, options_away)

    min_passes = 6
    width = 15
    proportion = 80 / 120
    font_size = 6.5

    weights_home= nx.get_edge_attributes(H, 'passes').values()
    edges_home = [e for e, w in zip(H.edges(), weights_home) if w >= min_passes]

    weights_away= nx.get_edge_attributes(A, 'passes').values()
    edges_away = [e for e, w in zip(A.edges(), weights_away) if w >= min_passes]

    pos_home = {str(p['player']).strip(): (p['x'], p['y']) for p in pos_h if p['player'] in options_home}
    pos_away = {str(p['player']).strip(): (((p['x'] - 120 ) * -1), ((p['y']) - 80) * -1) for p in pos_a if p['player'] in options_away}

    

    fig, ax = plt.subplots(figsize=(width, width * proportion))
    pitch = Pitch(pitch_type='statsbomb', line_color=lines)
    pitch.draw(ax=ax, constrained_layout=True)

    nx.draw_networkx_nodes(H, ax=ax, node_color=color_home, node_size=200, pos=pos_home)
    nx.draw_networkx_labels(H, ax=ax, pos=pos_home, font_weight='bold', font_size=font_size)
    nx.draw_networkx_edges(H, pos=pos_home, edgelist=edges_home, edge_color=lines)

    nx.draw_networkx_nodes(A, ax=ax, node_color=color_away, node_size=200, pos=pos_away)
    nx.draw_networkx_labels(A, ax=ax, pos=pos_away, font_weight='bold', font_size=font_size)
    nx.draw_networkx_edges(A, pos=pos_away, edgelist=edges_away, edge_color=color_away)

    fig.patch.set_facecolor(background)
    ax.set_facecolor(background)

    st.pyplot(fig)

#get the list of teams names
home_teams = list(col_matches.find({'league_id': LEAGUE_ID}).distinct('home'))
away_teams = list(col_matches.find({'league_id': LEAGUE_ID}).distinct('away'))

#streamlit page configuration
st.set_page_config(
    page_title="Matches Graphs", 
    layout='wide'
)

#create a sidebar
with st.sidebar:
    st.image('static/image.jpeg', 
             caption="Saulo Faria - Data Scientist Specialized in Football")
    st.write("This Web App was designed in order to get the graphs of all matches of Brazilian Serie A. If you want to have more details about these matches, send an email to saulo.foot@gmail.com")

    st.subheader("My links (pt-br)")
    st.link_button("Aposta Consciente", "https://go.hotmart.com/Q98778179P?dp=1", use_container_width=True)
    #st.link_button("Udemy", "https://www.udemy.com/user/saulo-faria-3/", use_container_width=True)
    st.link_button("Instagram", "https://www.instagram.com/saulo.foot/", use_container_width=True)
    st.link_button("X", "https://x.com/fariasaulo_", use_container_width=True)
    st.link_button("Youtube", "https://www.youtube.com/channel/UCkSw2eyetrr8TByFis0Uyug", use_container_width=True)
    st.link_button("LinkedIn", "https://www.linkedin.com/in/saulo-faria-318b872b9/", use_container_width=True)

col_header, col_image = st.columns([7, 2], vertical_alignment='center')

with col_header:
    st.header("Brazilian Serie A 2025 Matches Graphs and its Centrality Measures")
with col_image:
    st.image(IMAGE_LEAGUE, width=100)

#form to select the teams
with st.form('my-form'):
    if 'home' not in st.session_state:
        st.session_state['home'] = 'Flamengo'
    
    if 'away' not in st.session_state:
        st.session_state['away'] = 'Internacional'

    col1, col2 = st.columns(2)

    with col1:
        home = st.selectbox(label="Select a Home Team", options=home_teams, index=0)
    
    with col2:
        away = st.selectbox(label="Select an Away Team", options=away_teams, index=1)

    submitted = st.form_submit_button("Submit")

    if submitted:
        try:
            st.session_state['home'] = home
            st.session_state['away'] = away

            match = get_match(st.session_state['home'], st.session_state['away'])

            home_graph = nx.node_link_graph(match['home_graph'], edges="links")
            st.session_state['home_graph'] = home_graph

            away_graph = nx.node_link_graph(match['away_graph'], edges="links")
            st.session_state['away_graph'] = away_graph

            pos_h = match['home_pos']
            st.session_state['pos_h'] = pos_h

            pos_a = match['away_pos']
            st.session_state['pos_a'] = pos_a

            coach_home = match['coach_home']
            coach_away = match['coach_away']
            df_pos_h = pd.DataFrame(pos_h)
            df_pos_a = pd.DataFrame(pos_a)
            lineup_home = match['lineup_home']
            lineup_away = match['lineup_away']
            st.session_state['lineup_home'] = lineup_home
            st.session_state['lineup_away'] = lineup_away

            pitch = Pitch(pitch_type='statsbomb', line_color=lines)
            vpitch = VerticalPitch(pitch_type='statsbomb', line_color=lines)

            tab1, tab2 = st.tabs([f"{st.session_state['home']}", f"{st.session_state['away']}"])

            with tab1:        
                col3, col4 = st.columns([3, 1])

                with col3:
                    st.pyplot(create_plot_field(graph=home_graph, pos=pos_h, coach=coach_home, color=color_home, venue='home'))
                with col4:
                    st.pyplot(create_average_pos_plot(df=df_pos_h))

                col5, col6, col7, col8 = st.columns(4)

                with col5:
                    st.pyplot(create_histogram(graph=home_graph, measure='betweenness centrality', color=color_home, bins=BINS))

                with col6:
                    st.pyplot(create_histogram(graph=home_graph, measure='closeness centrality', color=color_home, bins=BINS))
                
                with col7:
                    st.pyplot(create_histogram(graph=home_graph, measure='eigenvector centrality', color=color_home, bins=BINS))

                with col8:
                    st.pyplot(create_histogram(graph=home_graph, measure='pagerank', color=color_home, bins=BINS))

            with tab2:        
                col9, col10 = st.columns([3, 1])

                with col9:
                    st.pyplot(create_plot_field(graph=away_graph, pos=pos_a, coach=coach_away, color=color_away, venue='away'))
                with col10:
                    st.pyplot(create_average_pos_plot(df=df_pos_a))

                col11, col12, col13, col14 = st.columns(4)

                with col11:
                    st.pyplot(create_histogram(graph=away_graph, measure='betweenness centrality', color=color_away, bins=BINS))

                with col12:
                    st.pyplot(create_histogram(graph=away_graph, measure='closeness centrality', color=color_away, bins=BINS))
                
                with col13:
                    st.pyplot(create_histogram(graph=away_graph, measure='eigenvector centrality', color=color_away, bins=BINS))

                with col14:
                    st.pyplot(create_histogram(graph=away_graph, measure='pagerank', color=color_away, bins=BINS))          


        except Exception as e:
            st.write("Ops! Something Wrong Has Happened! Maybe This Match Didn't Occurred Yet")

st.divider()

try:
    st.subheader("Make Substitutions to Observe how the Dynamic of the Match Has Changed")
    st.write("Only connections with 5 or more passes is shown")
    plot_players_pos(home_graph=st.session_state['home_graph'], away_graph=st.session_state['away_graph'], 
                     home=st.session_state['lineup_home'], away=st.session_state['lineup_away'], 
                     pos_h=st.session_state['pos_h'], pos_a=st.session_state['pos_a'])

#pretend from show any error before selecting the teams
except:
    st.write(' ')
