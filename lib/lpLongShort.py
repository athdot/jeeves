import datetime
import threading
import pandas as pd
import os
import utils

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
        
    def run(self):
        utils.p_error("NOTIFICATION: RUNNING A LOW-POWER LONG-SHORT ALGO")
        utils.p_sep()
        
        # Await the market open
        print("Waiting for market to open...")
        tAMO = threading.Thread(target=self.awaitMarketOpen)
        tAMO.start()
        tAMO.join()
        print("Market opened.")
        
        
    # Wait for market to open.
    def awaitMarketOpen(self):
        isOpen = self.alpaca.get_clock().is_open
        while(not isOpen):
            clock = self.alpaca.get_clock()
            openingTime = clock.next_open.replace(tzinfo=datetime.timezone.utc).timestamp()
            currTime = clock.timestamp.replace(tzinfo=datetime.timezone.utc).timestamp()
            timeToOpen = int((openingTime - currTime) / 60)
            print("Time until market opens: [", end="")
            time_list = []
            if int(timeToOpen / (60 * 24)) > 0:
                time_list.append(str(int(timeToOpen / (60 * 24))) + " day")
                if int(timeToOpen / (60 * 24)) > 1:
                    time_list[len(time_list) - 1] = time_list[len(time_list) - 1] + "s"
            if int(timeToOpen / 60) % 24 > 0:
                time_list.append(str(int(timeToOpen / 60) % 24) + " hour")
                if int(timeToOpen / 60) % 24 > 1:
                    time_list[len(time_list) - 1] = time_list[len(time_list) - 1] + "s"
            if timeToOpen % 60 > 0:
                time_list.append(str(timeToOpen % 60) + " minute")
                if timeToOpen % 60 > 1:
                    time_list[len(time_list) - 1] = time_list[len(time_list) - 1] + "s"
                    
            if len(time_list) > 2:
                time_list[len(time_list) - 1] = "and " + time_list[len(time_list) - 1]
                time_list = [", " + s for s in time_list]
                time_list[0] = time_list[0][2:]
            else:
                if len(time_list) > 1:
                    time_list[len(time_list) - 1] = " and " + time_list[len(time_list) - 1]
            
            print("".join(time_list), end="")
            
            print("]")
      
            time.sleep(60)
            isOpen = self.alpaca.get_clock().is_open