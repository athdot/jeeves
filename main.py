from lib import *
import json
import os
import sys
import alpaca_trade_api as tradeapi
from utils import *
import glob

from datetime import date
from os.path import exists

abspath = os.path.abspath(__file__)
dname = os.path.dirname(abspath)
os.chdir(dname)

stockUniverse = ['DOMO', 'TLRY', 'SQ', 'MRO', 'AAPL', 'GM', 'SNAP', 'SHOP',
                 'SPLK', 'BA', 'AMZN', 'SUI', 'SUN', 'TSLA', 'CGC', 'SPWR',
                 'NIO', 'CAT', 'MSFT', 'PANW', 'OKTA', 'TWTR', 'TM',
                 'ATVI', 'GS', 'BAC', 'MS', 'TWLO', 'QCOM', 'GLD', ]

# Algorithm name, no .py
algorithm = "testBed"

def main():
    # Set our global python variables for all of our child scripts
    init_alpaca_environ()
    print_header(algorithm + ".py") 
    
    # Run investment strategy
    algo = eval(algorithm).TradeAlgo()
    algo.run()

# Modify our API settings
def init_alpaca_environ():
    try:
        params = json.load(open("params.json"))
    except FileNotFoundError:
        utils.p_sep()
        utils.p_error("Error: params.json does not exist!")
        utils.p_error("Exiting...")
        utils.p_sep()
        sys.exit()
    os.environ["APCA_API_BASE_URL"] = str(params["alpaca_url"])
    os.environ["APCA_API_KEY_ID"] = str(params["alpaca_public"])
    os.environ["APCA_API_SECRET_KEY"] = str(params["alpaca_private"])
    
    version = open("README.md", 'r')
    version = version.readline()[9:]
    os.environ["JEEVES_VERSION"] = str(version)
    
    # Turn our stock list into an os variable
    os.environ["STOCK_UNIVERSE"] = ','.join(stockUniverse)
    
def existant_algo(name):
    return exists("lib/" + name + ".py")

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

if existant_algo(algorithm):
    main()
else:
    utils.p_sep()
    utils.p_error("ERROR: MISSING DEPENDANCY")
    utils.p_error("> 'lib/" + algorithm + ".py' DOES NOT EXIST")
    utils.p_error("> Please use an existant algorithm and rerun".upper())
    utils.p_error(" ")
    utils.p_error("EXISTING ALGORITHMS:")
    
    files = glob.glob("lib/*.py")
    for file in files:
        if file != "lib/__init__.py":
            utils.p_error("> " + str(file))
    
    utils.p_sep()