import os
import json

import alpaca_trade_api as tradeapi
from alpaca_trade_api.stream import Stream

def main():
    # Start running instance
    init_alpaca_environ()
    
    global api
    api = tradeapi.REST()

    # Es esso asi

    stream = Stream(
        os.environ["APCA_API_KEY_ID"],
        os.environ["APCA_API_SECRET_KEY"],
        base_url='https://paper-api.alpaca.markets',
        data_feed='iex')
    
    stream.subscribe_quotes(quote_callback, 'IBM')
    stream.run()

# Modify our API settings
def init_alpaca_environ():
    params = json.load(open("params.json"))
    if params["paper"] == "T":
        os.environ["APCA_API_BASE_URL"] = "https://paper-api.alpaca.markets"
    os.environ["APCA_API_KEY_ID"] = str(params["alpaca_public"])
    os.environ["APCA_API_SECRET_KEY"] = str(params["alpaca_private"])

# =-=-=-=-=-=-=-=-=-=-=
# The following functions are used to generate a
# confidence score in a certain stock symbol
# def scs(symbol):
    # This function generates a number from 0 to 1 of confidence
    # in a specific symbol
    
def price_earnings(symbol):
    # EPS = (Income - Dividends) / Outstanding Shares
    share_price = 1
    
async def trade_callback(t):
    print('trade', t)
    
async def quote_callback(q):
    print('quote', q)
    
# =-=-=-=-=-=-=-=-=-=-=

main()