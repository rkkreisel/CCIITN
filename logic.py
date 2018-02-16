""" Trading Algorithm Definition """

########## STDLIB IMPORTS ##########
import threading
from time import sleep

########## CUSTOM IMPORTS ##########
from logger import getConsole as console
from contracts import getContractDetails, updateFuture
from tradingday import TradingDay, updateToday
import config
from constants import MARKET_DATA_TYPES
from helpers import waitForProp
from account import Account


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