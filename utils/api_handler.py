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

# --- UNIFIED, CACHED API FETCHER ---
@st.cache_data(ttl=3600) # Cache live data for 1 hour
def fetch_from_api(tournament_path):
    """
    This is now the ONLY function that talks to the Liquipedia API.
    It's cached to protect against repeated calls for live data.
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
        # Return the error message to be displayed in the UI
        return {'error': str(e)}

# --- NEW MASTER DATA LOADER with Fetch-and-Save Logic ---
def load_tournament_data(tournament_name):
    """
    Decides whether to load data from a local file (archived) or fetch from API (live).
    If an archived file is not found, it fetches and saves it.
    """
    tournament_info = ALL_TOURNAMENTS[tournament_name]
    is_live = tournament_info.get('live', False)
    path = tournament_info['path']
    
    # Create a filename-safe version of the tournament name
    filename = f"{tournament_name.replace(' ', '_').replace('/', '_')}.json"
    data_dir = "data"
    filepath = os.path.join(data_dir, filename)

    # Ensure the 'data' directory exists
    os.makedirs(data_dir, exist_ok=True)

    if not is_live:
        # --- STRATEGY 1: Try to load from local file first ---
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                data = json.load(f)
                st.toast(f"Loaded {len(data)} matches for {tournament_name} from file.", icon="📄")
                return data
        except FileNotFoundError:
            # --- File not found, so we fetch AND save it ---
            st.toast(f"Local file for {tournament_name} not found. Fetching from API...", icon="☁️")
            data = fetch_from_api(path)
            
            if isinstance(data, dict) and 'error' in data:
                st.error(f"Failed to fetch {tournament_name}: {data['error']}")
                return []
            
            # Save the fetched data to a file for next time
            try:
                with open(filepath, 'w', encoding='utf-8') as f:
                    json.dump(data, f, indent=4)
                st.toast(f"Saved API data for {tournament_name} locally.", icon="💾")
            except Exception as e:
                st.warning(f"Could not save data for {tournament_name}: {e}")
            return data
        except Exception as e:
            st.error(f"Error reading local file for {tournament_name}: {e}")
            return []
            
    else:
        # --- STRATEGY 2: Fetch live data using the cached function ---
        data = fetch_from_api(path)
        if isinstance(data, dict) and 'error' in data:
            st.error(f"Failed to fetch live data for {tournament_name}: {data['error']}")
            return []

        st.toast(f"Fetched {len(data)} live matches for {tournament_name} from API.", icon="📡")
        return data
