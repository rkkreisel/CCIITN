""" IBAPI / CCI ITN Constant Variable Declarations """
########## STDLIB IMPORTS ##########
from collections import namedtuple

########## CONSTANT DEFINITIONS ##########
MARKET_DATA_TYPES = {
    "LIVE" : 1,
    "FROZEN" : 2,
    "DELAYED" : 3,
    "FROZEN_DELAYED" : 4
}

TICK_TYPES = {
    "LAST_PRICE": 4
}

BAR = namedtuple("BAR",["Time","High","Low","Close"])
