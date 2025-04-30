import streamlit as st
import requests
import pandas as pd
import datetime
import traceback

from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer

class NewsSentimentAnalyzerApp:
    def __init__(self):
        """Initializes the News Sentiment Analyzer App."""
        # --- Configuration ---
        self.API_ENDPOINT = "https://api.worldnewsapi.com/search-news"

        # --- API Key (Hardcoded - SECURITY RISK) ---
        # WARNING: Hardcoding keys is risky. Consider environment variables or secrets management.
        self.NEWS_API_KEY = "d9bde6ceee3941c99948f5983585bead" # Your provided key

        # Basic check if the key is empty during initialization
        if not self.NEWS_API_KEY:
            st.error("ERROR: The NEWS_API_KEY is empty in NewsSentimentAnalyzerApp.")


        # --- Initialize Sentiment Analyzer ---
        self.analyzer = SentimentIntensityAnalyzer()

        # List of topics/domains for the dropdown (can be instance variable)
        self.available_topics = [
            "Apple", "AAPL", "Apple stock",
            "Microsoft", "MSFT", "Microsoft stock",
            "Amazon", "AMZN", "Amazon stock",
            "Alphabet", "GOOGL", "Google stock",
            "Meta Platforms", "META", "Facebook stock",
            "Tesla", "TSLA", "Tesla stock",
            "NVIDIA", "NVDA", "Nvidia stock",
            "Netflix", "NFLX", "Netflix stock",
            "Adobe", "ADBE", "Adobe stock",
            "Intel", "INTC", "Intel stock",
            "AMD", "Advanced Micro Devices stock",
            "Broadcom", "AVGO", "Broadcom stock",
            "Qualcomm", "QCOM", "Qualcomm stock",
            "Cisco Systems", "CSCO", "Cisco stock",
            "Oracle", "ORCL", "Oracle stock",
            "Salesforce", "CRM", "Salesforce stock",
            "PayPal Holdings", "PYPL", "PayPal stock",
            "Shopify", "SHOP", "Shopify stock",
            "Zoom Video Communications", "ZM", "Zoom stock",
            "Uber Technologies", "UBER", "Uber stock",
            "Spotify Technology", "SPOT", "Spotify stock",
            "The Walt Disney Company", "DIS", "Disney stock",
            "Coca-Cola", "KO", "Coca-Cola stock",
            "PepsiCo", "PEP", "Pepsi stock",
            "Walmart", "WMT", "Walmart stock",
            "Procter & Gamble", "PG", "P&G stock",
            "Johnson & Johnson", "JNJ", "J&J stock",
            "McDonald's", "MCD", "McDonald's stock",
            "Berkshire Hathaway", "BRK.B", "BRK.A", "Berkshire stock",
            "Visa", "V", "Visa stock"
        ]


    # Removed hash_funcs and renamed 'self' parameter to '_self'
    @st.cache_data(ttl=600)
    def fetch_articles_from_worldnewsapi(_self, api_key, topic_text):
        """Fetches news articles from World News API based on the topic text."""
        # NOTE: Access instance attributes via _self instead of self
        if not topic_text:
            return None, "No topic selected."

        st.info(f"Fetching news about: {topic_text} using World News API...")

        params = {
            'api-key': api_key,
            'text': topic_text,
            'source-countries': 'us', # Optional: Filters for articles published by sources in the US.
            'language': 'en', # Optional: Request English articles
            'number': 50
        }

        try:
            # Access instance attributes via _self
            response = requests.get(_self.API_ENDPOINT, params=params, timeout=15)

            if response.status_code == 401:
                return None, f"API Error 401: Authentication failed. Check if the API Key is valid."
            elif response.status_code == 402:
                return None, f"API Error 402: Payment Required / Quota Exceeded. Check your plan limits."
            elif response.status_code == 429:
                return None, "API Error 429: Rate limit exceeded. Please wait and try again."

            response.raise_for_status()

            data = response.json()
            return data, None

        except requests.exceptions.Timeout:
            return None, "Network Error: The request timed out."
        except requests.exceptions.HTTPError as http_err:
            error_details = f"HTTP Error: {http_err}"
            try:
                error_json = http_err.response.json()
                error_details += f" - Response: {error_json.get('message', error_json)}"
            except:
                 error_details += f" - Response: {http_err.response.text}"
            return None, error_details
        except requests.exceptions.RequestException as req_err:
            return None, f"Request Error: {req_err}"
        except Exception as e:
            st.error(f"An unexpected error occurred during news fetching: {e}")
            st.error(traceback.format_exc())
            return None, f"An unexpected error occurred: {e}"

    # --- Method to get sentiment score ---
    def get_sentiment_score(self, text):
        """Calculates the VADER sentiment compound score for a given text."""
        if not text or not isinstance(text, str):
            return None
        vs = self.analyzer.polarity_scores(text)
        return vs['compound']

    # --- Streamlit App UI Method ---
    def build_ui(self):
        """Builds the Streamlit UI for the News Sentiment Analyzer."""
        st.title(" News Topic Sentiment Summary")
        # st.set_page_config is handled by main.py

        selected_topic = st.selectbox(
            "Choose a topic or company to search for news about:",
            options=self.available_topics,
            index=None,
            placeholder="Select topic..."
        )

        if st.button("Fetch Data & Analyze Sentiment", key="fetch_data_button_sentiment"): # Unique key
            if not selected_topic:
                st.warning("Please select a topic.")
            elif not self.NEWS_API_KEY:
                 st.error("News API Key is missing. Cannot fetch news.")
            else:
                with st.spinner(f"Fetching articles for {selected_topic} and analyzing sentiment..."):
                    # Call the fetching method - 'self' is passed implicitly as the first arg
                    # Streamlit will see the parameter name starts with '_' and skip hashing it
                    data, error = self.fetch_articles_from_worldnewsapi(self.NEWS_API_KEY, selected_topic)

                    if error:
                        st.error(f" Error: {error}")
                    elif data:
                        articles = data.get("news", [])
                        st.success(f"API Call Successful. Found {len(articles)} articles for topic: {selected_topic}.")

                        if articles:
                            display_data = []
                            for a in articles:
                                title = a.get("title", "N/A")
                                sentiment_score = self.get_sentiment_score(title) # Use instance method

                                sentiment_label = "Neutral"
                                if sentiment_score is not None:
                                    if sentiment_score >= 0.05:
                                        sentiment_label = "Positive"
                                    elif sentiment_score <= -0.05:
                                        sentiment_label = "Negative"

                                display_data.append({
                                    "Title": title,
                                    "Sentiment Score (VADER)": sentiment_score,
                                    "Sentiment Label": sentiment_label
                                })

                            df = pd.DataFrame(display_data)

                            st.subheader(f"Sentiment Summary for '{selected_topic}' News Titles")

                            if not df.empty:
                                sentiment_counts = df["Sentiment Label"].value_counts().reset_index()
                                sentiment_counts.columns = ["Sentiment", "Count"]

                                st.write("Distribution of sentiment across article titles found:")
                                st.dataframe(sentiment_counts, hide_index=True, use_container_width=True)

                                if not sentiment_counts.empty:
                                    most_common_sentiment_row = sentiment_counts.loc[sentiment_counts['Count'].idxmax()]
                                    most_common_sentiment = most_common_sentiment_row['Sentiment']
                                    most_common_count = most_common_sentiment_row['Count']

                                    if most_common_count > 0:
                                        st.info(f"Overall, the sentiment of the news titles for '{selected_topic}' leans **{most_common_sentiment}**.")
                                    else:
                                         st.info("No articles with definitive positive/negative/neutral sentiment found.")
                            else:
                                st.info("No articles with calculable sentiment found to summarize.")

                        else:
                            st.info(f"No articles found in the 'news' list for the topic '{selected_topic}'.")
                    else:
                        st.warning("Received no data and no specific error message from the API.")