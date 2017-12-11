import datetime
import logging
import threading
import time

from ibapi import *
from ibapi.contract import *


class AppLogic(threading.Thread):
    def __init__(self, app):
        threading.Thread.__init__(self)
        self.daemon = True
        self.app = app
        self.name = "Logic"
        self.console = logging.getLogger("console")
        self.account = None
        self.nextOrderId = None
        self.nextRequestId = 100
        self.nextSubscriptionId = 1
        
        self.priceData= {} 
        self.subscriptions = {}
        self.requests = {}

    def run(self): #MAIN APPLICATION LOGIC BLOCK
        self.console.info("Starting Application Logic Handler")

        #Request Details for ES
        contract = getContract() 
        self.console.info("Getting Details for Futures Symbol: {}".format(contract.symbol))
        contractDetails = self.getContractDetails(contract)
        
        #Select The Current ES Symbol (ex: ESZ7)
        self.console.info("Selecting Current Symbol for {}".format(contract.symbol))
        tradingContract = getCurrentFutureSymbol(contractDetails)
        self.console.info("Selected Trading Symbol: {}. Expires: {}".format(tradingContract.summary.localSymbol, tradingContract.summary.lastTradeDateOrContractMonth))

        #Start Receiving Market Data
        self.console.info("Requesting Market Data For: {}".format(tradingContract.summary.localSymbol))
        self.subscribe(tradingContract)

        #Subscribe to Market Data
        while True:
           time.sleep(1)

    def waitForProp(self, objname):
        while getattr(self, objname) is None:
            pass
    
    def waitForID(self,id):
        while self.requests[id] is None:
            pass
        while not self.requests[id]["complete"]:
            pass
    
    def pushData(self, id, data):
        if not isinstance(data, dict):
            print("Error. Non Dict Data Push")
            return
        self.requests[id].update(data)

    def getData(self, id):
        if not self.requests[id]["complete"]:
            return None
        self.requests[id].pop("complete")        
        return self.requests[id]

    def finishRequest(self, id):
        self.requests[id]["complete"] = True

    def startRequest(self):
        requestId = self.nextRequestId
        if self.nextRequestId == 1000:
            self.nextRequestId = 100
        else:
            self.nextRequestId += 1
        self.requests[requestId] = { "complete" : False}
        return requestId

    def subscribe(self, contractDetails):
        subscriptionID = self.nextSubscriptionId
        self.nextSubscriptionId += 1
        self.app.reqMarketDataType(3)
        self.app.reqMktData(subscriptionID, contractDetails.summary, "", False, False, None)
        self.subscriptions.update({subscriptionID : contractDetails})


    def getContractDetails(self, contract):
        requestID = self.startRequest()
        self.app.reqContractDetails(requestID, contract)
        self.waitForID(requestID)
        return self.getData(requestID)

    def printPriceData(self):
        for symbol, data in self.priceData.items():
            self.console.info("SYMBOL: {} PRICE: ${}".format(symbol,data))


def getContract():
    contract = Contract()
    contract.symbol = "ES"
    contract.secType = "FUT"
    contract.exchange = "GLOBEX"
    return contract

def getCurrentFutureSymbol(contractDetails):
    soonest = None   
    for symbol, data in contractDetails.items():
        expireString = data.summary.lastTradeDateOrContractMonth
        expireYear = int(expireString[:4])
        expireMonth = int(expireString[4:6])
        expireDay = int(expireString[6:8])

        expireDate = datetime.datetime(year=expireYear, month=expireMonth, day=expireDay)
        
        if soonest is None or (expireDate < soonest[0]):
            soonest = (expireDate, data)
    return soonest[1] 