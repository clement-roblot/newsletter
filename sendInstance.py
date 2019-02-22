#!/usr/bin/env python3

import csv
import random
import xkcd
import webbrowser
import os
import datetime
import argparse
import smtplib, ssl
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from mako.template import Template
from secrets import *


# Header like grit or the husle etc..
# A random picture from IG
# A quote from the list
# # articles from the most popular articles in hacker news and other websites like that


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

    return randomComic



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
        dailyXKCD = getRandomXkcd()

        mailTemplate = Template(filename="./mailTemplate.html")
        mailInstance = mailTemplate.render(dailyQuote=dailyQuote[0],
                                           dailyQuoteAuthor=dailyQuote[1],
                                           imageUrl=dailyXKCD["imgUrl"],
                                           imageTitle=dailyXKCD["title"])
        
        # print(mailInstance)

        if args.test == False:
            sendEmail(mailInstance)
        else:
            with open("testEmail.html", "w") as testEmailFile:        
                testEmailFile.write(str(mailInstance))
            filename = 'file:///'+os.getcwd()+'/' + 'testEmail.html'
            webbrowser.open_new_tab(filename)
