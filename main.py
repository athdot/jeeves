from lib import longShort
import json
import os
import sys
import alpaca_trade_api as tradeapi
import utils
from datetime import date

def main():
    # Set our global python variables for all of our child scripts
    init_alpaca_environ()
    print_header("longShort.py")
    
    # Run investment strategy
    ls = longShort.LongShort()
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