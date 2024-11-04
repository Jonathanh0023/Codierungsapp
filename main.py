import streamlit as st
from bonsai_app import bonsai_page
from fuzzy_app import fuzzy_page
import json
import os
import uuid
import atexit
import time

# Set page configuration here
st.set_page_config(page_title="BonsAI Codierung", page_icon="", layout="centered")

# Function to get or create session ID using streamlit's persistent state
def get_or_create_session_id():
    if 'persistent_session_id' not in st.session_state:
        # Check if there's an existing session file for this user
        existing_session = None
        for filename in os.listdir():
            if filename.startswith('saved_state_') and filename.endswith('.json'):
                try:
                    with open(filename, 'r') as f:
                        data = json.load(f)
                        # Check if the session is still valid (less than 24 hours old)
                        if time.time() - data.get('session_start_time', 0) < 24 * 3600:
                            existing_session = filename.replace('saved_state_', '').replace('.json', '')
                            break
                except:
                    continue
        
        if existing_session:
            st.session_state.persistent_session_id = existing_session
        else:
            st.session_state.persistent_session_id = str(uuid.uuid4())
            st.session_state.session_start_time = time.time()
    
    return st.session_state.persistent_session_id

# Get the session ID
session_id = get_or_create_session_id()

# Get the path for the session-specific state file
def get_state_file_path():
    return f'saved_state_{session_id}.json'

# Function to clean up old session files
def cleanup_old_sessions(max_age_hours=24):
    try:
        current_time = time.time()
        for filename in os.listdir():
            if filename.startswith('saved_state_') and filename.endswith('.json'):
                file_path = os.path.join(os.getcwd(), filename)
                try:
                    with open(file_path, 'r') as f:
                        data = json.load(f)
                        file_age = current_time - data.get('session_start_time', 0)
                        # Delete files older than max_age_hours
                        if file_age > (max_age_hours * 3600):
                            os.remove(file_path)
                except Exception as e:
                    # If we can't read the file or it's invalid, delete it
                    try:
                        os.remove(file_path)
                    except:
                        pass
    except Exception as e:
        print(f"Error during cleanup: {e}")

# Clean up old session files at startup
cleanup_old_sessions()

# Function to load saved state
def load_saved_state():
    try:
        state_file = get_state_file_path()
        if os.path.exists(state_file):
            with open(state_file, 'r', encoding='utf-8') as f:
                return json.load(f)
    except Exception as e:
        print(f"Error loading saved state: {e}")
    return {}

# Function to save state
def save_state():
    state_dict = {
        'selected_app': st.session_state.get('selected_app'),
        'codes_input': st.session_state.get('codes_input', ''),
        'categories_input': st.session_state.get('categories_input', ''),
        'search_words_input': st.session_state.get('search_words_input', ''),
        'study_context_input': st.session_state.get('study_context_input', ''),
        'beispiele_input': st.session_state.get('beispiele_input', ''),
        'selected_task_template': st.session_state.get('selected_task_template'),
        'instructions_read': st.session_state.get('instructions_read', False),
        'api_key': st.session_state.get('api_key', ''),
        'system_message': st.session_state.get('system_message', ''),
        'question_template': st.session_state.get('question_template', ''),
        'codeplan_expander_open': st.session_state.get('codeplan_expander_open', False),
        'session_start_time': st.session_state.get('session_start_time', time.time())
    }
    
    try:
        with open(get_state_file_path(), 'w', encoding='utf-8') as f:
            json.dump(state_dict, f, ensure_ascii=False, indent=2)
    except Exception as e:
        print(f"Error saving state: {e}")

# Load saved state
saved_state = load_saved_state()

# Initialize session state variables with saved values
if 'selected_app' not in st.session_state:
    st.session_state.selected_app = saved_state.get('selected_app')
if 'codes_input' not in st.session_state:
    st.session_state.codes_input = saved_state.get('codes_input', '')
if 'categories_input' not in st.session_state:
    st.session_state.categories_input = saved_state.get('categories_input', '')
if 'search_words_input' not in st.session_state:
    st.session_state.search_words_input = saved_state.get('search_words_input', '')
if 'study_context_input' not in st.session_state:
    st.session_state.study_context_input = saved_state.get('study_context_input', '')
if 'beispiele_input' not in st.session_state:
    st.session_state.beispiele_input = saved_state.get('beispiele_input', '')
if 'selected_task_template' not in st.session_state:
    st.session_state.selected_task_template = saved_state.get('selected_task_template')
if 'instructions_read' not in st.session_state:
    st.session_state.instructions_read = saved_state.get('instructions_read', False)
if 'api_key' not in st.session_state:
    st.session_state.api_key = saved_state.get('api_key', '')
if 'system_message' not in st.session_state:
    st.session_state.system_message = saved_state.get('system_message', '')
if 'question_template' not in st.session_state:
    st.session_state.question_template = saved_state.get('question_template', '')
if 'codeplan_expander_open' not in st.session_state:
    st.session_state.codeplan_expander_open = saved_state.get('codeplan_expander_open', False)

# Save state whenever it changes
save_state()

# Function to reset app state
def reset_app_state():
    st.session_state.selected_app = None
    st.session_state.codes_input = ''
    st.session_state.categories_input = ''
    st.session_state.search_words_input = ''
    st.session_state.study_context_input = ''
    st.session_state.beispiele_input = ''
    st.session_state.selected_task_template = None
    st.session_state.question_template = ''
    # Don't reset instructions_read and api_key

# Function to display the landing page
def landing_page():
    # Custom CSS for modern styling
    st.markdown("""
        <style>
        /* Import Ucity font */
        @import url('https://fonts.cdnfonts.com/css/ucity');
        
        /* Apply Ucity font to all elements */
        * {
            font-family: 'Ucity', sans-serif !important;
        }
        
        /* Set light background for the entire page */
        .stApp {
            background: #fffffff;
        }
        
        .app-card {
            background-color: #ffffff;
            padding: 20px;
            border-radius: 10px;
            box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
            margin: 10px;
            transition: all 0.3s ease;
            height: 380px;
            display: flex;
            flex-direction: column;
            border: 1px solid #e0e0e0;
        }
        .app-card:hover {
            transform: translateY(-5px);
            box-shadow: 0 8px 15px rgba(0, 0, 0, 0.1);
            border-color: #e5007f;
        }
        .app-title {
            font-size: 24px;
            font-weight: bold;
            margin-bottom: 20px;
            color: #e5007f;  /* Changed to pink */
        }
        .app-description {
            color: #2c3e50;
            font-size: 16px;
            margin-bottom: 20px;
            flex-grow: 1;
        }
        .app-description ul {
            color: #34495e;
        }
        .button-container {
            margin-top: auto;
            text-align: center;
        }
        .centered-title {
            text-align: center;
            font-size: 48px;
            font-weight: bold;
            margin-bottom: 30px;
            background: linear-gradient(45deg, #e5007f, #ff4081);  /* Pink gradient */
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            padding: 20px;
        }
        /* Style for the subtitle */
        .subtitle {
            color: #34495e !important;
            font-size: 20px !important;
            margin-bottom: 40px !important;
        }
        /* Footer styling */
        .footer {
            text-align: center;
            margin-top: 50px;
            color: #e5007f;  /* Changed to pink */
            font-size: 16px;
        }
        </style>
        """, unsafe_allow_html=True)

    # Title with gradient
    st.markdown('<h1 class="centered-title">BonsAI Codierung</h1>', unsafe_allow_html=True)

    # Subtitle
    st.markdown("""
        <div class='subtitle' style='text-align: center;'>
            Wähle eine der folgenden Anwendungen:
        </div>
    """, unsafe_allow_html=True)

    # Create two columns for the app cards
    col1, col2 = st.columns(2)

    with col1:
        container = st.container()
        with container:
            st.markdown("""
                <div class='app-card'>
                    <div class='app-title'>🤖 BonsAI Codierungstool</div>
                    <div class='app-description'>
                        KI-gestützte Codierung von offenen Nennungen mit folgenden Features:
                        <ul>
                            <li>Automatische Kategorisierung</li>
                            <li>Single- und Multi-Label Codierung</li>
                            <li>Excel Import/Export</li>
                            <li>Interaktive Benutzeroberfläche</li>
                        </ul>
                    </div>
                </div>
                """, unsafe_allow_html=True)
            if st.button("Starten", key="bonsai_button", use_container_width=True):
                st.session_state.selected_app = "BonsAI Codierungstool"
                st.rerun()

    with col2:
        container = st.container()
        with container:
            st.markdown("""
                <div class='app-card'>
                    <div class='app-title'>🔍 FuzzyWuzzy Markencodierung</div>
                    <div class='app-description'>
                        Fuzzy-String-Matching für Markencodierung mit:
                        <ul>
                            <li>Ähnlichkeitsbasierte Zuordnung</li>
                            <li>Automatische Markenerkennung</li>
                            <li>Batch-Verarbeitung</li>
                            <li>Exportfunktion</li>
                        </ul>
                    </div>
                </div>
                """, unsafe_allow_html=True)
            if st.button("Starten", key="fuzzy_button", use_container_width=True):
                st.session_state.selected_app = "FuzzyWuzzy Markencodierung"
                st.rerun()

    # Footer
    st.markdown("""
        <div class='footer'>
            <p>Entwickelt von BonsAI ❤️</p>
        </div>
    """, unsafe_allow_html=True)

# Display the landing page or the selected app
if st.session_state.selected_app is None:
    landing_page()
elif st.session_state.selected_app == "BonsAI Codierungstool":
    bonsai_page()
elif st.session_state.selected_app == "FuzzyWuzzy Markencodierung":
    fuzzy_page()


