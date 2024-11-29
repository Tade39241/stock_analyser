from newsapi import NewsApiClient
import requests
from bs4 import BeautifulSoup

# Connect to the NewsAPI using the unique key 
api_key = '68fb419ed37d46eab18ce14d524371e5'
newsapi = NewsApiClient(api_key = api_key)

# Class that stores all details of the news of the given company 
class CompanyNews:

    def __init__(self, company):

        self.company = company
        self.articles = newsapi.get_everything(q = self.company,
        language = 'en',
        sort_by= 'publishedAt',
        page_size = 10)

        self.titles = []
        self.urls = []
        self.dates = []
        self.article_texts = []

    def setTitles(self):
        for article in self.articles['articles']:
            self.titles.append(article['title'])

    def setURLs(self):
        for article in self.articles['articles']:
            self.urls.append(article['url'])

    def setDates(self):
        for article in self.articles['articles']:
            self.dates.append(article['publishedAt'])

    def getTitles(self):
        return self.titles

    def getDescriptions(self):
        return self.descriptions

    def getURLs(self):
        return self.urls

    def getDates(self):
        return self.dates

    def getText(self):
        return self.article_texts

    # Output details of each news articles to terminal
    def displayNews(self):

        i = 0
        for i in range(len(self.articles['articles']) - 1):
            print(self.getTitles()[i])
            print("\n")
            print(self.getURLs()[i])
            print("\n")
            print(self.getDates()[i])
            print("\n")

    # Scrape all text from the news articles 
    def setText(self):

        i = 0
        for i in range(len(self.articles['articles']) - 1):

            try:
                response = requests.get((self.getURLs()[i]))
                response.raise_for_status()

                bs = BeautifulSoup(response.content, 'html.parser')

                # Remove all content of webpage that is not HTML
                for non_text in bs(['script', 'style']):
                    non_text.decompose()

                main_content = bs.find('article') or bs.find('div', role='main') or bs.find('main')
                if main_content:
                    self.article_texts.append(' '.join(main_content.stripped_strings))
                else:
                    self.article_texts.append(' '.join(bs.body.stripped_strings))

            # Error capture if scraping is unsuccessful
            except requests.exceptions.HTTPError as http_err:
                 return (http_err.status, http_err)
            except Exception as err:
                return (err)

    # Output text of each news article of the given company
    def displayTexts(self):

        for text in self.getText():

            print("-" *20)
            print(text)
            print("-" *20)