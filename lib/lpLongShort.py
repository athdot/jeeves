import datetime
import threading
import pandas as pd
import os
from utils import utils
from utils import mailjet

import alpaca_trade_api as tradeapi
import time
from alpaca_trade_api.rest import TimeFrame
from scipy import stats

class TradeAlgo:
    def __init__(self):
        self.alpaca = tradeapi.REST(os.environ["APCA_API_KEY_ID"],
                                os.environ["APCA_API_SECRET_KEY"],
                                os.environ["APCA_API_BASE_URL"],
                                'v2')

        # Message
        self.init_equity = -1.0
        self.allow_liquidations = False # True means that we care about stop-loss

        self.var_init()

    def var_init(self):
        positions = self.alpaca.list_positions()

        stockUniverse = os.environ["STOCK_UNIVERSE"].split(",")
        for p in positions:
            if stockUniverse.count(p.symbol) > 0:
                stockUniverse = os.environ["ALT_STOCK_UNIVERSE"].split(",")
                break
        
        # Format the allStocks variable for use in the class.
        self.allStocks = []
        for stock in stockUniverse:
            self.allStocks.append([stock, 0])
        
        self.timeToClose = None
        self.opening = True
        
        self.long = []
        self.short = []
        self.blacklist = set()
        self.longAmount = 0
        self.shortAmount = 0
        self.currentEquity = 0
        
        # Function Parameters
        self.short_position_ratio = 0.3 # How much of our cash is reserved for short positions
        self.long_position_ratio = 1.3 # % of portfolio allocated to long positions
        self.percent_period = 6 # Period in days to view retrospectively, to order stocks
        self.equity_cash_ratio = 1 # Only maximise equity usage to this percentage
        self.stock_cost_limiter = 0.5 # Remove stocks that cost more than X% of alloted cash

        # Risk Management
        self.relative_stock_allotment = 1 # % of available equity 1 stock can take up, maximum. The 1% Rule would be '0.01' -- limits stocks for small accounts
        self.stop_loss = 0.05 # Close a trade if we lose money by 5%
        self.take_profit = 0.15 # Close a trade if we profit by 15%
        self.profit_margins = [] # List of bounds for each trade
        self.do_stop_loss = True
        
        self.pdt_counter = 0
        
        self.do_init_reb = False

    def run(self):
        utils.print_header("lpLongShort.py") 
        utils.p_error("NOTIFICATION: RUNNING A LOW-POWER LONG-SHORT ALGO")
        utils.p_sep()

        if self.init_equity == -1.0:
            self.init_equity = float(self.alpaca.get_account().equity)
        
        # Run each day
        while True:
            # Await the market open
            tAMO = threading.Thread(target=self.awaitMarketOpen)
            tAMO.start()
            tAMO.join()

            # Refresh equity totals
            self.currentEquity = self.getUsableEquity()
            self.init_equity = float(self.alpaca.get_account().equity)

            self.shortAmount = self.currentEquity * self.short_position_ratio
            self.longAmount = self.currentEquity * self.long_position_ratio

            # Rebalancing portfolio on market open
            positions = self.alpaca.list_positions()
            
            for position in positions:
                if not (position.unrealized_plpc == position.unrealized_intraday_plpc):
                    self.do_init_reb = True
                    break
            
            if not self.do_init_reb:
                utils.write_log("Skipped Initial Rebalance")
                self.shortAmount = 0
                self.longAmount = 0

            d_reb = True

            # Monitor the portfolio every minute, making needed trades
            while True:
                clock = self.alpaca.get_clock()
                closingTime = clock.next_close.replace(tzinfo=datetime.timezone.utc).timestamp()
                currTime = clock.timestamp.replace(tzinfo=datetime.timezone.utc).timestamp()
                self.timeToClose = closingTime - currTime

                if(self.timeToClose < (60 * 5)):
                    # Go to next day
                    utils.write_log("Sleeping until market close (5 minutes).")
                    time.sleep(60 * 5)
                
                    self.opening = True
                    utils.write_log("Market Close: " + str(clock.timestamp).split()[0])
                    utils.p_sep()
                    self.var_init()
                    break

                utils.write_log("Time until market close: [" + utils.p_time(int((closingTime - currTime) / 60)) + "]")

                # Invest free cash
                if d_reb:
                    dtRebalance = threading.Thread(target=self.rebalance)
                    dtRebalance.start()
                    dtRebalance.join()

                    d_reb = False

                # Check our active positions with our predictions, and remove our participation if position violates our expectations
                # Check each position to see if it goes past our risk management values and liquidate & add to blacklist if so
                # Stop-loss and take-profit points?
                positions = self.alpaca.list_positions()

                if (self.timeToClose // 60) % 10 == 0:
                    s_all = 0
                    l_all = 0
                    for position in positions:
                        if position.side == "long":
                            l_all = l_all + float(position.market_value)
                        else:
                            s_all = s_all + float(position.market_value)
                    utils.write_log("Total Short Allocation: [" + str(s_all) + "]")
                    utils.write_log("Total Long Allocation: [" + str(l_all) + "]")
                        

                for position in positions:
                    m_p = 1
                    if position.side == "short":
                        m_p = -1
                    pctg_change = abs(float(position.unrealized_plpc)) * m_p

                    if (pctg_change > self.take_profit or pctg_change < -self.stop_loss) and self.do_stop_loss:
                        d_reb = True

                        # Time to exit the trade
                        p_message = "exceeded the take_profit point of " + str(self.take_profit * 100)
                        if pctg_change < self.stop_loss:
                            p_message = "plumeted to the stop_loss point of " + str(self.stop_loss * 100)
                        utils.write_log("Position " + str(position.symbol) + " has " + p_message + "%. Liquidating...")

                        respSendBOLong = []
                        tSendBOLong = threading.Thread(target=self.sendBatchOrder, args=[[position.symbol], [-m_p * int(float(position.qty))], respSendBOLong])
                        tSendBOLong.start()
                        tSendBOLong.join()

                        # respSendBOLong is a list of booleans on if the order succeeded, we dont need to use it tho
                        for failed_stock in respSendBOLong[0][1]:
                            # Take every incomplete order and contribute monies to its specific short / long pool
                            self.blacklist.add(failed_stock)

                        if position.symbol not in self.blacklist:
                            # Trade succeeded! Lets add our cash to the money pot now
                            if position.side == "short":
                                self.shortAmount = self.shortAmount + abs(float(position.market_value))
                            else:
                                self.longAmount = self.longAmount + abs(float(position.market_value))

                time.sleep(60)
        
    # Wait for market to open.
    def awaitMarketOpen(self):
        isOpen = self.alpaca.get_clock().is_open
        clock = self.alpaca.get_clock()
        closeTime = clock.timestamp.replace(tzinfo=datetime.timezone.utc).timestamp()

        sent_rep = False
        
        utils.write_log("Waiting for market to open...")   

        while(not isOpen):
            clock = self.alpaca.get_clock()
            openingTime = clock.next_open.replace(tzinfo=datetime.timezone.utc).timestamp()
            currTime = clock.timestamp.replace(tzinfo=datetime.timezone.utc).timestamp()
            timeToOpen = int((openingTime - currTime) / 60)
            timeSinceClose = int((currTime - closeTime) / 60)
            
            utils.write_log("Time until market opens: [" + utils.p_time(timeToOpen) + "]")
      
            # 4 hours
            if int(timeSinceClose / 60) >= 4 and not sent_rep:
                utils.write_log("Sending a report!")
                self.submitReport()
                sent_rep = True

            time.sleep(60)
            
            isOpen = self.alpaca.get_clock().is_open

            if isOpen:
                utils.print_header("lpLongShort.py") 
                
                # Do operations at 9:35 AM
                self.do_init_reb = True
                time.sleep(60 * 5)
        utils.write_log("Market opened.")

    # Update our profit margins stop-loss list on a new purchase
    def update_profits(self, stock, side):
        # Check to see if stock is already within our list
        stock_index = -1
        for i, position in enumerate(profit_margins):
            if position[0] == stock:
                stock_index = i
                break

        # Place / Update the stocks price in our list
        # list_item = [stock, low, high]
        list_item = [stock]
        stock_price = self.getStockPrice(stock)

        if side == "buy":
            list_item.append(stock_price * (1 - self.stop_loss))
            list_item.append(stock_price * (1 + self.take_profit))
        else:
            list_item.append(stock_price * (1 + self.stop_loss))
            list_item.append(stock_price * (1 - self.take_profit))

        if stock_index == -1:
            # Doesnt exist, we are now appending
            profit_margins.append(list_item)
        else:
            # Does exist, we need to set the index
            profit_margins[stock_index] = list_item
    
    # An improved rebalance algo
    def rebalance(self):
        if self.longAmount > 0 or self.shortAmount > 0:
            utils.write_log("Short Balance [" + str(self.shortAmount) + "]")
            utils.write_log("Long Balance [" + str(self.longAmount) + "]")
        
        tRerank = threading.Thread(target=self.rerank)
        tRerank.start()
        tRerank.join()
        
        # We have a list of stocks to long and to short
        # Clear existing orders
        orders = self.alpaca.list_orders(status="open")
        for order in orders:
            self.alpaca.cancel_order(order.id)

        # Handle currently invested stonks from yesterday
        positions = self.alpaca.list_positions()
        
        stock_list = [] # Stock name
        stock_change = [] # Stock change

        # Basically save our position changes in order to liquidate all our assets
        do_rebalance = False
        for position in positions:
            if not (position.unrealized_plpc == position.unrealized_intraday_plpc):
                do_rebalance = True
                break
        
        if do_rebalance:
            for position in positions:
                stock_list.append(position.symbol)
                if position.side == "long":
                    stock_change.append(-abs(int(float(position.qty))))
                else:
                    stock_change.append(abs(int(float(position.qty))))
        
        # Create a new list of how we want the new portfolio to look
        # Using self.shortAmount & self.longAmount
        stock_list_rb = []
        stock_change_rb = []

        short_prices = []
        long_prices = []

        # Get price numbers for shorts and longs
        for stock in self.short:
            short_prices.append(self.getStockPrice(stock))
            stock_list_rb.append(stock)
            stock_change_rb.append(0)
        for stock in self.long:
            long_prices.append(self.getStockPrice(stock))
            stock_list_rb.append(stock)
            stock_change_rb.append(0)
            

        while True:
            # Compile prices to find the current minimum price
            price_list = []
            for i, price in enumerate(short_prices):
                change_index = stock_list_rb.index(self.short[i])
                price_list.append(price * (abs(stock_change_rb[change_index]) + 1))
                
            min_index = 0
            for i, price in enumerate(price_list):
                if price < price_list[min_index] and price <= self.shortAmount:
                    min_index = i
                    
            if price_list[min_index] > self.shortAmount:
                break
            else:
                self.shortAmount = self.shortAmount - abs(short_prices[min_index])
                
                stock_list_index = stock_list_rb.index(self.short[min_index])
                stock_change_rb[stock_list_index] = stock_change_rb[stock_list_index] - 1
        
        while True:
            # Compile prices to find the current minimum price
            price_list = []
            for i, price in enumerate(long_prices):
                change_index = stock_list_rb.index(self.long[i])
                price_list.append(price * (abs(stock_change_rb[change_index]) + 1))
                
            min_index = 0
            for i, price in enumerate(price_list):
                if price < price_list[min_index] and price <= self.longAmount:
                    min_index = i
                    
            if price_list[min_index] > self.longAmount:
                break
            else:
                self.longAmount = self.longAmount - abs(long_prices[min_index])
                
                stock_list_index = stock_list_rb.index(self.long[min_index])
                stock_change_rb[stock_list_index] = stock_change_rb[stock_list_index] + 1
        
        for i in range(2):
            position_list_p = []
            
            for j, qty in enumerate(stock_change_rb):
                if (i * 2 - 1) * qty > 0:
                    position_list_p.append(stock_list_rb[j])
            
            if i == 0 and len(position_list_p) > 0:
                utils.write_log("We are taking a short position in: " + str(position_list_p))
            elif len(position_list_p) > 0:
                utils.write_log("We are taking a long position in: " + str(position_list_p))

        # Merge the 2 stock lists
        for i, stock in enumerate(stock_list_rb):
            if stock_list.count(stock) == 0:
                # Stock isnt in stock_list, we will add
                stock_list.append(stock)
                stock_change.append(stock_change_rb[i])
            else:
                # Stock is in our list, so we have to modify the stock at the index
                stock_index = stock_list.index(stock)
                stock_change[stock_index] = stock_change[stock_index] + stock_change_rb[i]

        # Remove stocks with a net change of 0
        t_stock_list = stock_list
        t_stock_change = stock_change
        stock_list = []
        stock_change = []
        for i, stock in enumerate(t_stock_list):
            if not (t_stock_change[i] == 0):
                stock_list.append(stock)
                stock_change.append(t_stock_change[i])

        # Stock list is complete, we can batch order lol
        respSendBOLong = []
        tSendBOLong = threading.Thread(target=self.sendBatchOrder, args=[stock_list, stock_change, respSendBOLong])
        tSendBOLong.start()
        tSendBOLong.join()

        # respSendBOLong is a list of booleans on if the order succeeded, we dont need to use it tho
        for failed_stock in respSendBOLong[0][1]:
            # Take every incomplete order and contribute monies to its specific short / long pool
            self.blacklist.add(failed_stock)
            stock_index = stock_list.index(failed_stock)
            order_change = stock_change[stock_index]

            if self.short.count(failed_stock) > 0:
                order_index = self.short.index(failed_stock)
                self.shortAmount = self.shortAmount + abs(order_change * short_prices[order_index])
            elif self.long.count(failed_stock) > 0:
                order_index = self.long.index(failed_stock)
                self.longAmount = self.longAmount + abs(order_change * long_prices[order_index])       
        
    # Re-rank all stocks to adjust longs and shorts.
    def rerank(self):
        # Rank all stocks from greatest to least on percentage change in the last 10 min
        tRank = threading.Thread(target=self.rank)
        tRank.start()
        tRank.join()
        
        self.long = []
        self.short = []

        for i, stockField in enumerate(self.allStocks):
            if(i < len(self.allStocks) // 4):
                self.short.append(stockField[0])
            elif(i > len(self.allStocks) // (4 / 3)):
                self.long.insert(0, stockField[0])
        
    # Mechanism used to rank the stocks, the basis of the Long-Short Equity Strategy.
    def rank(self):
        # Ranks all stocks by percent change over the past 10 minutes (higher is better).
        tGetPC = threading.Thread(target=self.getDailyPredictions)
        tGetPC.start()
        tGetPC.join()

        # Sort the stocks in place by the percent change field (marked by pc).
        self.allStocks.sort(key=lambda x: x[1])
        
    # Get percent changes of the stock prices over the past 10 minutes.
    def getDailyPredictions(self):
        length = int(self.percent_period)
        
        for i, stock in enumerate(self.allStocks):
            local_bars = self.get_bars(stock[0], length, 0)

            # Generate prediction
            local_perdiction = self.d_trend_line(local_bars)

            self.allStocks[i][1] = local_perdiction
    
    def submitReport(self):
        current_equity = float(self.alpaca.get_account().equity)

        positions = self.alpaca.list_positions()
        short_list = []
        long_list = []

        for position in positions:
            if position.side == "long":
                # Its a long
                long_list.append([position.symbol, int(position.qty), float(position.unrealized_plpc), float(position.unrealized_pl)])
            else:
                # Its a short
                short_list.append([position.symbol, int(position.qty), float(position.unrealized_plpc), float(position.unrealized_pl)])

        # [symbol, qty, pct_change, price_change_total]
        mailjet.day_report([current_equity, self.init_equity], short_list, long_list)
        self.init_equity = current_equity

    # Submit an order if quantity is above 0.
    def submitOrder(self, qty, stock, side, resp):
        my_acc = self.alpaca.get_account()
        
        pdt_qualified = False
        positions = self.alpaca.list_positions()
        for position in positions:
            if position.symbol == stock:
                if ((side == "buy" and position.side == "short") or (side == "sell" and position.side == "long")) and position.unrealized_plpc == position.unrealized_intraday_plpc:
                    pdt_qualified = True
                    self.pdt_counter = self.pdt_counter + 1
                else:
                    break

        # my_acc.daytrade_count
        if self.pdt_counter >= 2 and my_acc.daytrade_count >= 3 and not self.allow_liquidations:
            # ALMOST MARKED AS PDT, NONO
            utils.write_log("Pushing up against PDT restrictions | " + str(qty) + " " + stock + " " + side + " | not completed.")
            resp.append(True)
            return

        if(qty > 0):
            try:
                self.alpaca.submit_order(stock, qty, side, "market", "day")
                utils.write_log("Market order of | " + str(qty) + " " + stock + " " + side + " | completed.")
                resp.append(True)
            except:
                utils.write_log("Order of | " + str(qty) + " " + stock + " " + side + " | did not go through.")
                resp.append(False)
        else:
            utils.write_log("Quantity is 0, order of | " + str(qty) + " " + stock + " " + side + " | not completed.")
            resp.append(True)

    def getStockPrice(self, stock):
        try:
            bars = self.alpaca.get_bars(stock, TimeFrame.Minute,
                                            pd.Timestamp('now').date(),
                                            pd.Timestamp('now').date(), limit=1,
                                            adjustment='raw')
            return bars[0].c
        except Exception as err:
            utils.write_log("Unable to get price of " + stock)

    def getUsableEquity(self):
        return int(float(self.alpaca.get_account().equity) * self.equity_cash_ratio)

    # Submit a batch order that returns completed and uncompleted orders.
    def sendBatchOrder(self, stocks, qtys, resp):
        executed = []
        incomplete = []
        for i, stock in enumerate(stocks):
            if(self.blacklist.isdisjoint({stock})):
                if qtys[i] < 0:
                    side = "sell"
                else:
                    side = "buy"
                respSO = []
                tSubmitOrder = threading.Thread(target=self.submitOrder, args=[abs(qtys[i]), stock, side, respSO])
                tSubmitOrder.start()
                tSubmitOrder.join()
                if(not respSO[0]):
                    # Stock order did not go through, add it to incomplete.
                    incomplete.append(stock)
                else:
                    executed.append(stock)
                respSO.clear()
        resp.append([executed, incomplete])

    def get_bars(self, stock, period, hist_period):
        day = pd.Timestamp('now').date() - pd.Timedelta(days = (hist_period + 1))

        bars = self.alpaca.get_bars(stock, TimeFrame.Day,
                                    day - pd.Timedelta(days = 2 + period + 2 * int(period / 7 + 1)),
                                    day,
                                    adjustment='raw')

        bar_count = 0
        for bar in bars:
            bar_count = bar_count + 1
        bars = bars[bar_count - period:]
        
        return bars

    def d_trend_line(self, bars):
        # Similar to trend_line, but the trend starts on the interval with the best r_value
        # List of median values between day open and close
        med_values = []
        value_axis = []
        for bar_val in range(0, len(bars)):
            bar = bars[bar_val]
            # med_values.extend([bar.o, bar.c, bar.h, bar.l])
            # value_axis.extend([bar_val, bar_val, bar_val, bar_val])
            med_values.append((bar.c - bar.o) / 2 + bar.o)
            value_axis.append(bar_val)

        prime_value = [-1,-1, 0] # Start index, R-Value
        for bar in range(0, len(bars) - 2):
            # Essentially check list for slope and r_value and keep going through until we have the best r value
            slope, intercept, r_value, p_value, std_err = stats.linregress(value_axis[bar:], med_values[bar:])

            if r_value * r_value > prime_value[1] or prime_value[0] == -1:
                # slope = -slope

                # Slope as PCTG of previous day?
                slope = slope / bars[len(bars) - 1].c
                prime_value = [bar, r_value * r_value, slope]

        return prime_value[2]
