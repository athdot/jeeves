# Jeeves v1.4.1 - "Pisspot"
Python Auto-Trader with Alpaca API

Compatable trading algorithms and scripts are stored in our lib/ folder

### Recent Version Notes
- Addition of candlestick analysis functionality beta
- Adding of test toolkit tools to test effectiveness and functionality

### Algorithm Creation

To create a new algorithm, you must do 3 things
- Create a new .py file of the name you choose, with a class named "TradeAlgo"
- Add a .run() function to be invocated
- Place function into the lib/ folder

#### Variables of Note
- os.environ["APCA_API_BASE_URL"]
- os.environ["APCA_API_KEY_ID"]
- os.environ["APCA_API_SECRET_KEY"]
- os.environ["STOCK_UNIVERSE"]

### Other Requirements

In order to execute our algorithms, an accout with Alpaca Algorithmic Traders is needed. Please create a file named ```params.json``` within the project base directory. This file must appear as follows:

```
{
    "alpaca_public":"XXXXXXXXXXXXXXXX",
    "alpaca_private":"XXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX",
    "alpaca_url":"https://paper-api.alpaca.markets"
}
```
Inclusion of this file will allow each script to connect and interact with your Alpaca account, in order to recieve market data and total account equity, but also complete market_orders and manage portfolio standings.

### License
© 2022, Charles Graham. All rights reserved.
