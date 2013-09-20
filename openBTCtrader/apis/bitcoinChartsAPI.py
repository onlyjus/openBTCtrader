# -*- coding: utf-8 -*-

import time, hmac, base64, hashlib, urllib, urllib2, json, pprint



class bitcoinCharts(object):
    def __init__(self):
        self.base =  'http://api.bitcoincharts.com'

    def getTicker(self):

        jsonData = urllib2.urlopen(self.base + '/v1/markets.json').read()

        output = json.loads(jsonData)

        return output


if __name__=='__main__':
    btcCharts = bitcoinCharts()
    pprint.pprint( btcCharts.getTicker())