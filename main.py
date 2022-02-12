from lib import *
import json
import os
import sys
import alpaca_trade_api as tradeapi
import utils
from datetime import date

stockUniverse = ['DOMO', 'TLRY', 'SQ', 'MRO', 'AAPL', 'GM', 'SNAP', 'SHOP',
                 'SPLK', 'BA', 'AMZN', 'SUI', 'SUN', 'TSLA', 'CGC', 'SPWR',
                 'NIO', 'CAT', 'MSFT', 'PANW', 'OKTA', 'TWTR', 'TM',
                 'ATVI', 'GS', 'BAC', 'MS', 'TWLO', 'QCOM', 'GLD', ]

def main():
    # Set our global python variables for all of our child scripts
    algorithm = "longShort"
    
    init_alpaca_environ()
    print_header(algorithm + ".py") 
    
    # Run investment strategy
    ls = eval(algorithm).TradeAlgo()
    ls.run()

# Modify our API settings
def init_alpaca_environ():
    try:
      params = json.load(open("params.json"))
    except FileNotFoundError:
      print("Error: params.json does not exist!")
      print("Exiting...")
      sys.exit()
    os.environ["APCA_API_BASE_URL"] = str(params["alpaca_url"])
    os.environ["APCA_API_KEY_ID"] = str(params["alpaca_public"])
    os.environ["APCA_API_SECRET_KEY"] = str(params["alpaca_private"])
    
    version = open("README.md", 'r')
    version = version.readline()[9:]
    os.environ["JEEVES_VERSION"] = str(version)
    
    # Turn our stock list into an os variable
    os.environ["STOCK_UNIVERSE"] = ','.join(stockUniverse)

def print_header(strat):
    alpaca = tradeapi.REST(os.environ["APCA_API_KEY_ID"],
                           os.environ["APCA_API_SECRET_KEY"],
                           os.environ["APCA_API_BASE_URL"],
                           'v2')
    
    utils.p_sep()
    
    print("\nJEEVES")
    
    print(os.environ["JEEVES_VERSION"])
    
    print("Automated Trading and Portfolio Management Script for the Raspberry PI")
    print("© " + str(date.today().year) + ", Charles Graham. All rights reserved.")
    
    total_equity = float(alpaca.get_account().equity)
    
    print("\nFree Equity: $" + str(total_equity))
    print("Algorithm: " + str(strat) + "\n")
    
    utils.p_sep()

main()