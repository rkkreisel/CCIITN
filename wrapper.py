from ibapi import *
import logging 

from ibapi import wrapper
from ibapi.utils import iswrapper
from ibapi.contract import *
from ibapi.common import *
from ibapi.ticktype import *
from ibapi.execution import *

import config
from logic import AppLogic 


class TICKTYPE:
    DELAYED_LAST_PRICE = 68

class AppWrapper(wrapper.EWrapper):
    def __init__(self):
        wrapper.EWrapper.__init__(self)
        self.console = logging.getLogger("console")
        self.logic = AppLogic(self)
        self.startedLogic = False

    @iswrapper
    def nextValidId(self, orderId):
        self.logic.nextValidId = orderId
        self.console.info("Next Order ID: {}".format(orderId))
        if not self.startedLogic:
            self.logic.start()
            self.startedLogic = True

    @iswrapper
    def managedAccounts(self, accountsList):
        accounts = accountsList.split(",")
        if len(accounts) > 1: 
            self.console.error("Recieved More than One Account. Not Implemented.")
        self.logic.account = accounts[0]
        self.console.info("Received Account ID: {}".format(self.logic.account))
        
    @iswrapper
    def contractDetails(self, reqId, contractDetails):
        super().contractDetails(reqId, contractDetails)
        symbol = contractDetails.summary.localSymbol
        expires = contractDetails.summary.lastTradeDateOrContractMonth
        self.console.info("Received Contract Details for: {}. Expires: {}".format(symbol, expires))
        self.logic.pushData(reqId, {symbol : contractDetails})
        
    def contractDetailsEnd(self, reqId):
        super().contractDetailsEnd(reqId)
        self.console.info("Got All Contract Details.")
        self.logic.finishRequest(reqId)

    @iswrapper        
    def tickPrice(self, reqId, tickType, price, attrib):
        super().tickPrice(reqId, tickType, price, attrib)
        try: 
            stock = self.logic.subscriptions[reqId]
        except:
            self.console.error("Got Price Data for Unknown Subscription ID: {}".format(reqId))
            return 

        if tickType == TICKTYPE.DELAYED_LAST_PRICE:
            self.logic.priceData.update({stock.summary.localSymbol : price})