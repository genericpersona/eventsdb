# -*- coding: utf-8 -*-

# Imports
import json
import re

import requests

from utils.url import safe_get

# Constants
BTC_ADDR_RE = r'^[13][a-km-zA-HJ-NP-Z0-9]{26,33}$'
BTC_ADDR_RE = re.compile(BTC_ADDR_RE)

def balance(addr, min_confirms=6):
    '''
    Return the balance of a given Bitcoin address

    Parameters
    ----------
        addr: string
            Bitcoin address

        min_confirms: int
            Minimum number of confirms before considering an input
            part of the address' balance

            Defaults to Bitcoin Core's value of 6
    '''
    for obj in [BlockchainAPI(), BlockrAPI()]:
        try:
            bal = obj.balance(addr, min_confirms)
            if bal is not None:
                return bal
        except:
            pass

def block_hash(block):
    '''
    Return the hash of a given block

    Parameters
    ----------
        block: int
            Which block to retrieve the hash from
    '''

def btc_avg(currency):
    '''
    Return the current average in a given currency
    '''
    try:
      return BitcoinAverageAPI().average(currency)
    except:
      return

def btc_avg_usd():
    '''
    Return the current USD/BTC average price
    '''
    for obj in [BitcoinAverageAPI(), BlockrAPI()]:
        try:
            avg = obj.averageUSD()
            if avg is not None:
                return avg
        except:
            pass

def current_block():
    '''
    Return the current Bitcoin block
    '''
    for obj in [BlockchainAPI(), BlockExplorerAPI(), BlockrAPI()]:
        try:
            block = obj.currentBlock()
            if block is not None:
                return block
        except:
            pass

def latest_hash():
    '''
    Return the hash of the current block
    '''

def valid_address(addr):
    '''
    Return True if addr is a valid Bitcoin address

    Parameters
    ----------
        addr: string
            Potential Bitcoin address
    '''
    return BTC_ADDR_RE.match(addr) is not None

#-------------------------------------------------
#
#               Bitcoin API Classes
#
#-------------------------------------------------
class BitcoinAverageAPI(object):
    ALL = 'https://api.bitcoinaverage.com/ticker/global/all'
    LAST = 'https://api.bitcoinaverage.com/ticker/global/{}/last'

    def __init__(self):
        pass

    def average(self, currency):
        return safe_get([self.LAST.format(currency)], None)

    def averageUSD(self):
        return safe_get([self.LAST.format('USD')], None)

    def saveAll(self):
        self.all = safe_get([self.ALL], None)
        if self.all is not None:
            self.all = json.loads(self.all)
        return self.all is not None

class BlockchainAPI(object):
    ADDR_BAL = 'https://blockchain.info/q/addressbalance/{}?confirmations={}'
    BLOCK_INFO = 'https://blockchain.info/rawblock/{}'
    LAST_BLOCK = 'https://blockchain.info/q/getblockcount'
    LAST_HASH = 'https://blockchain.info/q/latesthash'

    def __init__(self):
        pass

    def balance(self, addr, min_confirms):
        bal = safe_get([self.ADDR_BAL.format(addr, min_confirms)], None)
        if not bal is None:
            return round(float(bal) / 1.e8, 8)

    def blockHash(self, block):
        info = safe_get([self.BLOCK_INFO.format(block)], None)
        if not info is None:
            return json.loads(info)['hash']

    def currentBlock(self):
        last = safe_get([self.LAST_BLOCK], None)
        if not last is None:
            return int(last)

    def latestHash(self):
        return safe_get([self.LASH_HASH], None)

class BlockExplorerAPI(object):
    BLOCK_HASH = 'https://blockexplorer.com/q/getblockhash/{}'
    LAST_BLOCK = 'https://blockexplorer.com/q/getblockcount'
    LAST_HASH = 'https://blockexplorer.com/q/latesthash'

    def __init__(self):
        pass

    def blockHash(self, block):
        return safe_get([self.BLOCK_HASH.format(block)], None)

    def currentBlock(self):
        last = safe_get([self.LAST_BLOCK], None)
        if not last is None:
            return int(last)

    def latestHash(self):
        return safe_get([self.LASH_HASH], None)

class BlockrAPI(object):
    AVG_RATE = 'http://btc.blockr.io/api/v1/exchangerate/current'
    BALANCE = 'http://btc.blockr.io/api/v1/address/balance/{}?confirmations={}'
    BLOCK_INFO = 'http://btc.blockr.io/api/v1/block/info/{}'
    LAST_BLOCK = 'http://btc.blockr.io/api/v1/block/info/last'

    def __init__(self):
        pass

    def averageUSD(self):
        avg = safe_get([self.AVG_RATE], None)
        if not avg is None:
            rates = json.loads(avg)['data'][0]['rates']
            usd = 1.0 / float(rates['BTC'])
            return round(usd, 2)

    def balance(self, addr, min_confirms):
        bal_url = self.BALANCE.format(addr, min_confirms)
        bal_url += '&amount_format=float'

        bal = safe_get([bal_url], None)
        if not bal is None:
            balj = json.loads(bal)
            return balj['data']['balance']

    def blockHash(self, block):
        block_data = safe_get([self.BLOCK_INFO.format(block)], None)
        if not block_data is None:
            block_data = json.loads(block_data)
            if block_data['status'] == 'success':
                return block_data['data']['hash']
    
    def currentBlock(self):
        last = safe_get([self.LAST_BLOCK], None)
        if not last is None:
            lastj = json.loads(last)
            return lastj['data']['nb']

    def latestHash(self):
        last = safe_get([self.LAST_BLOCK], None)
        if not last is None:
            lastj = json.loads(last)
            return lastj['data']['hash']
