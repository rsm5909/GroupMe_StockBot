
# IMPORTS
import os
import json
from urllib.parse import urlencode
from urllib.request import Request, urlopen
from flask import Flask, request
import requests
import re

app = Flask(__name__)



@app.route('/', methods=['POST'])
def webhook():
    token = os.environ.get('token')
    print(type(token))
    data = request.get_json()
    text = str(data['text'])
    tickers = re.findall(r'\$([^a-z\d][^\ &]+)(?=&(peers|chart|pt|news))*', text)
    
    if len(tickers) >= 1:
        for ticker in tickers:
            if ticker[1] == "":
                replyString = stockQuote(ticker[0], token)
                reply(replyString)
            elif ticker[1] == 'chart':
                reply_with_image(ticker[0])
            elif ticker[1] == 'peers':
                replyString = peers(ticker[0], token)
                reply(replyString)
            elif ticker[1] == 'pt':
                replyString = price_target(ticker[0], token)
                reply(replyString)
            elif ticker[1] == 'news':
                replyString = news(ticker[0], token)
                reply(replyString)

    return "ok", 200


def stockQuote(ticker,token):
    url = 'https://cloud.iexapis.com/v1/stock/{}/quote?token={}'.format(ticker, token)
    print(ticker)
    print(url)
    r = requests.get(url)
    if r.status_code == 200:
        response = requests.get(url).json()
        if response['companyName']:
            companyName = response['companyName']
        else:
            companyName = 'N/A'
        if response['latestPrice']:
            latestPrice = response['latestPrice']
        else:
            latestPrice = 0
        if response['changePercent']:
            changePercent = response['changePercent']
        else:
            changePercent = 0
        if response['peRatio']:
            peRatio = response['peRatio']
        else:
            peRatio = 0
        replyString = "Name: {},  Last price: {:.2f},  Pct chg: {:.2%},  P/E: {:.2f}x".format(companyName, latestPrice, changePercent, peRatio)
    elif r.status_code == 404:
        replyString = "Stonk not found :-("
    else:
        replyString = "You retard! response={}".format(r.status_code)
    return replyString

def peers(ticker,token):
    url = 'https://cloud.iexapis.com/v1/stock/{}/peers?token={}'.format(ticker, token)
    r = requests.get(url)
    if r.status_code == 200:
        response = requests.get(url).json()
        reply = str(response)
        return reply

def price_target(ticker,token):
    url = 'https://cloud.iexapis.com/v1/stock/{}/price-target?token={}'.format(ticker, token)
    r = requests.get(url)
    if r.status_code == 200:
        response = requests.get(url).json()
        reply = str(response)
        return reply

def news(ticker,token):
    url = 'https://cloud.iexapis.com/v1/stock/{}/news/last/5?token={}'.format(ticker, token)
    r = requests.get(url)
    if r.status_code == 200:
        response = requests.get(url).json()
        x=[(x['headline'], x['url']) for x in response]
        reply = str(x)
        return reply

# Send a message in the groupchat
def reply(msg):
    bot = os.environ.get('botid')
    url = 'https://api.groupme.com/v3/bots/post'
    data = {'bot_id':bot, 'text':msg}
    request = Request(url, urlencode(data).encode())
    json = urlopen(request).read().decode()

def upload_image(imgURL):
    session = requests.Session()
    access = os.environ.get('access')
    imgRequest = session.get(imgURL, stream=True, timeout=10, headers={'User-Agent': 'Mozilla/5.0'})
    filename = 'temp.png'
    postImage = None
    if imgRequest.status_code == 200:
        # Save Image
        with open(filename, 'wb') as image:
            for chunk in imgRequest:
                image.write(chunk)
        # Send Image
        headers = {'content-type': 'application/json'}
        url = 'https://image.groupme.com/pictures'
        files = {'file': open(filename, 'rb')}
        payload = {'access_token': access}
        r = requests.post(url, files=files, params=payload, timeout=10)
        imageurl = r.json()['payload']['url']
        os.remove(filename)
        return imageurl

def reply_with_image(ticker):
    bot = os.environ.get('botid')
    token = os.environ.get('token')
    url = 'https://api.groupme.com/v3/bots/post'
    imgURL = 'https://c.stockcharts.com/c-sc/sc?s={}&p=D&b=5&g=0&i=0&r=1564148102465'.format(ticker)
    msg = stockQuote(ticker,token)
    urlOnGroupMeService = upload_image(imgURL)
    print(urlOnGroupMeService)
    print('!!!!!!!!!!{}!!!!!!!!'.format(urlOnGroupMeService))
    data = {
        'text' : msg,
        'bot_id'        : bot,
        'picture_url'       : urlOnGroupMeService
    }
    request = Request(url, urlencode(data).encode())
    json = urlopen(request, timeout=10).read().decode()
