""" Callback Functions from TWS Gateway / Workstation """

########## STDLIB IMPORTS ##########
from collections import deque
########## CUSTOM IMPORTS ##########

from ibapi import wrapper
from ibapi.utils import iswrapper

from logic import AppLogic, calculateCCI
from logger import getConsole as console
from constants import TICK_TYPES, BAR
from requests import subscribeAccountPositions
from contracts import getCurrentFuturesContract
from orders import logOrder
import config

########## CLASS DEFINITON ##########
class AppWrapper(wrapper.EWrapper):
    """ Thread to Manage Callbacks. """
    def __init__(self):
        wrapper.EWrapper.__init__(self)
        self.startedLogic = False
        self.logic = AppLogic(self)
        self.client = self.logic.client

    @iswrapper
    def nextValidId(self, orderId):
        self.logic.account.setNextOrderId(orderId)
        console().info("Next Order ID: {}".format(orderId))
        if not self.startedLogic:
            self.logic.start()
            self.startedLogic = True

    @iswrapper
    def managedAccounts(self, accountsList):
        self.logic.account.setAccount(accountsList)
        console().info("Received Account: {}".format(self.logic.account))
        subscribeAccountPositions(self.client)

    @iswrapper
    def contractDetails(self, reqId, contractDetails):
        super().contractDetails(reqId, contractDetails)
        symbol = contractDetails.summary.localSymbol
        expires = contractDetails.summary.lastTradeDateOrContractMonth
        console().info("Received Contract Details for: {}. Expires: {}".format(symbol, expires))
        self.client.pushRequestData(reqId, {symbol : contractDetails})

    @iswrapper
    def contractDetailsEnd(self, reqId):
        super().contractDetailsEnd(reqId)
        console().info("Got All Contract Details.")
        self.client.finishRequest(reqId)
        contractDetails = self.client.getRequestData(reqId)
        self.client.purgeRequest(reqId)
        self.logic.future = getCurrentFuturesContract(contractDetails)

    @iswrapper
    def tickPrice(self, reqId, tickType, price, attrib):
        super().tickPrice(reqId, tickType, price, attrib)
        if tickType == TICK_TYPES["LAST_PRICE"]:
            self.client.pushRequestData(reqId, {"price":{"last": price}})

    @iswrapper
    def tickSize(self, reqId, tickType, size):
        super().tickSize(reqId, tickType, size)

    @iswrapper
    def tickGeneric(self, reqId, tickType, value):
        super().tickGeneric(reqId, tickType, value)

    @iswrapper
    def tickString(self, reqId, tickType, value):
        super().tickString(reqId, tickType, value)

    @iswrapper
    def error(self, reqId, errorCode, errorString):
        super().error(reqId, errorCode, errorString)
        apiMessage(errorString)

    @iswrapper
    def position(self, account, contract, position, avgCost):
        super().position(account, contract, position, avgCost)
        if account == self.logic.account.account:
            console().info("Position Update: {}: #Contracts: {}".format(
                contract.localSymbol, position))
            self.logic.account.updatePosition(contract, position)
        else:
            console().warning("Got Position for Untracked Account: {}".format(account))

    @iswrapper
    def historicalData(self, reqId, bar):
        if("bars" not in self.client.data[reqId].keys()):
            self.client.pushRequestData(reqId, {"bars": deque(maxlen=config.TIME_PERIODS)})
        self.client.data[reqId]["bars"].append(BAR(High=bar.high,Low=bar.low,Close=bar.close,Time=bar.date))

    @iswrapper
    def historicalDataUpdate(self, reqId, bar):
        lastBar = self.client.data[reqId]["bars"][-1]
        newBar = BAR(High=bar.high,Low=bar.low,Close=bar.close,Time=bar.date)
        if (lastBar.Time == newBar.Time):
            self.client.data[reqId]["bars"][-1] = newBar
        else:
            self.client.data[reqId]["bars"].append(newBar)

        cci = calculateCCI(self.client.data[reqId]["bars"])
        console().info("Calculated CCI: {}".format(cci))

    @iswrapper
    def historicalDataEnd(self, reqId, start, end):
        super().historicalDataEnd(reqId, start, end)
        console().info("Got CCI Historical Data")
        self.client.finishRequest(reqId)

    @iswrapper
    def openOrder(self, orderId, contract, order, orderState):
        self.logic.account.tmpOrders[orderId] = (contract, order, orderState.status)

    @iswrapper
    def openOrderEnd(self):
        openOrders, tmpOrders = self.logic.account.openOrders, self.logic.account.tmpOrders
        ledger = self.client.ledger

        for orderId, values in tmpOrders.items():
            symbol, status = values[0].localSymbol, values[2]
            oldStatus = openOrders[orderId][2] if orderId in openOrders.keys() else None

            logOrder(ledger, orderId, symbol, values[1], status, oldStatus)

        self.logic.account.openOrders = tmpOrders
        self.logic.account.tmpOrders = {}


    @iswrapper
    def orderStatus(self, orderId, status, filled, remaining, avgFillPrice,
                    permId, parentId, lastFillPrice, clientId, whyHeld):

        if clientId != config.CLIENTID:
            return

        openOrders = self.logic.account.openOrders

        if orderId not in openOrders.keys():
            return

        contract, order, oldStatus = openOrders[orderId]
        symbol = contract.localSymbol

        logOrder(self.client.ledger, orderId, symbol, order, status, oldStatus)
        openOrders[orderId] = (contract, order, status)

        if status in ["Cancelled", "Filled"]:
            self.client.reqOpenOrders()

def apiMessage(msg):
    """ Print API Messages """
    msg = msg.replace("\n", ". ")
    console().info("API: {}".format(msg))
