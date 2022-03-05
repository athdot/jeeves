import matplotlib.pyplot as plt
import matplotlib.dates as mdates

from datetime import datetime
from datetime import timedelta

import base64
import os

def gen_plot(y1, time_scale):
    market_open = datetime.now().replace(hour=7, minute=0, second=0)

    # x1 = [market_open + timedelta(minutes=i * time_scale) for i in range(int(11 * (60 / time_scale)))]
    # y1 = [i+random.gauss(0,1) for i,_ in enumerate(x1)]

    x1 = [market_open + timedelta(minutes=i * time_scale) for i in range(len(data))]

    dtFormat = mdates.DateFormatter('%H:%M')

    plt.figure(figsize=(8,5), dpi=120)

    plt.plot(x1, y1, color = "darkgoldenrod", label = "Equity")

    plt.xlabel("Time (hrs)")
    plt.ylabel("Value (Dollars)")
    plt.title("Portfolio Performance")

    # plt.gcf().autofmt_xdate()
    plt.gca().xaxis.set_major_formatter(dtFormat)
    plt.gca().yaxis.set_major_formatter('${x:1.2f}')

    plt.legend()

    plt.savefig('utils/mailjet/temp_equity.png')

    with open('utils/mailjet/temp_equity.png', 'rb') as img_file:
        b_string = base64.b64encode(img_file.read())
    
    os.remove('utils/mailjet/temp_equity.png')

    b_string = str(b_string)[2:]
    b_string = b_string[:len(b_string) - 1]

    return b_string