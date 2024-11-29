import stock_info
import news
from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer

# Using all news articles and VaderSentiment, get average decayed sentiment score of given company
def averageScore(company_texts):

    total = 0
    count = 0
    decay_factor = 0.95
    latest_news = company_texts
    analyzer = SentimentIntensityAnalyzer()

    for text in latest_news:
        count += 1
        if (count % 10 == 0) and decay_factor < 1: 
            decay_factor += 0.05
        
        total += analyzer.polarity_scores(text)['compound'] * decay_factor

    return 0.5 * ((total/count) + 1)

# Returns the average daily change in the close stock prices of the given company
def stockPercentage(stockPrices):

    total_percentage = 0 
    i = 1 
    for i in range(len(stockPrices) - 1):
        
        total_percentage += ((stockPrices[i + 1] - stockPrices[i]) / stockPrices[i]) * 100

    return total_percentage / len(stockPrices)

stock_ticker = 'AAPL'
company_name = 'Apple'

stockInformation = stock_info.StockInformation(stock_ticker)
companyNews = news.CompanyNews(company_name)
companyNews.setTitles()
companyNews.setURLs()
companyNews.setDates()
companyNews.setText()
stockInformation.setClosePrices()

# Combine the news sentiment score and average daily change to get final sentiment score of the company
final_sentiment = str(round(((averageScore(companyNews.getText()) + stockPercentage(stockInformation.getClosePrices())) / 2) * 100)) + '%'

print("News Sentiment: " + str(averageScore(companyNews.getText())))
print("Average Daily Stock Change: " + str(stockPercentage(stockInformation.getClosePrices())) + "%")
print("Sentiment Score: " + final_sentiment)
