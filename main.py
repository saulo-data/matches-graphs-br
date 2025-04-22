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

client = MongoClient(st.secrets['url_con'])
db = client.football_data
col_matches = db.matches_graph

LEAGUE_ID = st.secrets['league_id']
IMAGE_LEAGUE = st.secrets['image_league']
BINS = 5


@st.cache_data(show_spinner=False)
def get_match(home: str, away: str) -> dict:
    match = col_matches.find_one({'league_id': LEAGUE_ID, 'home': home, 'away': away})

    return match

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
    



home_teams = list(col_matches.find({'league_id': LEAGUE_ID}).distinct('home'))
away_teams = list(col_matches.find({'league_id': LEAGUE_ID}).distinct('away'))

st.set_page_config(
    page_title="Matches Graphs", 
    layout='wide'
)

with st.sidebar:
    st.image('static/image.jpeg', 
             caption="Saulo Faria - Data Scientist Specialized in Football")
    st.write("This Web App was designed in order to get the graphs of all matches of Brazilian Serie A. If you want to have more details about these matches, send an email to saulo.foot@gmail.com")

    st.subheader("My links (pt-br)")
    st.link_button("Aposta Consciente", "https://go.hotmart.com/Q98778179P?dp=1", use_container_width=True)
    st.link_button("Udemy", "https://www.udemy.com/user/saulo-faria-3/", use_container_width=True)
    st.link_button("Instagram", "https://www.instagram.com/saulo.foot/", use_container_width=True)
    st.link_button("X", "https://x.com/fariasaulo_", use_container_width=True)
    st.link_button("Youtube", "https://www.youtube.com/channel/UCkSw2eyetrr8TByFis0Uyug", use_container_width=True)

col_header, col_image = st.columns([7, 2], vertical_alignment='center')

with col_header:
    st.header("Brazilian Serie A Matches Graphs and its Centrality Measures")
with col_image:
    st.image(IMAGE_LEAGUE, width=100)

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
            away_graph = nx.node_link_graph(match['away_graph'], edges="links")
            pos_h = match['home_pos']
            pos_a = match['away_pos']        
            coach_home = match['coach_home']
            coach_away = match['coach_away']
            df_pos_h = pd.DataFrame(pos_h)
            df_pos_a = pd.DataFrame(pos_a)

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

        






