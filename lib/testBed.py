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
        
        # self.run_candle_test()
        self.run_tests(30)

        utils.p_sep()
        utils.p_error("OPERATION COMPLETE")
        utils.p_sep()
        
    def run_tests(self, period):
        run_num = 3 # 4
        
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
                local_perdiction = self.simple_dir(local_bars)
                
                # Flip, betting on volitility
                local_perdiction = -local_perdiction

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

    def simple_dir(self, bars):
        mean_val_y = []
        for bar in bars:
            mean_val_y.append((bar.o + bar.c + bar.h + bar.l) / 4)

        # Convert to precentages
        temp = list()
        for val in range(0, len(mean_val_y) - 1):
            temp.append(100 * (mean_val_y[val + 1] - mean_val_y[val]) / mean_val_y[val])
        
        return sum(temp) / len(temp)
        
        return bars[len(bars) - 1].c - bars[len(bars) - 1 - day_period].o

    def run_candle_test(self):
        day_period = 10 # 15 for funsies, 10 for trends
        start_day = 0
        stock_name = "DOMO"

        # Header
        print("Day-Period: " + str(day_period))
        print("Function to Test: candle_analysis")
        print("Current Stock: " + stock_name)
        utils.p_sep()

        local_bars = self.get_bars(stock_name, day_period, start_day)

        local_perdiction = self.candle_analysis(local_bars)


    def candle_analysis(self, bars):
        # This function takes our inputted bars, and does a number of checks to find
        # Patterns within a period of X days
        # Outputs from this are supposed to follow this format
        #
        # p is pressure, True is up, False is down
        # r is relevance (how recent is it, lower is better) number of days essentially
        #
        # As of now, this is what we are checking for:
        # - Hammer & Reverse Hammer, Hanging man & Shooting star - DONE (Need better trend algo?)
        # - Bullish engulfing, Bearish engulfing - DONE (Need better trend algo?)
        # - Piercing line - DONE (Idk how id test this lol)
        # - Morning star, Evening star
        # - Three white soldiers, Three black crows
        # - Dark cloud cover
        #
        # Perhaps implement:
        # - Doji
        # - Spinning top
        # - Falling three methods, Rising three methods

        output_list = []

        # Check recent history for any evidence of a hammer, and if exists, add it to the output list

        # Bullish hammer viewing
        temp = [] # Right here, its a list of potential hammers within the study
        p_crop = 0.35 # Limiter for a hammer
        day_period = 6 # How many days prior we look for trends

        # HAMMERS
        for bar in range(0, len(bars)):
            c_bar = bars[bar]

            # Classify as a hammer if body is above/below 35% of height
            low = c_bar.o
            high = c_bar.c
            if c_bar.o > c_bar.c:
                low = c_bar.c
                high = c_bar.o

            if low > (c_bar.h - c_bar.l) * (1 - p_crop) + c_bar.l or high < (c_bar.h - c_bar.l) * p_crop + c_bar.l:
                # Qualifies as a hammer/star of some kind
                temp.append(bar)

        # TODO("If slope is too small, dont decide?")

        for val in temp:
            # Go through each identified hammer and see where the trend is headed
            # Period of 4 prior days
            rev_day = val - day_period
            
            if rev_day < 0:
                continue

            short_bars = bars[rev_day:val]

            # Trend line seems to preform well at 4 days
            # delta pctg seems to do well at 6
            trend = self.delta_pctg(short_bars)

            output_list.append({"t":"hammer","p":(trend < 0),"r":(len(bars) - val)})

        # ENGULFING
        for bar in range(1, len(bars)):
            p_bar = bars[bar - 1]
            c_bar = bars[bar]

            rev_day = bar - day_period

            if rev_day < 0:
                continue

            short_bars = bars[rev_day:bar]

            if c_bar.h > p_bar.h and c_bar.l < p_bar.l:
                if p_bar.o < p_bar.c:
                    if c_bar.o > c_bar.c:
                        # Bearish engulfing
                        # Check prior trend, if its positive, this means a possible reversal
                        trend = self.delta_pctg(short_bars)
                        if trend > 0:
                            # We have it!
                            output_list.append({"t":"engulfing","p":False,"r":(len(bars) - bar)})
                else:
                    if c_bar.o < c_bar.c:
                        # Bullish engulfing
                        # Check prior trend, if its negative, this means a possible reversal
                        trend = self.delta_pctg(short_bars)
                        if trend < 0:
                            # We have it!
                            output_list.append({"t":"engulfing","p":True,"r":(len(bars) - bar)})
        
        # PIERCING_LINE
        # Average bar size
        delta_b = 0
        for bar in bars:
            delta_b = delta_b + abs(bar.o - bar.c)
        delta_b = delta_b / len(bars)

        res = (sum([((abs(bar.o - bar.c) - delta_b) ** 2) for bar in bars]) / len(bars)) ** 0.5

        for bar in range(1, len(bars)):
            p_bar = bars[bar - 1]
            c_bar = bars[bar]

            # Is the bar size applicable?
            p_z_score = (abs(p_bar.o - p_bar.c) - delta_b) / res
            c_z_score = (abs(c_bar.o - c_bar.c) - delta_b) / res
            
            # 0.85 is about 80% of all candles
            z_limit = 0.85
            if p_z_score < z_limit or c_z_score < z_limit:
                continue

            if p_bar.o > p_bar.c and c_bar.o < c_bar.c and p_bar.c > c_bar.o and c_bar.c > (p_bar.o - p_bar.c) / 2 + p_bar.c:
                output_list.append({"t":"piercing","p":True,"r":(len(bars) - bar)})

        # STAR
        # TODO("Other patterns")

        # DEFAULT
        # Last 2 days sloping?
        day_period = 3
        output_list.append({"t":"default","p":(bars[len(bars) - 1].c - bars[len(bars) - 1 - day_period].o > 0),"r":0})

        print(output_list)

        return output_list