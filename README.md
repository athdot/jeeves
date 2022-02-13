# Jeeves v1.3.1 - "Smith"
Python Auto-Trader with Alpaca API

Compatable trading algorithms and scripts are stored in our lib/ folder

### Algorithm Creation

To create a new algorithm, you must do 3 things
- Create a new .py file of the name you choose, with a class named "TradeAlgo"
- Add a .run() function to be invocated
- Place function into the lib/ folder

Variables of Note:
- os.environ["APCA_API_BASE_URL"]
- os.environ["APCA_API_KEY_ID"]
- os.environ["APCA_API_SECRET_KEY"]
- os.environ["STOCK_UNIVERSE"]

© 2022, Charles Graham. All rights reserved.
