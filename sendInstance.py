#!/usr/bin/env python3

from __future__ import absolute_import
from __future__ import division, print_function, unicode_literals

import xkcd
import os
import datetime
import argparse
import requests
import extraction
import smtplib, ssl
import urllib.parse
from random import randrange
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from mako.template import Template
from openai import OpenAI

client = OpenAI(
    api_key=os.environ.get("OPENAI_API_KEY"),
)

class Image():
    title = None
    url = None

    def __init__(self, title, url):
        self.title = title
        self.url = url

    def isValidImage(self):

        try:
            image_formats = ("image/png", "image/jpeg", "image/jpg")
            r = requests.head(self.url, timeout=5)
            if r.headers["content-type"] in image_formats:
                return True
        except requests.exceptions.ConnectionError:
            # Our request got rejected
            return False
        except requests.exceptions.InvalidSchema:
            # Our request got rejected
            return False
        except requests.exceptions.ReadTimeout:
            # Our request got rejected
            return False
        except KeyError:
            # The response doesn't have "content-type"
            return False
        
        return False


class Article():
    title = None
    summary = None
    url = None
    image = None

    language = "english"
    sentencesCount = 1

    def __init__(self, url):
        self.url = url
        self.pocketUrl = "https://getpocket.com/edit?url=" + urllib.parse.quote_plus(self.url)

        try:
            self.htmlContent = requests.get(self.url, timeout=5).text
        except requests.exceptions.ConnectTimeout:
            self.htmlContent = None
        except requests.exceptions.ReadTimeout:
            self.htmlContent = None

        print("Initing article")
        self.getSummary()
        print("Got summed article")
        self.getMetadata()
        print("Got metadata article")

    def isValid(self):

        if self.htmlContent is None:
            return False

        # If we fail to get the image
        if not self.image:
            return False

        if not self.image.isValidImage():
            return False

        # If we catch a capcha
        if "are you a robot" in self.title.lower():
            return False

        return True

    def getMetadata(self):
        try:
            extracted = extraction.Extractor().extract(self.htmlContent, source_url=self.url)

            self.title = extracted.title

            if extracted.image:
                self.image = Image(self.title, extracted.image)
        except:
            self.initializedProperly = False

    def getSummary(self):

        try:
            prompt = f"Please summarize the following article in one paragraph as a teaser for it. Do not start with \"in this article\":\n\n{self.url}"
            chat_completion = client.chat.completions.create(
                messages=[
                    {
                        "role": "user",
                        "content": prompt, 
                    }
                ],
                model="gpt-3.5-turbo",
            )

            self.summary = chat_completion.choices[0].message.content
            return self.summary
        except Exception as e:
            print("Error summurizing:")
            print(e)
            self.initializedProperly = False


def getRandomQuote():

    baseAddress = "https://directus.martobre.fr"

    # Login
    payload = {"email": "clement.roblot@martobre.fr", "password": os.getenv("DIRECTUS_PASSWORD")}

    try:
        r = requests.post(baseAddress+"/auth/login", json=payload)

        token = r.json()["data"]["access_token"]
        # refreshToken = r.json()["data"]["refresh_token"]

        # Get quotes count
        headers = {"Authorization": f"Bearer {token}"}
        r = requests.get(baseAddress+"/items/Quotes?aggregate[count]=*", headers=headers)
        quotesCount = r.json()["data"][0]["count"]

        randomIndex = randrange(quotesCount)

        headers = {"Authorization": f"Bearer {token}"}
        r = requests.get(baseAddress+f"/items/Quotes?limit=1&offset={randomIndex}", headers=headers)

        quote = r.json()["data"][0]["Quote"]
        author = r.json()["data"][0]["Author"]
    except:
        quote = "The best way to predict the future is to invent it."
        author = "Alan Kay"

    return [quote, author]


def getRandomXkcd():

    randomComic = {}

    randomComicObj = xkcd.getRandomComic()

    randomComic["title"] = randomComicObj.getAsciiTitle().decode('ascii')
    randomComic["imgUrl"] = randomComicObj.getAsciiImageLink().decode('ascii')

    imageTitle = "<a href=\"https://xkcd.com/\">XKCD : " + randomComic["title"] + "</a>"

    imageObj = Image(imageTitle, randomComic["imgUrl"])

    return imageObj


def getRandomImage():
    url = "https://api.unsplash.com/photos/random"
    params = {
        'query': 'landscape',
        'orientation': 'landscape',
        'client_id': os.environ.get("UNSPLASH_API_KEY"),
    }
    
    try:
        response = requests.get(url, params=params)
        
        if response.status_code == 200:
            data = response.json()
            image_url = data['urls']['full']

            imageTitle = "<a href=\"https://unsplash.com\">Unsplash</a>"
            imageObj = Image(imageTitle, image_url)

            if imageObj:
                if imageObj.isValidImage():
                    return imageObj
    except:
        pass
            
    return None


def getHNStories(count):

    # https://hacker-news.firebaseio.com/v0/topstories.json

    newsList = requests.get("https://hacker-news.firebaseio.com/v0/topstories.json")
    newsList = newsList.json()

    articles = []
    for news in newsList:

        newsObj = requests.get("https://hacker-news.firebaseio.com/v0/item/" + str(news) + ".json", timeout=5)
        newsObj = newsObj.json()

        print("Got article")
        if "url" not in newsObj:
            continue

        article = Article(newsObj["url"])

        # If the article was properly fetched with it's image
        if article.isValid():
            articles.append(article)

        if len(articles) == count:
            break

    return articles


# Switch to api call to mailgun: https://stackoverflow.com/questions/6270782/how-to-send-an-email-with-python
def sendEmail(htmlVersion, txtVersion=""):

    message = MIMEMultipart("alternative")
    message["Subject"] = "The Tech Spyglass"
    message["From"] = os.getenv("NEWSLETTER_SENDER")
    message["To"] = os.getenv("NEWSLETTER_RECEIVER")

    # Turn these into plain/html MIMEText objects
    part1 = MIMEText(htmlVersion, "html")
    message.attach(part1)

    if txtVersion != "":
        part2 = MIMEText(text, "plain")
        message.attach(part2)

    # Create secure connection with server and send email
    context = ssl.create_default_context()
    with smtplib.SMTP_SSL("smtppro.zoho.com", 465, context=context) as server:
        server.login(os.getenv("NEWSLETTER_SENDER"), os.getenv("NEWSLETTER_PASSWORD"))
        server.sendmail(
            os.getenv("NEWSLETTER_SENDER"), os.getenv("NEWSLETTER_RECEIVER"), message.as_string()
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


def processEmail(args):

    print("Assembling the message")
    dailyQuote = getRandomQuote()
    # dailyImage = getRandomXkcd()
    dailyImage = getRandomImage()
    articles = getHNStories(3)

    print("Finished the message")

    # https://loremflickr.com/500/500/landscape
    # https://source.unsplash.com/daily?travel
    # https://source.unsplash.com/daily?landscape

    mailTemplate = Template(filename="./mailTemplate.html")
    mailInstance = mailTemplate.render(dailyQuote=dailyQuote[0],
                                       dailyQuoteAuthor=dailyQuote[1],
                                       articles=articles,
                                       closingImage=dailyImage)

    if args.test == False:
        sendEmail(mailInstance)
    else:
        with open("testEmail.html", "w") as testEmailFile:
            testEmailFile.write(str(mailInstance))
        filename = 'file:///'+os.getcwd()+'/' + 'testEmail.html'


def main():
    parser = argparse.ArgumentParser(description='Process some integers.')
    parser.add_argument('--test', dest='test', action='store_const',
                        const=True, default=False,
                        help='Generate a test email and display it in a browser')
    args = parser.parse_args()

    processEmail(args)


if __name__ == "__main__":
    main()
