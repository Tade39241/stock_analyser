import yfinance as yf
import pandas as pd
from newsapi import NewsApiClient


class StockInformation:
    def __init__(self, ticker, newsapi_key):
        self.ticker = ticker
        self.information = yf.Ticker(ticker)
        self.history = self.information.history(period="1y")
        self.newsapi_client = NewsApiClient(api_key=newsapi_key)  # Initialize NewsAPI client here

    def get_company_name(self):
        return self.information.info.get('longName', '')

    def get_logo_url(self):
        return self.information.info.get('logo_url', '')

    def get_daily_growth(self):
        hist = self.history
        try:
            daily_growth = round(((hist['Close'].iloc[-1] / hist['Open'].iloc[0]) - 1) * 100, 2)
        except IndexError:
            daily_growth = "Data not available"
        return daily_growth

    def get_news(self):
        # Convert the ticker to a string and use it for fetching news
        ticker_str = str(self.ticker)  # Explicitly convert ticker to string
        if ticker_str:
            try:
                response = self.newsapi_client.get_everything(q=ticker_str, language='en', sort_by='relevancy')
                return response['articles'][:10]  # Return the top 10 articles
            except Exception as e:
                print(f"Error fetching news for ticker {ticker_str}: {e}")
                return []
        else:
            print("Ticker is not defined.")
            return []  # Handle case where ticker is not valid or defined
        
    def get_price_data(self, period="1mo"):
        hist = self.information.history(period=period)
        # Convert to a suitable Python structure (list of dicts, etc.)
        price_data = hist[['Open', 'High', 'Low', 'Close']].reset_index().to_dict('records')
        return price_data
