from lib import longShort
import json
import os
import alpaca_trade_api as tradeapi

def main():
    # Set our global python variables for all of our child scripts
    init_alpaca_environ()
    print_header("longShort.py")
    
    # Run investment strategy
    ls = longShort.LongShort()
    ls.run()

# Modify our API settings
def init_alpaca_environ():
    params = json.load(open("params.json"))
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
    
    print("=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=\n")
    
    print("JEEVES")
    
    print(os.environ["JEEVES_VERSION"])
    
    print("Automated Trading and Portfolio Management Script for the Raspberry PI")
    print("© 2022, Charles Graham. All rights reserved.")
    
    total_equity = float(alpaca.get_account().equity)
    
    print("\nFree Equity: $" + str(total_equity))
    print("Algorithm: " + str(strat))
    
    print("\n=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=")

main()