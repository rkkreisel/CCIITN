""" Trading Algorithm Definition """

########## STDLIB IMPORTS ##########
import threading
from time import sleep
from talib import CCI
import numpy as np
########## CUSTOM IMPORTS ##########
from logger import getConsole as console
from contracts import getContractDetails, updateFuture
from tradingday import TradingDay, updateToday
import config
from constants import MARKET_DATA_TYPES
from helpers import waitForProp
from account import Account
import requests


########## CLASS DEFINITON ##########
class AppLogic(threading.Thread):
    """ Thread to Hold Algorithm Logic """
    def __init__(self, client):
        threading.Thread.__init__(self)
        self.daemon = True
        self.client = client
        self.name = "Logic"
        self.future = None
        self.account = Account()

########## MAIN ALGO LOGIC  ##########
    def run(self):
        client = self.client
        console().info("Staring CCI ITN App Logic...")

        console().info("Setting Market Data Type : {}".format(config.DATATYPE))
        client.reqMarketDataType(MARKET_DATA_TYPES[config.DATATYPE])

        client.reqOpenOrders()

        getContractDetails(client)
        waitForProp(self, "future")
        today = TradingDay(self.future)
        state = getNewState()

        requests.subscribeCCIBars(client, self.future)

        while True:
            sleep(.05) # Reduce Processor Load.
            updateFuture(client, self.future)
            newDay = updateToday(today)
            if newDay != today:
                state = getNewState()
            today = newDay

            #Sleep on Non-Trading Days
            if not today.normalDay: continue

def getNewState():
    """ Generate a Blank State for a New Day """
    return {
        "executedToday" : False
    }

def calculateCCI(bars):
    high = np.array([x.High for x in bars])
    low = np.array([x.Low for x in bars])
    close = np.array([x.Close for x in bars])
    cci = CCI(high, low, close, config.TIME_PERIODS)[19]
    return cci

    