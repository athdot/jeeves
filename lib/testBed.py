import datetime
import threading
import pandas as pd
import os
from scipy import stats
from utils import *

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
        self.allStocks = stockUniverse
                
    def run(self):
        utils.p_error("TEST FUNCTION RUNNER")
        utils.p_sep()
        
        self.run_tests(30)
        
        utils.p_sep()
        utils.p_error("OPERATION COMPLETE")
        utils.p_sep()
        
    def run_tests(self, period):
        run_num = 4
        
        # Header
        print("Day-Period: " + str(run_num))
        print("Function to Test: delta_pctg")
        utils.p_sep()
        
        # Official tests
        print("Running Tests, starting " + str(period) + " day(s) ago..")
        p_accuracy = list() # List
        weekend_offset = 0
        for day in range(1, period + 1):
            print("Executing Day " + str(day) + "...")
            predictions = [] # List of predictions per stock for the day
            actuals = [] # List of actual stock movements
            
            day_today = pd.Timestamp('now').date() - pd.Timedelta(days = day + weekend_offset)
            
            if day_today.weekday() > 4:
                weekend_offset = weekend_offset + 2
            
            for stock_name in self.allStocks:
                local_bars = self.get_bars(stock_name, run_num, day + weekend_offset)
                
                # Generate prediction
                local_perdiction = self.trend_line(local_bars)
                
                if local_perdiction > 0:
                    local_perdiction = "P"
                elif local_perdiction == 0:
                    local_perdiction = "-"
                elif local_perdiction < 0:
                    local_perdiction = "N"
                
                predictions.append([stock_name, local_perdiction])
                
                actuals.append([stock_name, self.get_day_behaviour(stock_name, day + weekend_offset)])
            
            # Perdictions generated, validate them and get a correctness score
            totals = 0
            for val in range(0, len(actuals)):
                if actuals[val] == predictions[val]:
                    totals = totals + 1
            print("  Accuracy: " + str(totals/len(actuals)))
            p_accuracy.append(totals / len(actuals))
        
        # Everything has been tested
        print("DONE")
        utils.p_sep()
        print(str(period) + " tests run with an average correctness of " + str(100 * sum(p_accuracy) / len(p_accuracy)) + "%...")
            
    def get_day_behaviour(self, stock, day):
        day_bar = self.get_bars(stock, 2, day - 1)
        
        local_perdiction = day_bar[1].c - day_bar[0].c

        if local_perdiction > 0:
            local_perdiction = "P"
        elif local_perdiction == 0:
            local_perdiction = "-"
        elif local_perdiction < 0:
            local_perdiction = "N"

        return local_perdiction

    def get_bars(self, stock, period, hist_period):
        day = pd.Timestamp('now').date() - pd.Timedelta(days = (hist_period + 1))
        bars = self.alpaca.get_bars(stock, TimeFrame.Day,
                                    day - pd.Timedelta(days = 1 + period + 2 * int(period / 7 + 1)),
                                    day,
                                    adjustment='raw')
        bar_count = 0
        for bar in bars:
            bar_count = bar_count + 1
        bars = bars[bar_count - period:]
        
        return bars
        

    def trend_line(self, bars):
        # Trendline
        mean_val_y = list()
        for bar in bars:
            mean_val_y.append(float(bar.c))

        # Convert to precentages
        temp = list()
        for val in range(0, len(mean_val_y) - 1):
            temp.append(100 * (mean_val_y[val + 1] - mean_val_y[val]) / mean_val_y[val])

        mean_val_y = temp

        mean_val_x = list()
        for val in range(0, len(mean_val_y)):
            mean_val_x.append(val)

        slope, intercept, r_value, p_value, std_err = stats.linregress(mean_val_y, mean_val_x)
        
        return slope
    
    def delta_pctg(self, bars):
        # Trendline
        mean_val_y = list()
        for bar in bars:
            mean_val_y.append(float(bar.c))

        # Convert to precentages
        temp = list()
        for val in range(0, len(mean_val_y) - 1):
            temp.append(100 * (mean_val_y[val + 1] - mean_val_y[val]) / mean_val_y[val])
        
        return sum(temp) / len(temp)