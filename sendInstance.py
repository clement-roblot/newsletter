#!/usr/bin/env python3

from __future__ import absolute_import
from __future__ import division, print_function, unicode_literals

import csv
import random
import xkcd
import webbrowser
import os
import datetime
import argparse
import requests
import smtplib, ssl
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from mako.template import Template
from secrets import *


from sumy.parsers.html import HtmlParser
from sumy.parsers.plaintext import PlaintextParser
from sumy.nlp.tokenizers import Tokenizer
from sumy.summarizers.lsa import LsaSummarizer as Summarizer
from sumy.nlp.stemmers import Stemmer
from sumy.utils import get_stop_words

# Header like grit or the husle etc..
# A random picture from IG
# A quote from the list
# # articles from the most popular articles in hacker news and other websites like that
# Have some music in the newsletter like gary playlist



class Image():
    title = None
    url = None

    def __init__(self, title, url):
        self.title = title
        self.url = url


class Article():
    title = None
    summary = None
    url = None
    image = None

    language = "english"
    sentencesCount = 3

    def __init__(self, url):
        self.url = url
        self.getSummary()

        print(self.summary)

    def getSummary(self):

        # https://github.com/miso-belica/sumy
        
        parser = HtmlParser.from_url(self.url, Tokenizer(self.language))
        stemmer = Stemmer(self.language)

        summarizer = Summarizer(stemmer)
        summarizer.stop_words = get_stop_words(self.language)

        # print("Article : " + str(self.url))
        self.summary = ""
        for sentence in summarizer(parser.document, self.sentencesCount):
            self.summary = self.summary + str(sentence)


def getRandomQuote(path):

    selectedQuoteNumber = 0
    with open(path, newline='\n') as csvfile:
        quoteReader = csv.reader(csvfile, delimiter=',', quotechar='\"')

        nbrQuotes = sum(1 for quote in quoteReader)
        selectedQuoteNumber = random.randint(1, nbrQuotes)

    with open(path, newline='\n') as csvfile:
        # Reload the CSV file
        quoteReader = csv.reader(csvfile, delimiter=',', quotechar='\"')
        for i in range(selectedQuoteNumber-1):
            next(quoteReader)

        selectedQuote = next(quoteReader)
        return selectedQuote


def getRandomXkcd():

    randomComic = {}

    randomComicObj = xkcd.getRandomComic()

    randomComic["title"] = randomComicObj.getAsciiTitle().decode('ascii')
    randomComic["imgUrl"] = randomComicObj.getAsciiImageLink().decode('ascii')

    imageTitle = "<a href=\"https://xkcd.com/\">XKCD : " + randomComic["title"] + "</a>"

    imageObj = Image(imageTitle, randomComic["imgUrl"])

    return imageObj


def getRandomImage():

    imageTitle = "<a href=\"https://unsplash.com\">Unsplash</a>"

    imageObj = Image(imageTitle, "https://source.unsplash.com/daily?landscape")

    return imageObj


def getHNStories(count):

    # https://hacker-news.firebaseio.com/v0/topstories.json

    newsList = requests.get("https://hacker-news.firebaseio.com/v0/topstories.json")
    newsList = newsList.json()
    newsList = newsList[:count]

    articles = []
    for news in newsList:

        newsObj = requests.get("https://hacker-news.firebaseio.com/v0/item/" + str(news) + ".json")
        newsObj = newsObj.json()

        article = Article(newsObj["url"])
        articles.append(article)

    return articles


def sendEmail(htmlVersion, txtVersion=""):

    message = MIMEMultipart("alternative")
    message["Subject"] = "The Tech Spyglass"
    message["From"] = sender_email
    message["To"] = receiver_email

    # Turn these into plain/html MIMEText objects
    part1 = MIMEText(htmlVersion, "html")
    message.attach(part1)

    if txtVersion != "":
        part2 = MIMEText(text, "plain")
        message.attach(part2)

    # Create secure connection with server and send email
    context = ssl.create_default_context()
    with smtplib.SMTP_SSL("smtp.gmail.com", 465, context=context) as server:
        server.login(sender_email, password)
        server.sendmail(
            sender_email, receiver_email, message.as_string()
        )


def needToSendEmail():

    now = datetime.datetime.now()

    try:
        with open("lastSent", "r") as lastSentFile:
            lastSent = datetime.datetime.strptime(lastSentFile.read(), '%Y-%m-%d')

            dateDiff = (now - lastSent)

            if dateDiff.days < 1:
                return False
    except:
        pass

    # Write date in file
    with open("lastSent", "w") as lastSentFile:        
        lastSentFile.write(str(now.date()))

    return True

if __name__ == "__main__":

    parser = argparse.ArgumentParser(description='Process some integers.')
    parser.add_argument('--test', dest='test', action='store_const',
                       const=True, default=False,
                       help='Generate a test email and display it in a browser')
    args = parser.parse_args()

    if (needToSendEmail() == True) or (args.test == True):
        dailyQuote = getRandomQuote("./quotes.csv")
        # dailyImage = getRandomXkcd()
        dailyImage = getRandomImage()
        articles = getHNStories(3)

        # https://loremflickr.com/500/500/landscape
        # https://source.unsplash.com/daily?travel
        # https://source.unsplash.com/daily?landscape


        mailTemplate = Template(filename="./mailTemplate.html")
        mailInstance = mailTemplate.render(dailyQuote=dailyQuote[0],
                                           dailyQuoteAuthor=dailyQuote[1],
                                           imageUrl=dailyImage.url,
                                           imageTitle=dailyImage.title)
        
        # print(mailInstance)

        if args.test == False:
            sendEmail(mailInstance)
        else:
            with open("testEmail.html", "w") as testEmailFile:        
                testEmailFile.write(str(mailInstance))
            filename = 'file:///'+os.getcwd()+'/' + 'testEmail.html'
            #webbrowser.open_new_tab(filename)
