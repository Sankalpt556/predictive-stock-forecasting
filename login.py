import streamlit as st
import pandas as pd
import os
import traceback # Added for more detailed error logging if needed

class LoginSystem:
    def __init__(self, user_file='users.csv'):
        self.user_file = user_file
        # Initialize session state keys if they don't exist
        if 'logged_in' not in st.session_state:
            st.session_state.logged_in = False
        if 'username' not in st.session_state:
             st.session_state.username = None

    def set_background(self):
        # Changed background-color from black to #282c34
        pass


    def check_user_exists(self, username):
        if not os.path.exists(self.user_file):
            return False
        try:
            # Check if file is empty first to avoid EmptyDataError on read
            if os.path.getsize(self.user_file) == 0:
                return False
            df = pd.read_csv(self.user_file)
            return username in df['username'].values
        except pd.errors.EmptyDataError: # Should be caught by size check, but kept for safety
             return False
        except Exception as e: # Catch other potential read errors
            st.error(f"Error reading user file: {e}")

            return False


    def save_user(self, username, password):
        # Basic validation
        if not username or not password:
            st.error("Username and password cannot be empty.")
            return False # Indicate failure

        new_user = pd.DataFrame([[username, password]], columns=['username', 'password'])
        try:
            file_exists = os.path.exists(self.user_file)
            # Determine if header should be written (only if file doesn't exist or is empty)
            write_header = not file_exists or os.path.getsize(self.user_file) == 0
            new_user.to_csv(self.user_file, mode='a', index=False, header=write_header)
            return True # Indicate success
        except Exception as e:
            st.error(f"Error saving user data: {e}")

            return False # Indicate failure

    def validate_login(self, username, password):
         # Basic validation
        if not username or not password:

            return False

        if not os.path.exists(self.user_file):
            return False
        try:
             # Check if file is empty first
            if os.path.getsize(self.user_file) == 0:
                return False
            df = pd.read_csv(self.user_file)
            # Ensure comparison handles potential type issues robustly
            user_record = df[(df['username'].astype(str) == str(username)) & (df['password'].astype(str) == str(password))]
            return not user_record.empty
        except pd.errors.EmptyDataError:
             return False # File is empty, no users
        except Exception as e:
            st.error(f"Error reading user file during login: {e}")

            return False

    def show_logout_button(self):
        """Displays a logout button if the user is logged in."""
        if st.session_state.get('logged_in', False):

             if st.button("Logout", key="logout_button"):
                  st.session_state.logged_in = False
                  st.session_state.username = None
                  # Clear other session state variables if needed
                  st.rerun() # Rerun the script to reflect the change


    def login_ui(self):
        """Displays the Login/Signup UI components. Returns True if login is successful this cycle."""
        login_successful_this_run = False # Flag to indicate login success on this specific run

        # Apply background only when showing the UI
        self.set_background()

        # If already logged in, optionally show welcome message and logout
        if st.session_state.get('logged_in', False):
             st.success(f"Welcome back, {st.session_state.get('username', 'N/A')}!")
             self.show_logout_button() # Display logout option
             return False # Not a new login event

        # --- Login/Signup Form ---
        st.title("Login / Signup")
        tab = st.radio("Choose Action", ["Login", "Signup"], key="login_signup_tab", horizontal=True) # Horizontal layout
        username = st.text_input("Username", key="username_input")
        password = st.text_input("Password", type="password", key="password_input")

        col1, col2 = st.columns([1, 5]) # Create columns for button alignment

        if tab == "Signup":
            with col1: # Place button in the first (smaller) column
                 if st.button("Create Account", key="signup_button"):
                    if not username or not password:
                        st.error("Username and password cannot be empty.")
                    elif self.check_user_exists(username):
                        st.error("Username already exists!")
                    else:
                        if self.save_user(username, password):
                            st.success("Account created successfully! Please go to the Login tab.")
                        # else: Error message is shown by save_user
        elif tab == "Login":
             with col1: # Place button in the first (smaller) column
                if st.button("Login", key="login_button"):
                    if not username or not password:
                         st.error("Please enter both username and password.")
                    elif self.validate_login(username, password):
                        st.success("Logged in successfully!") # Show success briefly
                        st.session_state.logged_in = True
                        st.session_state.username = username
                        login_successful_this_run = True # Set flag for external check
                        # Removed st.rerun() here - let the main app decide when to rerun
                    else:
                        st.error("Invalid username or password!")

        return login_successful_this_run # Return the flag


