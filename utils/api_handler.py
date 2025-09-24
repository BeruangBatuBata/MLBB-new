import streamlit as st
import requests
import os
import json

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


@st.cache_data(ttl=3600)
def fetch_live_tournament_matches(tournament_path):
    """
    This function is ONLY for fetching LIVE data and is cached for 1 hour.
    """
    try:
        params = BASE_PARAMS.copy()
        params['conditions'] = f"[[parent::{tournament_path}]]"
        url = "https://api.liquipedia.net/api/v3/match"
        resp = requests.get(url, headers=HEADERS, params=params)
        resp.raise_for_status()
        return resp.json().get("result", [])
    except Exception as e:
        print(f"API Error fetching {tournament_path}: {e}")
        return []

# --- NEW MASTER DATA LOADER ---
def load_tournament_data(tournament_name):
    """
    Decides whether to load data from a local file (archived) or fetch from API (live).
    """
    tournament_info = ALL_TOURNAMENTS[tournament_name]
    is_live = tournament_info.get('live', False)
    
    if not is_live:
        # --- STRATEGY 1: Load from local file ---
        # Create a filename-safe version of the tournament name
        filename = f"{tournament_name.replace(' ', '_').replace('/', '_')}.json"
        filepath = os.path.join("data", filename) # Assumes a 'data' folder
        
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                data = json.load(f)
                st.toast(f"Loaded {len(data)} matches for {tournament_name} from file.", icon="📄")
                return data
        except FileNotFoundError:
            st.warning(f"Archived data file not found for {tournament_name}. Expected at: {filepath}")
            # Optional: You could fetch and save it here the first time.
            return []
        except Exception as e:
            st.error(f"Error reading local file for {tournament_name}: {e}")
            return []
            
    else:
        # --- STRATEGY 2: Fetch live data with Streamlit cache ---
        path = tournament_info['path']
        data = fetch_live_tournament_matches(path)
        if data:
            st.toast(f"Fetched {len(data)} live matches for {tournament_name} from API.", icon="📡")
        return data
