import datetime
import threading
import pandas as pd
import os
from utils import utils

import alpaca_trade_api as tradeapi
import time
from alpaca_trade_api.rest import TimeFrame

class TradeAlgo:
    def __init__(self):
        self.alpaca = tradeapi.REST(os.environ["APCA_API_KEY_ID"],
                                os.environ["APCA_API_SECRET_KEY"],
                                os.environ["APCA_API_BASE_URL"],
                                'v2')
        
        stockUniverse = os.environ["STOCK_UNIVERSE"].split(",")
        
        # Format the allStocks variable for use in the class.
        self.allStocks = []
        for stock in stockUniverse:
            self.allStocks.append([stock, 0])
        
        self.timeToClose = None
        self.opening = True
        
    def run(self):
        utils.p_error("NOTIFICATION: RUNNING A LOW-POWER LONG-SHORT ALGO")
        utils.p_sep()
        
        # Await the market open
        print("Waiting for market to open...")
        tAMO = threading.Thread(target=self.awaitMarketOpen)
        tAMO.start()
        tAMO.join()
        print("Market opened.")
        
        # Rebalance the portfolio every minute, making necessary trades.
        while True:
            # Figure out when the market will close so we can prepare to sell beforehand.
            clock = self.alpaca.get_clock()
            closingTime = clock.next_close.replace(tzinfo=datetime.timezone.utc).timestamp()
            currTime = clock.timestamp.replace(tzinfo=datetime.timezone.utc).timestamp()
            self.timeToClose = closingTime - currTime
            
            if(self.timeToClose < (60 * 15)):
                # Run script again after market close for next trading day.
                print("Sleeping until market close (15 minutes).")
                time.sleep(60 * 15)
                
                self.opening = True
        
                print("Waiting for market to open...")
                tAMO = threading.Thread(target=self.awaitMarketOpen)
                tAMO.start()
                tAMO.join()
                print("Market opened.")
            else:
                # Rebalance the portfolio, and do stuff for the day
                # Change self.opening to False once we remove old stocks
                
                # tRebalance = threading.Thread(target=self.rebalance)
                # tRebalance.start()
                # tRebalance.join()
                time.sleep(60)
        
        
    # Wait for market to open.
    def awaitMarketOpen(self):
        isOpen = self.alpaca.get_clock().is_open
        while(not isOpen):
            clock = self.alpaca.get_clock()
            openingTime = clock.next_open.replace(tzinfo=datetime.timezone.utc).timestamp()
            currTime = clock.timestamp.replace(tzinfo=datetime.timezone.utc).timestamp()
            timeToOpen = int((openingTime - currTime) / 60)
            
            print("Time until market opens: [" + utils.p_time(timeToOpen) + "]")
      
            time.sleep(60)
            isOpen = self.alpaca.get_clock().is_open