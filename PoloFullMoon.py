#!/usr/bin/env python3
# -*- coding: utf-8 -*-

#トレード対象の通貨ペア
Currency_Pair = 'USDT_BTC'

#この数値％以上買値から上がったらBTC売却する
Exit_Gain_Percentage = 10

#この数値％以上下がったらBTC購入する
Entry_Drop_Percantage = 5

#ドル建て総資産のうち、この数値％分のBTCを購入する
Trade_USD_Percantage = 50

#アクセスキー
API_Key = ''

#シークレットアクセスキー
API_Secret = ''


from datetime import datetime
from poloniex import Poloniex
from math import floor
import sys
import json
import requests
import time
import hmac
import hashlib


class Polo:

    def __init__(self):
        
        self.public = Poloniex()
        self.private = Poloniex(API_Key, API_Secret)

        self.watch()

    def watch(self):

        res = self.private.returnBalances()
        self.btc = float(res['BTC'])
        self.usd = float(res['USDT'])
        self.xrp = float(res['XRP'])
        self.xem = float(res['XEM'])
        self.ltc = float(res['LTC'])
        self.eth = float(res['ETH'])

        res = self.public.returnOrderBook(Currency_Pair)

        self.ask = [float(res['asks'][0][0]), float(res['asks'][0][1])]
        self.bid = [float(res['bids'][0][0]), float(res['bids'][0][1])]

    def sell(self, am):
        return self.private.sell('USDT_BTC', self.bid[0], am)

    def buy(self, am):
        return self.private.buy('USDT_BTC', self.ask[0], am)


class Position:

    def __init__(self):
        self.api = Polo()

        if 0 < self.api.btc:
            self.entryPrice = self.api.ask[0]
            self.lastHighPrice = -1
        else:
            self.entryPrice = -1
            self.lastHighPrice = self.api.bid[0]

    def watch(self):
        tm = datetime.now().strftime('%Y/%m/%d %H:%M:%S')
        
        if 0 < self.entryPrice:
            price = self.api.bid[0]
            p = round(100 * (price - self.entryPrice) / self.entryPrice, 2)
            print(' ' + tm + ' 現在 BTC=' + str(price) + ' USD,  買値(' + str(self.entryPrice) + ' USD)から ' + ('+' if 0 < p else '') + str(p) + '%,  ' + self.getBalance(), end = '\r')

            if Exit_Gain_Percentage < p:
                self.sell(price)

        else:
            if self.lastHighPrice < self.api.bid[0]:
                self.lastHighPrice = self.api.bid[0]
  
            price = self.api.ask[0]
            p = round(100 * (price - self.lastHighPrice) / self.lastHighPrice, 2)
            print(' ' + tm + ' 現在 BTC=' + str(price) + ' USD,  直近高値(' + str(self.lastHighPrice) + ' USD)から ' + ('+' if 0 < p else '') + str(p) + '%,  ' + self.getBalance(), end = '\r')

            if Entry_Drop_Percantage < -1 * p or True:
                self.buy(price)
            
    def getBalance(self):
        return ('総資産 ' + str(floor(self.api.usd + self.api.bid[0] * self.api.btc)) + ' USD (' + str(self.api.usd) + ' USD + ' + str(self.api.btc) + ' BTC)')

    def buy(self, price):

        amount = floor(Trade_USD_Percantage * self.api.usd * 0.01 / price)

        print('\nBTC買い ' + str(amount) + 'BTC (1BTC=' + str(price) + 'USD)')
        print(self.api.buy(amount))
        print('\n')
        time.sleep(5)

        if 0 < self.api.btc:
            self.entryPrice = self.api.ask[0]
            self.lastHighPrice = -1

    def sell(self, price):

        print('\nBTC売り ' + str(self.api.btc) + 'BTC (1BTC=' + str(price) + 'USD)')
        print(self.api.sell(self.api.btc))
        print('\n')
        time.sleep(5)

        if 0 == self.api.btc:
            self.entryPrice = -1
            self.lastHighPrice = self.api.bid[0]
 

if __name__ == '__main__':

    tc = Position()

    while(True):
        try:
            tc.watch()
        except Exception as e:
            print(e)
            time.sleep(10)

        time.sleep(1)
