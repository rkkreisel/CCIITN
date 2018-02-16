""" Create and Transmit Orders """
########## STDLIB IMPORTS ##########
from ibapi.order import Order
########## CUSTOM IMPORTS ##########
from logger import getConsole as console
import config

def logOrder(ledger, orderId, symbol, order, newStatus, oldStatus):
    """ Log Order Status to CSV and Console if the State has Changed """
    price = order.auxPrice if order.auxPrice != 0 else order.lmtPrice
    action, quantity, orderType = order.action, order.totalQuantity, order.orderType

    orderMsg = "{} {} {} @ {} ${:.2f}".format(action, quantity, symbol, orderType, price)
    msg = "ID: {} Status: [{}]: {}".format(orderId, orderMsg, newStatus)
    if oldStatus != newStatus:
        if newStatus not in ["PendingSubmit", "PreSubmitted"]:
            console().info(msg)
        ledger.log(orderId, symbol, action, orderType, quantity, price, newStatus)
