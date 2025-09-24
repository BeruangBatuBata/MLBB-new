import streamlit as st
import requests
import os

# --- CONSTANTS (Moved from your notebook) ---
# NOTE: It's better practice to store API keys as Streamlit secrets,
# but for this conversion, we'll keep it here for simplicity.
API_KEY = "pIfcpzOZFhSaLGG5elRsP3s9rnL8NPr1Xt194SxPrryEfvb3cOvvNVj0V83nLAyk0FNuI6HtLCGfNvYpyHLjrKExyvOFYEQMsxyjnrk9H1KDU84ahTW3JnRF9FLIueN2"
HEADERS = {"Authorization": f"Apikey {API_KEY}", "User-Agent": "HeroStatsCollector/1.0"}
BASE_PARAMS = {"wiki": "mobilelegends", "limit": 500}

# List of tournaments (Moved from your notebook)
# We combine them into one dictionary for easier access
ALL_TOURNAMENTS = {
    'MPL ID Season 14': {'path': 'MPL/Indonesia/Season_14', 'region': 'Indonesia', 'year': 2024, 'live': False},
    'MPL PH Season 13': {'path': 'MPL/Philippines/Season_13', 'region': 'Philippines', 'year': 2024, 'live': False},
    'MSC 2024': {'path': 'MSC/2024', 'region': 'International', 'year': 2024, 'live': False},
    'MPL ID Season 15': {'path': 'MPL/Indonesia/Season_15', 'region': 'Indonesia', 'year': 2025, 'live': False},
    'MPL PH Season 15': {'path': 'MPL/Philippines/Season_15', 'region': 'Philippines', 'year': 2025, 'live': False},
    'MPL ID Season 16': {'path': 'MPL/Indonesia/Season_16', 'region': 'Indonesia', 'year': 2025, 'live': True},
    'MPL PH Season 16': {'path': 'MPL/Philippines/Season_16', 'region': 'Philippines', 'year': 2025, 'live': True},
    'MPL MY Season 16': {'path': 'MPL/Malaysia/Season_16', 'region': 'Malaysia', 'year': 2025, 'live': True},
    'VMC 2025 Winter': {'path': 'Vietnam_MLBB_Championship/2025/Winter', 'region': 'Vietnam', 'year': 2025, 'live': True},
    'MPL MENA S8': {'path': 'MPL/MENA/Season_8', 'region': 'MENA', 'year': 2025, 'live': True},
    'MCC S6': {'path': 'MLBB_Continental_Championships/Season_6', 'region': 'EECA', 'year': 2025, 'live': True},
    'China Masters 2025': {'path': 'MLBB_China_Masters/2025', 'region': 'China', 'year': 2025, 'live': True},
    'MTC S5': {'path': 'MTC_Turkiye_Championship/Season_5', 'region': 'Turkey', 'year': 2025, 'live': True},
}


@st.cache_data(ttl=3600) # Cache for 1 hour
def fetch_tournament_matches(tournament_path):
    """
    Load match data from Liquipedia API using tournament path.
    This function is cached by Streamlit to avoid re-fetching data.
    """
    try:
        params = BASE_PARAMS.copy()
        params['conditions'] = f"[[parent::{tournament_path}]]"
        url = "https://api.liquipedia.net/api/v3/match"

        resp = requests.get(url, headers=HEADERS, params=params)
        resp.raise_for_status() # This will raise an error for bad responses (4xx or 5xx)

        matches = resp.json().get("result", [])
        st.toast(f"Loaded {len(matches)} matches for {tournament_path}", icon="✅")
        return matches

    except requests.exceptions.RequestException as e:
        st.error(f"API Error fetching {tournament_path}: {e}")
        return []
    except Exception as e:
        st.error(f"An unexpected error occurred for {tournament_path}: {e}")
        return []
