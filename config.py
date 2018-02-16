""" CCI ITN Configuration Values """
from datetime import datetime
########## CONFIGURATION ##########

VERSION = "0.1"
LOGFILE = "ccitn_{}.log".format(datetime.now().strftime('%Y%m%d_%H%M'))
LEDGERFILE = "cciitn_trades.csv"

HOST = "localhost"
PORT = 55555
CLIENTID = 2

NUM_CONTRACTS = 1

SYMBOL = "ES"
EXCHANGE = "GLOBEX"

#Normal Timezone is CST.
NORMAL_TRADING_HOURS = "1700-1515,1530-1600"

# Type of Market Data To Stream. (LIVE, DELAYED, FROZEN_DELAYED)
DATATYPE = "LIVE"
