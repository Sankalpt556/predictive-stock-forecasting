import streamlit as st
import login # Assumes your LoginSystem code is in login_system.py
import model# Assumes your StockForecastingApp code is in stock_forecasting.py
import news # Assumes your NewsSentimentAnalyzerApp code is in news_sentiment_app.py

# --- Main App Configuration ---
st.set_page_config(page_title="Stock Analysis Platform", page_icon="📈", layout="wide")

# Initialize session state for logged_in and page if they don't exist
if 'logged_in' not in st.session_state:
    st.session_state.logged_in = False
if 'page' not in st.session_state:
     # Initial state before login
     st.session_state.page = 'Login'

# --- Instantiate the Login System ---
# Instantiate outside the conditional block so its session state initialization runs
login_app = login.LoginSystem()

# --- Apply Background (Using the method from LoginSystem for consistency) ---
# Apply background regardless of login state for consistent look across pages
login_app.set_background()

# --- Main Application Logic ---

if not st.session_state.get('logged_in', False):
    # --- User is NOT logged in: Show Login/Signup Page ---
    st.session_state.page = 'Login' # Ensure page state reflects the login screen

    # The login_ui method handles its own title, form, and sets st.session_state.logged_in upon success.
    # It also applies its background internally.
    login_success_this_run = login_app.login_ui()

    # If login was successful in this run, update page state and rerun to show main app
    if login_success_this_run:
         st.session_state.page = 'Forecasting' # Set initial logged-in page
         st.rerun() # Rerun to move to the forecasting page immediately

else:
    # --- User is logged in: Show Main Application Content ---

    # Ensure page state is initialized correctly upon first login or if it was 'Login'
    if st.session_state.page == 'Login':
        st.session_state.page = 'Forecasting'
        # No need to rerun here, as the login_ui block likely already triggered it

    st.success(f"Welcome, {st.session_state.get('username', 'User')}!")

    # --- Navigation within Logged-in Area (Sidebar) ---

    with st.sidebar:
        st.subheader("Navigation")
        # Radio buttons for page selection
        page_selection = st.radio(
            "Go to:",
            ('Stock Forecasting', 'News Sentiment'),
            key='page_selector_radio',
            # Set initial value based on current session state.page
            index=0 if st.session_state.page == 'Forecasting' else 1
        )

        # Update session state based on radio button selection and rerun if needed
        if page_selection == 'Stock Forecasting':
            if st.session_state.page != 'Forecasting': # Avoid unnecessary rerun
                 st.session_state.page = 'Forecasting'
                 st.rerun()
        elif page_selection == 'News Sentiment':
            if st.session_state.page != 'Sentiment': # Avoid unnecessary rerun
                st.session_state.page = 'Sentiment'
                st.rerun()

        st.markdown("---") # Separator in sidebar

        # Logout Button in the sidebar (available from any logged-in page)
        if st.button("Logout", key="sidebar_logout_button"):
            st.session_state.logged_in = False
            st.session_state.username = None
            st.session_state.page = 'Login' # Reset page state on logout
            # Consider clearing other app-specific session state variables here if needed
            st.rerun() # Rerun to go back to the login page

    # --- Display Content based on Page State ---

    if st.session_state.page == 'Forecasting':
        
        # Instantiate and build the Stock Forecasting UI
        stock_app = model.StockForecastingApp()
        stock_app.build_ui()


    elif st.session_state.page == 'Sentiment':
        
        # Instantiate and build the News Sentiment UI
        news_app = news.NewsSentimentAnalyzerApp()
        news_app.build_ui()