Stock Analysis Platform
A web application built with Streamlit that provides users with tools for stock price forecasting and news sentiment analysis, integrated within a secure login system.

Features
Secure User Authentication:

User login and signup system.

User credentials stored in a local CSV file (users.csv).

Stock Price Forecasting:

Fetch historical End-of-Day (EOD) stock data using the MarketStack API.

Implement and compare forecasting models: Simple Moving Average (SMA), Random Forest Regressor, and Linear Regression.

Evaluate model performance using Mean Absolute Percentage Error (MAPE).

Predict the average stock price for the next business day using the best-performing model.

News Sentiment Analysis:

Fetch news articles based on selected topics or companies using the World News API.

Analyze the sentiment of news headlines using the VADER library.

Categorize sentiment as Positive, Negative, or Neutral.

Display a summary of sentiment distribution.

User-Friendly Interface:

Interactive web application built with Streamlit.

Clear navigation between features after login.

Display of data, model results, and sentiment summaries.

Technologies Used
Python: The core programming language.

Streamlit: For building the web application interface.

Pandas: For data manipulation and handling.

NumPy: For numerical operations.

Requests: For making API calls to MarketStack and World News API.

Scikit-learn: For implementing and evaluating machine learning models.

VADER Sentiment: For performing sentiment analysis.

MarketStack API: External API for stock data.

World News API: External API for news articles.

Setup and Installation
Clone the repository:

git clone <repository_url>
cd <repository_name>

Replace <repository_url> with the actual URL of your GitHub repository and <repository_name> with the repository's directory name.

Create a virtual environment (recommended):

python -m venv venv

Activate the virtual environment:

On Windows:

.\venv\Scripts\activate

On macOS and Linux:

source venv/bin/activate

Install dependencies:

pip install -r requirements.txt

(Note: You might need to create a requirements.txt file containing the required libraries: streamlit, pandas, requests, numpy, scikit-learn, vaderSentiment).

Obtain API Keys:

Get an API key from MarketStack.

Get an API key from World News API.

Configure API Keys:

Open model.py and replace "YOUR_MARKETSTACK_API_KEY" with your actual MarketStack API key.

Open news.py and replace "YOUR_WORLDNEWS_API_KEY" with your actual World News API key.

Security Note: Hardcoding API keys directly in the code is not secure for production. For a real application, consider using environment variables or Streamlit Secrets.

How to Run
Ensure your virtual environment is active.

Run the Streamlit application:

streamlit run main.py

The application will open in your web browser.

File Structure
main.py: Main application file, handles navigation and integration.

login.py: Contains the LoginSystem class for user authentication.

model.py: Contains the StockForecastingApp class for stock data fetching and forecasting.

news.py: Contains the NewsSentimentAnalyzerApp class for news fetching and sentiment analysis.

users.csv: Stores user credentials (created automatically on first signup).

requirements.txt: Lists project dependencies.

Security Note
Please be aware that this project stores user passwords in plain text within the users.csv file. This is not secure for production environments. For a real-world application, you must implement proper password hashing and salting.

Future Enhancements
Implement secure password hashing.

Integrate more advanced forecasting models (e.g., ARIMA, LSTM).

Explore more sophisticated sentiment analysis techniques.

Add more data sources (e.g., fundamental data).

Improve data visualizations.

Add user portfolios or watchlists.

Implement alerts and notifications.

Deploy the application.
