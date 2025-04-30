
class StockForecastingApp:
    def __init__(self):
        """Initialize the app configuration and state."""
        # --- Configuration ---
        self.API_KEY = "##########################" # <<< Replace with your key if needed
        self.BASE_URL = "https://api.marketstack.com/v1/eod"
        self.company_dict = {
            "Apple Inc.": "AAPL", "Microsoft Corporation": "MSFT", "Amazon.com Inc.": "AMZN",
            "Alphabet Inc. (Google)": "GOOGL", "Meta Platforms Inc.": "META", "Tesla Inc.": "TSLA",
            "NVIDIA Corporation": "NVDA", "Netflix Inc.": "NFLX", "Adobe Inc.": "ADBE",
            "Intel Corporation": "INTC", "Advanced Micro Devices": "AMD", "Broadcom Inc.": "AVGO",
            "Qualcomm Inc.": "QCOM", "Cisco Systems Inc.": "CSCO", "Oracle Corporation": "ORCL",
            "Salesforce Inc.": "CRM", "PayPal Holdings Inc.": "PYPL", "Shopify Inc.": "SHOP",
            "Zoom Video Communications": "ZM", "Uber Technologies Inc.": "UBER",
            "Spotify Technology S.A.": "SPOT", "Walt Disney Company": "DIS", "Coca-Cola Company": "KO",
            "PepsiCo Inc.": "PEP", "Walmart Inc.": "WMT", "Procter & Gamble Co.": "PG",
            "Johnson & Johnson": "JNJ", "McDonald's Corporation": "MCD",
            "Berkshire Hathaway Inc.": "BRK.B", "Visa Inc.": "V"
        }
        self.data_limit = 1000
        self.min_data_points = 60
        self.test_size_percentage = 0.2
        self.window_sma = 5
        self.n_lags_ml = 5
        self.rf_model_params = {'n_estimators': 100, 'random_state': 42, 'n_jobs': -1,
                                'max_depth': 10, 'min_samples_split': 10}
        # --- State / Data ---
        self.raw_data_df = None
        self.symbol = None
        self.company_name = None
        self.target_series = None

    # --- Data Fetching and Display ---
    def fetch_data(self):
        """Fetches, cleans, and stores stock data."""
        if not self.company_name:
            st.warning("Company name not set.")
            return False

        self.symbol = self.company_dict[self.company_name]
        st.info(f"Attempting to fetch last {self.data_limit} data points for {self.symbol}...")
        params = {'access_key': self.API_KEY, 'symbols': self.symbol, 'limit': self.data_limit}

        try:
            response = requests.get(self.BASE_URL, params=params, timeout=20)
            response.raise_for_status()
            data = response.json()

            if 'data' in data and data['data']:
                df = pd.DataFrame(data['data'])
                df['date'] = pd.to_datetime(df['date'])
                df.set_index('date', inplace=True)
                df = df[['open', 'high', 'low', 'close', 'volume']]
                df.sort_index(inplace=True)
                df = df[~df.index.duplicated(keep='first')]
                for col in ['open', 'high', 'low', 'close', 'volume']:
                        df[col] = pd.to_numeric(df[col], errors='coerce')
                df.dropna(subset=['open', 'high', 'low', 'close'], inplace=True)

                if len(df) < self.min_data_points:
                    st.warning(f"Fetched {len(df)} valid data points, less than minimum required ({self.min_data_points}). Forecasting disabled.")
                    self.raw_data_df = df
                    return False # Indicate insufficient data for modeling

                self.raw_data_df = df
                st.success(f"Data fetched successfully! Found {len(df)} valid data points.")
                return True # Indicate data is sufficient
            elif 'data' in data and not data['data']:
                 st.warning(f"No data returned by API for {self.symbol}.")
                 self.raw_data_df = None
                 return False
            else:
                api_error_message = data.get('error', {}).get('message', "Unknown API error")
                st.error(f"API Error: {api_error_message}")
                self.raw_data_df = None
                return False
        except requests.exceptions.HTTPError as http_err:
            st.error(f"HTTP error occurred: {http_err}")
            st.error(f"Response content: {response.text}")
            self.raw_data_df = None
            return False
        except requests.exceptions.RequestException as req_err:
            st.error(f"Network error or API request failed: {req_err}")
            self.raw_data_df = None
            return False
        except Exception as e:
            st.error(f"An unexpected error occurred during data fetching:")
            st.error(traceback.format_exc())
            self.raw_data_df = None
            return False

    def display_data_info(self):
        """Displays latest data points if available."""
        if self.raw_data_df is not None and not self.raw_data_df.empty:
            st.subheader("Latest 15 Days of Stock Data")
            st.dataframe(self.raw_data_df.tail(15), use_container_width=True)

    # --- Model Implementations ---
    def _run_sma(self, train_data, test_data):
        """Runs SMA model, returns predictions and MAPE."""
        # st.write("Running Simple Moving Average (SMA)...") # Removed from frontend
        try:
            sma_preds = []
            history = train_data.values.tolist()
            for t in range(len(test_data)):
                if len(history) >= self.window_sma:
                    pred = np.mean(history[-self.window_sma:])
                elif history: pred = np.mean(history)
                else: pred = 0 # Handle case with no history
                sma_preds.append(pred)
                # Append the actual test value for the next iteration's history
                history.append(test_data.iloc[t])

            predictions = np.array(sma_preds)

            # Handle potential zero values in test_data before calculating MAPE
            actuals = test_data.values
            non_zero_mask = actuals != 0
            if np.all(~non_zero_mask): # All actuals are zero
                 mape = np.inf # Or handle as appropriate (e.g., return 0 if predictions are also 0)
            else:
                 # Calculate MAPE only on non-zero actuals
                 mape = mean_absolute_percentage_error(actuals[non_zero_mask], predictions[non_zero_mask])

            # st.write("SMA Done.") # Removed from frontend
            return predictions, mape
        except Exception as e:
            st.warning(f"SMA failed: {e}")
            return None, np.inf

    def _run_rf(self, X_train, y_train, X_test, y_test):
        """Runs Random Forest model, returns predictions and MAPE."""
        # st.write("Running Random Forest...") # Removed from frontend
        try:
            if not all(isinstance(df, pd.DataFrame) and not df.empty for df in [X_train, X_test]) or \
               not all(isinstance(s, pd.Series) and not s.empty for s in [y_train, y_test]):
                st.warning("RF received invalid/empty data splits. Skipping RF.")
                return None, np.inf

            rf_model = RandomForestRegressor(**self.rf_model_params)
            rf_model.fit(X_train, y_train)
            predictions = rf_model.predict(X_test)

            # Handle potential zero values in y_test before calculating MAPE
            actuals = y_test.values
            non_zero_mask = actuals != 0
            if np.all(~non_zero_mask): # All actuals are zero
                 mape = np.inf
            else:
                 # Calculate MAPE only on non-zero actuals
                 mape = mean_absolute_percentage_error(actuals[non_zero_mask], predictions[non_zero_mask])

            # st.write("Random Forest Done.") # Removed from frontend
            return predictions, mape
        except Exception as e:
            st.warning(f"Random Forest failed: {e}")
            st.warning(traceback.format_exc())
            return None, np.inf

    def _run_linear_regression(self, X_train, y_train, X_test, y_test):
        """Runs Linear Regression model, returns predictions and MAPE."""
        # st.write("Running Linear Regression (Least Squares)...") # Removed from frontend
        try:
            if not all(isinstance(df, pd.DataFrame) and not df.empty for df in [X_train, X_test]) or \
               not all(isinstance(s, pd.Series) and not s.empty for s in [y_train, y_test]):
                st.warning("Linear Regression received invalid/empty data splits. Skipping.")
                return None, np.inf

            lr_model = LinearRegression()
            lr_model.fit(X_train, y_train)
            predictions = lr_model.predict(X_test)

            # Handle potential zero values in y_test before calculating MAPE
            actuals = y_test.values
            non_zero_mask = actuals != 0
            if np.all(~non_zero_mask): # All actuals are zero
                 mape = np.inf
            else:
                 # Calculate MAPE only on non-zero actuals
                 mape = mean_absolute_percentage_error(actuals[non_zero_mask], predictions[non_zero_mask])

            # st.write("Linear Regression Done.") # Removed from frontend
            return predictions, mape
        except Exception as e:
            st.warning(f"Linear Regression failed: {e}")
            st.warning(traceback.format_exc())
            return None, np.inf

    # --- Evaluation and Prediction ---
    def evaluate_models_and_plot(self, model_mape, model_predictions, test_data, y_test_ml=None):
        """Compares models based on MAPE, plots the best. y_test_ml is the target for ML models (RF/LR)."""
        st.subheader("Model Comparison (Lower MAPE is better)")
        valid_mape = {k: v for k, v in model_mape.items() if np.isfinite(v)}

        if not valid_mape:
            st.error("All models failed evaluation.")
            return None

        # Display MAPE results (formatted as percentage)
        mape_df = pd.DataFrame.from_dict(model_mape, orient='index', columns=['MAPE'])
        st.dataframe(mape_df.sort_values(by='MAPE').style.format({"MAPE": "{:.4%}"}))

        # Find best model based on lowest MAPE
        best_model_name = min(valid_mape, key=valid_mape.get)
        st.success(f"Best Performing Model on Test Set: **{best_model_name}** (MAPE: {model_mape[best_model_name]:.4%})")

        # Plotting
        st.subheader(f"Actual vs. Predicted Avg. 'Price' ({best_model_name} on Test Set)")
        predicted_plot_data = model_predictions.get(best_model_name)
        # Use the correct actual data for plotting based on the model type
        actual_plot_data = y_test_ml if best_model_name in ['Random Forest', 'Linear Regression'] else test_data

        if predicted_plot_data is None or actual_plot_data is None or actual_plot_data.empty:
             st.warning(f"Data invalid or missing for plotting {best_model_name}. Cannot plot.")
             return best_model_name # Return best model name even if plotting fails

        # Ensure lengths match before plotting (can happen if prediction failed partially)
        if len(actual_plot_data) != len(predicted_plot_data):
             st.warning(f"Length mismatch between actual ({len(actual_plot_data)}) and predicted ({len(predicted_plot_data)}) data for {best_model_name}. Plotting might be inaccurate or fail.")
             # Attempt to plot common indices if possible, otherwise skip
             common_index = actual_plot_data.index.intersection(pd.Series(predicted_plot_data, index=actual_plot_data.index).index) # Assumes prediction aligns with actual index
             if len(common_index) > 0:
                 plot_df = pd.DataFrame({'Actual': actual_plot_data.loc[common_index].values,
                                         'Predicted': pd.Series(predicted_plot_data, index=actual_plot_data.index).loc[common_index].values},
                                         index=common_index)
                 st.line_chart(plot_df)
             else:
                  st.warning("Cannot plot due to index mismatch.")

        else:
             plot_df = pd.DataFrame({'Actual': actual_plot_data.values, 'Predicted': predicted_plot_data}, index=actual_plot_data.index)
             st.line_chart(plot_df)

        return best_model_name

    def predict_next_day(self, best_model_name, ml_features_full=None, ml_target_full=None):
        """Retrains best model on full data and predicts next day."""
        st.subheader("Next Day Prediction")
        if best_model_name is None:
             st.warning("Cannot predict next day without a best model.")
             return None, None
        if self.raw_data_df is None or self.raw_data_df.empty:
             st.warning("Cannot predict next day without valid historical data.")
             return None, None
        if self.target_series is None or self.target_series.empty:
             st.warning("Cannot predict next day without a target series.")
             return None, None


        # st.write(f"Retraining {best_model_name} on full dataset...") # Removed from frontend
        last_date = self.raw_data_df.index.max()

        # Calculate next business day (simple weekend skip)
        next_day_candidate = last_date + Timedelta(days=1)
        if next_day_candidate.dayofweek == 5: next_pred_date = next_day_candidate + Timedelta(days=2) # Saturday -> Monday
        elif next_day_candidate.dayofweek == 6: next_pred_date = next_day_candidate + Timedelta(days=1) # Sunday -> Monday
        else: next_pred_date = next_day_candidate

        next_day_pred = None
        try:
            if best_model_name == 'SMA':
                if len(self.target_series) >= self.window_sma:
                    next_day_pred = self.target_series.iloc[-self.window_sma:].mean()
                    # st.write("SMA calculated for next day.") # Removed
                else: st.warning("Not enough data in the full target series for SMA window.")
            elif best_model_name == 'Random Forest':
                if ml_features_full is not None and ml_target_full is not None and not ml_features_full.empty:
                    final_model = RandomForestRegressor(**self.rf_model_params)
                    final_model.fit(ml_features_full, ml_target_full)
                    # Prepare features for the next day (using the last available features)
                    last_features = ml_features_full.iloc[-1:].values # Use the last row of features
                    next_day_pred = final_model.predict(last_features)[0]
                    # st.write("Random Forest retrained for next day.") # Removed
                else: st.warning("Full RF features/target not available for retraining.")
            elif best_model_name == 'Linear Regression':
                if ml_features_full is not None and ml_target_full is not None and not ml_features_full.empty:
                    final_model = LinearRegression()
                    final_model.fit(ml_features_full, ml_target_full)
                     # Prepare features for the next day (using the last available features)
                    last_features = ml_features_full.iloc[-1:].values # Use the last row of features
                    next_day_pred = final_model.predict(last_features)[0]
                    # st.write("Linear Regression retrained for next day.") # Removed
                else: st.warning("Full LR features/target not available for retraining.")

        except Exception as e:
            st.error(f"Error during final prediction step ({best_model_name}): {e}")
            st.error(traceback.format_exc())

        # Display Prediction Result
        if next_day_pred is not None:
            st.metric(label=f"Predicted Avg. Price for {next_pred_date.strftime('%Y-%m-%d')} ({best_model_name})",
                      value=f"{next_day_pred:.2f}")
        else:
            st.warning("Could not generate next day prediction value.")

        return next_day_pred, next_pred_date

    # --- Main Workflow Orchestration ---
    def run_modeling_workflow(self):
        """Orchestrates model training, evaluation, and next day prediction."""
        try:
            progress_bar = st.progress(0)
            if self.raw_data_df is None or self.raw_data_df.empty:
                st.error("Cannot run modeling workflow without data.")
                progress_bar.progress(100) # Complete bar on error exit
                return
            if len(self.raw_data_df) < self.min_data_points:
                 st.error(f"Insufficient data ({len(self.raw_data_df)} points) to run modeling. Minimum required: {self.min_data_points}.")
                 progress_bar.progress(100)
                 return

            df_model = self.raw_data_df.copy()
            df_model['Price'] = (df_model['open'] + df_model['high'] + df_model['low'] + df_model['close']) / 4
            self.target_series = df_model['Price']

            # --- Data Splitting ---
            split_index = int(len(self.target_series) * (1 - self.test_size_percentage))
            # Ensure split_index is valid
            if split_index <= 0: split_index = 1 # Need at least one training point
            if split_index >= len(self.target_series): split_index = len(self.target_series) - 1 # Need at least one test point

            train_data = self.target_series.iloc[:split_index]
            test_data = self.target_series.iloc[split_index:]

            if train_data.empty or test_data.empty:
                st.error(f"Train/Test split failed (Train: {len(train_data)}, Test: {len(test_data)}). Need more data or adjust test size.")
                progress_bar.progress(100)
                return

            # st.write(f"SMA using Train data: {len(train_data)} points") # Removed from frontend
            # st.write(f"SMA using Test data: {len(test_data)} points") # Removed from frontend
            progress_bar.progress(10)

            # --- Feature Preparation for ML Models ---
            # st.write("Preparing features for ML models...") # Removed from frontend
            X_full_ml, y_full_ml, X_train_ml, y_train_ml, X_test_ml, y_test_ml = [None] * 6
            ml_features_created = False
            try:
                ml_df = pd.DataFrame({'Price': self.target_series})
                features_list = []
                # Create lagged features
                for i in range(1, self.n_lags_ml + 1):
                    lag_col_name = f'Lag_{i}'
                    ml_df[lag_col_name] = ml_df['Price'].shift(i)
                    features_list.append(lag_col_name)

                # Create target variable (next day's price)
                ml_df['Target'] = ml_df['Price'].shift(-1)
                ml_df.dropna(inplace=True) # Drop rows with NaNs (due to lags/target shift)

                if ml_df.empty or len(ml_df) < self.min_data_points // 2 : # Check if enough data remains
                    st.warning("Not enough data for ML features after lagging/dropping NaNs. Skipping ML models.")
                else:
                    X_full_ml = ml_df[features_list]
                    y_full_ml = ml_df['Target']

                    # Split ML data based on the original test set start date index
                    original_test_start_date = test_data.index.min()
                    # Find the location in the ML features index corresponding to the test start date
                    split_loc_ml = X_full_ml.index.searchsorted(original_test_start_date)

                    # Ensure split_loc_ml is valid
                    if split_loc_ml >= len(X_full_ml): split_loc_ml = len(X_full_ml) # Split at the end if date not found (test set empty)
                    if split_loc_ml <= 0 : split_loc_ml = 1 # Ensure train set is not empty

                    X_train_ml = X_full_ml.iloc[:split_loc_ml]
                    X_test_ml = X_full_ml.iloc[split_loc_ml:]
                    y_train_ml = y_full_ml.iloc[:split_loc_ml]
                    y_test_ml = y_full_ml.iloc[split_loc_ml:]

                    # Check if splits resulted in empty dataframes/series
                    if X_train_ml.empty or y_train_ml.empty or X_test_ml.empty or y_test_ml.empty:
                        st.warning("ML data splits resulted in empty sets after aligning with test date. Skipping ML models.")
                    else:
                        # st.write(f"ML models using Train data: {len(y_train_ml)}, Test data: {len(y_test_ml)} samples.") # Removed
                        ml_features_created = True
            except Exception as feat_err:
                st.error(f"Error during feature preparation: {feat_err}")
                st.error(traceback.format_exc())
                # Continue without ML features if prep fails

            progress_bar.progress(25)

            # --- Run Models ---
            model_predictions = {}
            model_mape = {} # Changed from model_mse

            # Run SMA
            sma_preds, model_mape['SMA'] = self._run_sma(train_data, test_data)
            if sma_preds is not None: model_predictions['SMA'] = sma_preds
            progress_bar.progress(50)

            # Run ML Models (if features were created)
            if ml_features_created:
                rf_preds, model_mape['Random Forest'] = self._run_rf(X_train_ml, y_train_ml, X_test_ml, y_test_ml)
                if rf_preds is not None: model_predictions['Random Forest'] = rf_preds
                progress_bar.progress(65)

                lr_preds, model_mape['Linear Regression'] = self._run_linear_regression(X_train_ml, y_train_ml, X_test_ml, y_test_ml)
                if lr_preds is not None: model_predictions['Linear Regression'] = lr_preds
                progress_bar.progress(80)
            else:
                st.warning("Skipping ML models due to feature preparation issues or insufficient data.")
                model_mape['Random Forest'] = np.inf
                model_mape['Linear Regression'] = np.inf
                progress_bar.progress(80) # Skip ML progress steps

            # --- Evaluate and Predict ---
            # Pass model_mape instead of model_mse
            best_model_name = self.evaluate_models_and_plot(model_mape, model_predictions, test_data, y_test_ml)
            progress_bar.progress(90)

            if best_model_name:
                self.predict_next_day(best_model_name, X_full_ml, y_full_ml)
            else:
                st.error("Cannot predict next day because no model performed successfully.")
            progress_bar.progress(100)

        except Exception as e:
             st.error("An critical error occurred during the modeling workflow:")
             st.error(traceback.format_exc())
             # Ensure progress bar completes even on unexpected error
             if 'progress_bar' in locals():
                 progress_bar.progress(100)


    # --- UI Build and Execution ---
    def build_ui(self):
        """Builds the main Streamlit user interface."""
        st.title("Stock Forecasting App")
        self.company_name = st.selectbox("Select a company:", list(self.company_dict.keys()), index=None, placeholder="Select company...") # Added placeholder

        if self.company_name:
            # Fetch data returns True if successful AND sufficient for modeling
            data_ok_for_modeling = self.fetch_data()
            self.display_data_info() # Display data regardless of sufficiency

            st.subheader("Forecasting Models")
            if data_ok_for_modeling:
                run_forecast_button = st.button("Run Forecasting Models & Predict Next Day")
                if run_forecast_button:
                    # Use context manager for spinner
                    with st.spinner("Running models and generating predictions... Please wait."):
                        self.run_modeling_workflow()
            elif self.raw_data_df is not None :
                # Warning about insufficient data already shown in fetch_data
                st.info("Insufficient data points available to run forecasting models.")
                pass # Don't show the button if data isn't sufficient
            else:
                # Error/Warning about fetching failure already shown in fetch_data
                 st.info("Data could not be fetched. Cannot run forecasting.")
                 pass
        else:
             st.info("Select a company from the dropdown to fetch data and enable forecasting.")

# --- Main Execution ---
if __name__ == "__main__":
    # Set page config once
    st.set_page_config(page_title="Stock Forecasting App", page_icon="💹", layout="wide") # Changed icon slightly
    app = StockForecastingApp()
    app.build_ui()
