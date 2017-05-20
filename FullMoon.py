#!/usr/bin/env python3
# -*- coding: utf-8 -*-

#この数値％以上買値から上がったらBTC売却する
Exit_Gain_Percentage = 10

#この数値％以上下がったらBTC購入する
Entry_Drop_Percantage = 5

#日本円総資産のうちこの数値％分のBTCを購入する
Trade_JPY_Percantage = 50

#アクセスキー
API_Key = 'APIキー'

#シークレットアクセスキー
API_Secret = 'APIシークレット'


from datetime import datetime
from math import floor
import sys
import json
import requests
import time
import hmac
import hashlib


class ApiCall:

    def __init__(self):
        self.api_key = API_Key
        self.api_secret = API_Secret
        self.api_endpoint = 'https://coincheck.com'

    def get_api_call(self,path):
        timestamp = str(int(time.time()))
        text = timestamp + self.api_endpoint + path
        sign = hmac.new(bytes(self.api_secret.encode('ascii')), bytes(text.encode('ascii')), hashlib.sha256).hexdigest()
        request_data=requests.get(
            self.api_endpoint+path
            ,headers = {
                'ACCESS-KEY': self.api_key,
                'ACCESS-NONCE': timestamp,
                'ACCESS-SIGNATURE': sign,
                'Content-Type': 'application/json'
                })
        return request_data

    def post_api_call(self,path,body):
        body = json.dumps(body)
        timestamp = str(int(time.time()))
        text = timestamp + self.api_endpoint + path + body
        sign = hmac.new(bytes(self.api_secret.encode('ascii')), bytes(text.encode('ascii')), hashlib.sha256).hexdigest()
        request_data=requests.post(
            self.api_endpoint+path
            ,data= body
            ,headers = {
                'ACCESS-KEY': self.api_key,
                'ACCESS-NONCE': timestamp,
                'ACCESS-SIGNATURE': sign,
                'Content-Type': 'application/json'
                })
        return request_data


class Position:

    TICKER = '/api/ticker'
    BALANCE = '/api/accounts/balance'
    ORDER = '/api/exchange/orders'    

    def __init__(self):
        self.api = ApiCall()

        if 0 < float(self.api.get_api_call(Position.BALANCE).json()['btc']) and False:
            self.entryPrice = self.getPrice('ask')
            self.lastHighPrice = -1
        else:
            self.entryPrice = -1
            self.lastHighPrice = self.getPrice('bid')


    def watch(self):
        tm = datetime.now().strftime('%Y/%m/%d %H:%M:%S')
        
        if 0 < self.entryPrice:
            price = self.getPrice('bid')
            p = round(100 * (price - self.entryPrice) / self.entryPrice, 2)
            net = self.getBalance(price)
            print(' ' + tm + ' 現在 BTC=' + str(price) + '円,  買値(' + str(self.entryPrice) + '円)から ' + ('+' if 0 < p else '') + str(p) + '%,  ' + net[0], end = '\r')

            if Exit_Gain_Percentage < p:
                self.sell(net[2], price)

        else:
            bid, ask = self.getPrice()
            if self.lastHighPrice < bid:
                self.lastHighPrice = bid
            
            p = round(100 * (ask - self.lastHighPrice) / self.lastHighPrice, 2)
            net = self.getBalance(bid)
            print(' ' + tm + ' 現在 BTC=' + str(ask) + '円,  直近高値(' + str(self.lastHighPrice) + '円)から ' + ('+' if 0 < p else '') + str(p) + '%,  ' + net[0], end = '\r')

            if Entry_Drop_Percantage < -1 * p:
                self.buy(net[1], ask)

            
    def getBalance(self, bid):
        res = self.api.get_api_call(Position.BALANCE).json()
        jpy = floor(float(res['jpy']))
        btc = float(res['btc'])
        return ('総資産 ' + str(floor(jpy + bid * btc)) + '円 (' + str(jpy) + 'JPY + ' + str(btc) + 'BTC)', jpy, btc)


    def buy(self, jpy, price):

        amount = floor(Trade_JPY_Percantage * jpy * 0.01)

        body = {
            'pair': 'btc_jpy',
            'order_type': 'market_buy',
            'market_buy_amount': amount
            }        

        print('\nBTC買い ' + str(amount) + '円 (1BTC=' + str(price) + '円)')
        print(self.api.post_api_call(Position.ORDER, body).json())
        print('\n')
        time.sleep(5)

        if 0 < float(self.api.get_api_call(Position.BALANCE).json()['btc']):
            self.entryPrice = self.getPrice('ask')
            self.lastHighPrice = -1


    def sell(self, btc, price):

        body = {
            'pair': 'btc_jpy',
            'order_type': 'market_sell',
            'amount': btc
            }

        print('\nBTC売り ' + str(btc) + 'BTC (1BTC=' + str(price) + '円)')
        print(self.api.post_api_call(Position.ORDER, body).json())
        print('\n')
        time.skeep(5)

        if 0 == float(self.api.get_api_call(Position.BALANCE).json()['btc']):
            self.entryPrice = -1
            self.lastHighPrice = self.getPrice('bid')



    def getPrice(self, which = 'both'):

        if which != 'both':
            return self.api.get_api_call(Position.TICKER).json()[which]
        else:
            res = self.api.get_api_call(Position.TICKER).json()
            return (res['bid'], res['ask'])
 

if __name__ == '__main__':

    tc = Position()

    while(True):
        tc.watch()
        time.sleep(1)
