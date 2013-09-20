#!/usr/bin/python
# -*- coding: utf-8 -*-

import time, hmac, base64, hashlib, urllib, urllib2, json
from matplotlib import pyplot as plt

class Mtgox:
    '''
    class designed to interact with Mt.Gox API 2.

    Example Usage:
        mtgox = Mtgox(key='yourKeyHere', secret='youSecretHere')
        mtgox.getTicker(fast=True)
    '''
    currencyInfo='''BTC\tBitcoin\t100,000,000\t1e8
                    USD\tUS Dollar\t100,000\t1e5
                    GBP\tGreat British Pound\t100,000\t1e5
                    EUR\tEuro\t100,000\t1e5
                    JPY\tJapanese Yen\t1000\t1e3
                    AUD\tAustralian Dollar\t100,000\t1e5
                    CAD\tCanadian Dollar\t100,000\t1e5
                    CHF\tSwiss Franc\t100,000\t1e5
                    CNY\tChinese Yuan\t100,000\t1e5
                    DKK\tDanish Krone\t100,000\t1e5
                    HKD\tHong Kong Dollar\t100,000\t1e5
                    PLN\tPolish Złoty\t100,000\t1e5
                    RUB\tRussian Rouble\t100,000\t1e5
                    SEK\tSwedish Krona\t1000\t1e3
                    SGD\tSingapore Dollar\t100,000\t1e5
                    THB\tThai Baht\t100,000\t1e5
                    NOK\tNorwegian Krone\t100,000\t1e5
                    CZK\tCzech Koruna\t100,000\t1e5'''

    def __init__(self, key='', secret='', agent='btc_bot', currency = 'USD', timeout = 10, tryout = 5):
        self.key = key
        self.secret = secret
        self.agent = key, secret, agent

        self.currency = currency

        self.time = {'init': time.time(), 'req': time.time()}
        self.reqs = {'max': 10, 'window': 10, 'curr': 0}
        self.base = 'https://data.mtgox.com/api/2/'

        self.timeout = timeout
        self.tryout = tryout

        #build currency info dictionary
        self.currencyDict = {}
        for currency in self.currencyInfo.split('\n'):
            data = currency.strip().split('\t')
            self.currencyDict[data[0]] = {'name':data[1], 'div':float(data[2].replace(',','')), 'sf':float(data[3])}

    def __sendRequest__(self, path, data):
        '''
        Send request to API.
        '''

        return urllib2.Request(self.base + path, data, {
            'User-Agent': self.agent,
            'Rest-Key': self.key,
            'Rest-Sign': base64.b64encode(str(hmac.new(base64.b64decode(self.secret), path + chr(0) + data, hashlib.sha512).digest())),
		})


    def __throttle__(self):
        # check that in a given time window (10 seconds),
		# no more than a maximum number of requests (10)
		# have been sent, otherwise sleep for a bit
        diff = time.time() - self.time['req']
        if diff > self.reqs['window']:
            self.reqs['curr'] = 0
            self.time['req'] = time.time()
        self.reqs['curr'] += 1
        if self.reqs['curr'] > self.reqs['max']:
            print 'Request limit reached...'
            time.sleep(self.reqs['window'] - diff)

    def __request__(self, path, inp={}):

        t = time.time()
        attempts = 0

        while True:
			# check if have been making too many requests
			self.__throttle__()

			try:
				# send request
				inp['nonce'] = str(int(time.time() * 1e6))
				inpstr = urllib.urlencode(inp.items())
				req = self.__sendRequest__(path, inpstr)
				response = urllib2.urlopen(req, inpstr)

				# parse json response
				output = json.load(response)
				if 'error' in output:
					raise ValueError(output['error'])
				return output

			except Exception as e:
				print "Error: %s" % e

			# check timeout and tryout
			attempts += 1
			if time.time() - t > self.timeout or attempts > self.tryout:
				raise Exception('Timeout')

    def getTickerData(self, fast = True):
        if fast:
            return self.__request__('BTC'+self.currency+'/money/ticker_fast')
        else:
            return self.__request__('BTC'+self.currency+'/money/ticker')

    def getTicker(self, fast = True):
        dataDict = self.getTickerData(fast=fast)['data']

        returnDict = {u'currency':dataDict['buy']['currency']}

        for key in dataDict.keys():
            try:
                returnDict[key] = int(dataDict[key]['value_int'])/self.currencyDict[returnDict['currency']]['div']
            except:
                pass

        return returnDict


if __name__=='__main__':
    gox = Mtgox(key = 'yourkeyhere',
                secret = 'youtsecretehere',
                currency = 'USD')

    buy = []
    for i in range(100):
        buy.append(gox.getTickerPretty(fast=False)['buy'])
        time.sleep(1.2)


    plt.plot(buy)
    plt.show()
