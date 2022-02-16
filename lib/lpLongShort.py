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
        
        self.long = []
        self.short = []
        self.qShort = None
        self.qLong = None
        self.adjustedQLong = None
        self.adjustedQShort = None
        self.blacklist = set()
        self.longAmount = 0
        self.shortAmount = 0
        
        # Function Parameters
        self.short_position_ratio = 0.3 
        self.percent_period = 10 # Period in seconds to view retrospectively, to order stocks
        self.equity_cash_ratio = 0.95 # Only maximise equity usage to this percentage
        
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
                
                tRebalance = threading.Thread(target=self.rebalance)
                tRebalance.start()
                tRebalance.join()
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
            
    
    def rebalance(self):
        tRerank = threading.Thread(target=self.rerank)
        tRerank.start()
        tRerank.join()
        
        # TODO
        
    # Re-rank all stocks to adjust longs and shorts.
    def rerank(self):
        # Rank all stocks from greatest to least on percentage change in the last 10 min
        tRank = threading.Thread(target=self.rank)
        tRank.start()
        tRank.join()
        
        # TODO: Change how we rank to give us a better estimate for a day
      
    # Mechanism used to rank the stocks, the basis of the Long-Short Equity Strategy.
    def rank(self):
        # Ranks all stocks by percent change over the past 10 minutes (higher is better).
        tGetPC = threading.Thread(target=self.getPercentChanges)
        tGetPC.start()
        tGetPC.join()

        # Sort the stocks in place by the percent change field (marked by pc).
        self.allStocks.sort(key=lambda x: x[1])
        
    # Get percent changes of the stock prices over the past 10 minutes.
    def getPercentChanges(self):
        length = int(self.percent_period)
        for i, stock in enumerate(self.allStocks):
            bars = self.alpaca.get_bars(stock[0], TimeFrame.Minute,
                                        pd.Timestamp('now').date(),
                                        pd.Timestamp('now').date(), limit=length,
                                        adjustment='raw')
            bar_count = 0
            for j in bars:
                bar_count = bar_count + 1
    
            stock_index = 0
            for j in self.allStocks:
                if j[0] == stock[0]:
                    break
                stock_index = stock_index + 1
    
            if bar_count > 0:
                self.allStocks[stock_index][1] = (bars[bar_count - 1].c - bars[0].o) / bars[0].o
        
    # Submit an order if quantity is above 0.
    def submitOrder(self, qty, stock, side, resp):
        if(qty > 0):
            try:
                self.alpaca.submit_order(stock, qty, side, "market", "day")
                print("Market order of | " + str(qty) + " " + stock + " " + side + " | completed.")
                resp.append(True)
            except:
                print("Order of | " + str(qty) + " " + stock + " " + side + " | did not go through.")
                resp.append(False)
        else:
            print("Quantity is 0, order of | " + str(qty) + " " + stock + " " + side + " | not completed.")
            resp.append(True)
            
    # Get the total price of the array of input stocks.
    def getTotalPrice(self, stocks, resp):
        totalPrice = 0
        for stock in stocks:
            bars = self.alpaca.get_bars(stock, TimeFrame.Minute,
                                        pd.Timestamp('now').date(),
                                        pd.Timestamp('now').date(), limit=1,
                                        adjustment='raw')
            totalPrice += bars[0].c
            
        resp.append(totalPrice)

    # Submit a batch order that returns completed and uncompleted orders.
    def sendBatchOrder(self, qty, stocks, side, resp):
        executed = []
        incomplete = []
        for stock in stocks:
            if(self.blacklist.isdisjoint({stock})):
                respSO = []
                tSubmitOrder = threading.Thread(target=self.submitOrder, args=[qty, stock, side, respSO])
                tSubmitOrder.start()
                tSubmitOrder.join()
                if(not respSO[0]):
                    # Stock order did not go through, add it to incomplete.
                    incomplete.append(stock)
                else:
                    executed.append(stock)
                respSO.clear()
        resp.append([executed, incomplete])