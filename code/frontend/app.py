from flask import Flask, render_template, request, jsonify, redirect, session
from newsapi import NewsApiClient
import requests
from textblob import TextBlob
import yfinance as yf
import pandas as pd

app = Flask(__name__)



app.secret_key = 'your_secret_key'

users = {
    'user1': 'password1',
    'user2': 'password2'
}

# Initialise the News API client
newsapi = NewsApiClient(api_key='5f9c7090bce540c8b737cb253212a8d9')

# Route for the homepage
@app.route('/')
def index():
    return render_template('index.html')

# Route for fetching news articles
@app.route('/news')
def get_news():
    # Fetch news articles related to companies
    articles = newsapi.get_top_headlines(q='company', language='en', country='gb')
    return render_template('news.html', articles=articles['articles'])

# Route for analysing sentiment
@app.route('/analyse_sentiment')
def analyse_sentiment():
    # Fetch news articles related to companies
    articles = newsapi.get_top_headlines(q='company', language='en', country='gb')

    # Analyse sentiment of each article
    sentiments = []
    for article in articles['articles']:
        blob = TextBlob(article['content'])
        sentiment = blob.sentiment.polarity
        sentiments.append(sentiment)

    return render_template('sentiment.html', articles=articles['articles'], sentiments=sentiments)

# Route for displaying company overview
@app.route('/company_overview/<ticker>')
def company_overview(ticker):
    # Fetch company data using yfinance
    company = yf.Ticker(ticker)
    info = company.info
    history = company.history(period='1y')

    return render_template('company.html', info=info, history=history)

# Route for the categories page
@app.route('/categories')
def categories():
    return render_template('categories.html')

# Route for the companies page
@app.route('/companies', methods=['GET', 'POST'])
def companies():
    if request.method == 'POST':
        ticker = request.form['ticker']
        company_data, error_message = fetch_company_data(ticker)
        if error_message:
            return render_template('companies.html', error_message=error_message)
        else:
            return render_template('companies.html', company_data=company_data.to_dict('records'))
    return render_template('companies.html')

def fetch_company_data(ticker):
    try:
        company = yf.Ticker(ticker)
        history = company.history(period='1y')
        # Convert the historical market data to a pandas DataFrame
        history_df = pd.DataFrame(history)
        return history_df, None
    except Exception as e:
        return None, str(e)

# Route for the about page
@app.route('/about')
def about():
    return render_template('about.html')

# Login route
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        if username in users and users[username] == password:
            session['username'] = username
            return redirect('/homepage')
        else:
            return render_template('login.html', error='Invalid username or password')
    return render_template('login.html')

# Logout route
@app.route('/logout')
def logout():
    session.pop('username', None)
    return redirect('/login')

# Home route (requires login)
@app.route('/homepage')
def home():
    if 'username' in session:
        username = session['username']
        return render_template('homepage.html', username=username)
    else:
        return redirect('/login')

# Registration route
@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        if username in users:
            return render_template('register.html', error='Username already exists')
        else:
            users[username] = password
            session['username'] = username
            return redirect('/homepage')
    return render_template('register.html')

def get_company_data(ticker):
    # Fetch company data using yfinance
    company = yf.Ticker(ticker)
    company_info = company.info
    company_data = {
        "logo_url": company_info.get('logo_url', None),
        "name": company_info.get('shortName', None),
        "info": f"{company_info.get('regularMarketPrice', 'N/A')} ({company_info.get('regularMarketChangePercent', 'N/A')}%)"
    }
    

    # Fetch news articles related to the company
    articles = newsapi.get_everything(q=company_data['name'], language='en', sort_by='relevancy')

    # Extract relevant information from articles
    company_data['articles'] = []
    for article in articles['articles']:
        article_data = {
            "title": article.get('title', 'N/A'),
            "description": article.get('description', 'N/A'),
            "url": article.get('url', 'N/A')
        }
        company_data['articles'].append(article_data)

    return company_data

def extract_images(articles):
    extracted_images = []
    for article in articles:
        if 'urlToImage' in article:
            extracted_images.append(article['urlToImage'])
        else:
            # If no image is available, you can add a placeholder image URL
            extracted_images.append('https://example.com/placeholder.jpg')
    return extracted_images

companies_data = [
    {"name": "Meta", "ticker": "META"},
    {"name": "Apple", "ticker": "AAPL"},
    {"name": "Google", "ticker": "GOOGL"},
    {"name": "Microsoft", "ticker": "MSFT"}
]

# Route for searching companies
@app.route('/search_company')
def search_company():
    query = request.args.get('company_name')
    companies_df = pd.DataFrame(companies_data)
    companies_list = companies_df.to_dict(orient='records')
    search_results = [company for company in companies_list if query.lower() in company['name'].lower()]
    return render_template('companies.html', search_results=search_results)

# Function to fetch news articles from NewsAPI
def get_news_articles(query):
    api_key = '5f9c7090bce540c8b737cb253212a8d9'
    url = f"https://newsapi.org/v2/everything?q={query}&apiKey={api_key}"
    response = requests.get(url)
    data = response.json()
    articles = data['articles']
    return articles

# Route for displaying company dashboard
@app.route('/company_dashboard/<ticker>')
def company_dashboard(ticker):
    # Fetch company data
    company_data = get_company_data(ticker)
    # Fetch news articles related to the company
    news_articles = newsapi.get_everything(q=ticker, language='en', sort_by='relevancy')
    # Select the top 10 articles
    top_10_articles = news_articles['articles'][:10]

    company_data = yf.Ticker(ticker)
    hist = company_data.history(period="1d")
    daily_growth = round(((hist['Close'].iloc[-1] / hist['Open'].iloc[0]) - 1) * 100,2)

    return render_template('company_dashboard.html', company_data=company_data, articles=top_10_articles,daily_growth=daily_growth)

if __name__ == '__main__':
    app.run(debug=True)