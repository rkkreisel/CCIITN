import argparse
import os
import sys
import signal
import pdb

import ibapi
from ibapi.client import EClient

from wrapper import AppWrapper
import config
import multiprocessing

import logging

########## CLASSES ##########
class AppClient(EClient):
    def __init__(self, wrapper):
        EClient.__init__(self, wrapper)
                    
class CCITrader(AppWrapper, AppClient):
    def __init__(self):
        AppWrapper.__init__(self)
        AppClient.__init__(self, wrapper=self)
        signal.signal(signal.SIGINT, self.interruptHandler) # CTRL + C
        #signal.signal(signal.SIGTSTP, self.debugHandler) # CTRL + Z
        #signal.signal(signal.SIGINFO, self.statusHandler) #CTRL + T

    def interruptHandler(self, signum, frame):
        console = logging.getLogger(name="console")
        if len(self.logic.subscriptions) > 0:
            console.info("Stopping Streaming Market Subscriptions...")
            for id, data in self.logic.subscriptions.items():
                console.info("Stopping Subscription: {}".format(data.summary.localSymbol))
                self.cancelMktData(id)
        console.info("Disconnecting From API...")
        self.disconnect()
        sys.exit(0)

    def debugHandler(self, signum, frame):
        console = logging.getLogger(name="console")
        console.info("Starting Debugging Console...")
        import pdb;pdb.set_trace()
        
    def statusHandler(self, signum, frame):
        self.logic.printPriceData()  
                    
########## FUNCTIONS ##########
def setupLogger():
    
    if os.path.exists(config.LOGFILE):
        os.remove(config.LOGFILE)
    
    logformat = "%(asctime)s -  %(funcName)s::%(lineno)d [%(threadName)s]: %(message)s"
    
    filelogger = logging.getLogger()
    logging.basicConfig(
        filename = config.LOGFILE,
        level = logging.INFO, 
        format = logformat)
        
    console = logging.getLogger(name="console")
    console_handler = logging.StreamHandler(stream=sys.stdout)
    console_handler.setFormatter(logging.Formatter(logformat))
    console.addHandler(console_handler)
    
    return console
    
########## MAIN ##########
def main():
    console = setupLogger()
    console.info("Started CCITrader v{}".format(config.VERSION))
    
    app = CCITrader()
    
    try:
        console.info("Connecting to TWS API  on HOST {} and PORT {}".format(config.HOST,config.PORT))
        console.info("Using Interactive Brokers API Version: {}".format(ibapi.get_version_string()))
        app.connect(config.HOST, config.PORT, clientId=0)
        if app.isConnected():
            console.info("Connection Successful.  Server Version: {}".format(app.serverVersion()))
            try:
                app.run()
            except AttributeError:
                pass
        else:
            console.info("Connection Failed")
    except:
        raise
        
if __name__ == "__main__":
    main()