import streamlit as st
import pandas as pd
from utils.analysis_functions import calculate_hero_stats_for_team

st.set_page_config(layout="wide", page_title="Statistics Breakdown")

st.title("📊 Statistics Breakdown")

# --- Check for loaded data ---
if 'pooled_matches' not in st.session_state or not st.session_state['pooled_matches']:
    st.warning("Please select and load tournament data on the 'app.py' homepage first.")
    st.stop()

# --- Cache the calculation ---
# This prevents re-calculating the entire dataframe every time a widget is changed.
@st.cache_data
def get_stats_df(pooled_matches, team_filter):
    return calculate_hero_stats_for_team(pooled_matches, team_filter)

# --- UI Controls ---
pooled_matches = st.session_state['pooled_matches']

# Get a unique, sorted list of all teams from the data
all_teams = sorted(list(set(
    opp.get('name','').strip()
    for match in pooled_matches
    for opp in match.get("match2opponents", [])
    if opp.get('name')
)))

# --- Sidebar for page-specific filters ---
st.sidebar.header("Statistics Filters")
selected_team = st.sidebar.selectbox(
    "Filter by Team:",
    options=["All Teams"] + all_teams,
    index=0
)

# --- Main Page Content ---
st.info(f"Displaying hero statistics for **{selected_team}** in the selected tournaments: **{', '.join(st.session_state['selected_tournaments'])}**")

# Calculate or retrieve cached stats
with st.spinner(f"Calculating stats for {selected_team}..."):
    df_stats = get_stats_df(pooled_matches, selected_team)

if df_stats.empty:
    st.warning(f"No match data found for '{selected_team}' in the selected tournaments.")
else:
    # --- Sorting and Display Controls ---
    col1, col2, col3 = st.columns(3)
    with col1:
        sort_column = st.selectbox(
            "Sort by:",
            options=df_stats.columns,
            index=list(df_stats.columns).index("Presence (%)") # Default sort
        )
    with col2:
        sort_order = st.radio(
            "Order:",
            options=["Descending", "Ascending"],
            horizontal=True
        )

   # Sort the DataFrame
    df_display = df_stats.sort_values(
        by=sort_column,
        ascending=(sort_order == "Ascending")
    ).reset_index(drop=True)
    
    # --- ADD THIS LINE ---
    df_display.index += 1
    
    # --- Display Table and Download Button ---
    st.dataframe(df_display, use_container_width=True)

    csv = df_display.to_csv(index=False).encode('utf-8')
    with col3:
        st.download_button(
           label="📥 Download as CSV",
           data=csv,
           file_name=f'hero_stats_{selected_team}.csv',
           mime='text/csv',
        )
