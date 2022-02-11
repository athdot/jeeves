from lib import longShort
import json
import os

def main():
    # Set our global python variables for all of our child scripts
    init_alpaca_environ()
    
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
    version.readline()
    version.readline()
    os.environ["JEEVES_VERSION"] = str(version.readline())
    
main()