from datetime import date
from mailjet_rest import Client
import os
import alpaca_trade_api as tradeapi
from utils import charts
import base64

email_html = "utils/mailjet/email.html"

def day_report(equity_list, short_list, long_list):
    # Equity List Structure
    # [5242.23,5000.00]
    #
    # Short & Long List Structure
    # [
    #   ['AAPL',2,1.5,24],
    #   [symbol, qty, pct, price_difference]
    # ]

    # Variable management
    today = date.today()
    t_date = today.strftime("%m/%d/%y")
    t_year = today.strftime("%Y")

    p_change = round((equity_list[0] / equity_list[1] - 1) * 100, 2)
    c_change = "green"

    if p_change < 0:
        c_change = "red"
        p_change = str(p_change) + "%"
    else:
        p_change = "+" + str(p_change) + "%"

    #open text file in read mode
    email_data = open(email_html, "r")
    data = email_data.read()
    email_data.close()

    # data is our html file
    data = data.replace("{current_eq}", "$" + "{0:.2f}".format(equity_list[0]))
    data = data.replace("{past_eq}", "$" + "{0:.2f}".format(equity_list[1]))
    data = data.replace("{eq_pct_change}", "<p style='display: inline; color: " + c_change + ";'>" + p_change + "</p>")
    data = data.replace("{date}", t_date)
    data = data.replace("{year}", t_year)

    # Parse the long and short data
    up1 = 0
    up2 = 0
    down1 = 0
    down2 = 0

    p_change_2 = 0

    d_insert = ""
    for short in short_list:
        p_change_2 = p_change_2 + short[2]
        if short[3] < 0:
            down1 = down1 + 1
            down2 = down2 + short[3]
            d_insert += gen_tb("", "red", short[0], short[1], str(round(short[2] * 100, 2)) + "%")
        else:
            up1 = up1 + 1
            up2 = up2 + short[3]
            d_insert += gen_tb("", "green", short[0], short[1], "+" + str(round(short[2] * 100, 2)) + "%")
    data = data.replace("{short_list}", d_insert)

    d_insert = ""
    for long_var in long_list:
        p_change_2 = p_change_2 + long_var[2]
        if long_var[3] < 0:
            down1 = down1 + 1
            down2 = down2 + long_var[3]
            d_insert += gen_tb("", "red", long_var[0], long_var[1], str(round(long_var[2] * 100, 2)) + "%")
        else:
            up1 = up1 + 1
            up2 = up2 + long_var[3]
            d_insert += gen_tb("", "green", long_var[0], long_var[1], "+" + str(round(long_var[2] * 100, 2)) + "%")
    data = data.replace("{long_list}", d_insert)

    d_insert = gen_tb("green", "", "Up", up1, "+$" + "{0:.2f}".format(up2))
    d_insert += gen_tb("red", "", "Down", down1, "-$" + "{0:.2f}".format(-down2))

    if up2 + down2 < 0:
        d_insert += gen_tb("", "red", "Total", up1 + down1, "-$" + "{0:.2f}".format(-(up2 + down2)))
    else:
        d_insert += gen_tb("", "green", "Total", up1 + down1, "+$" + "{0:.2f}".format(up2 + down2))

    data = data.replace("{portfolio_summary}", d_insert)

    d_insert = p_change_2 * 100 / (up1 + down1)
    if d_insert < 0:
        data = data.replace("{overall_change}", str(round(d_insert, 2)) + "%")
    else:
        data = data.replace("{overall_change}", "+" + str(round(d_insert, 2)) + "%")

    stock_list_org = []

    for stock in long_list:
        stock_list_org.append([stock[0], stock[2]])
    for stock in short_list:
        stock_list_org.append([stock[0], stock[2]])

    stock_list_org.sort(key=lambda x: x[1])
    stock_list_org.reverse()

    max = 5
    if max > len(stock_list_org):
        max = len(stock_list_org)

    d_insert = ""
    for i in range(0, max):
        symbol = stock_list_org[i][0]
        qty = 0
        pct = 0

        for stock in short_list:
            if stock[0] == symbol:
                qty = stock[1]
                pct = stock[2]
        for stock in long_list:
            if stock[0] == symbol:
                qty = stock[1]
                pct = stock[2]

        if pct < 0:
            d_insert += gen_tb("", "red", symbol, qty, str(round(pct * 100, 2)) + "%")
        else:
            d_insert += gen_tb("", "green", symbol, qty, "+" + str(round(pct * 100, 2)) + "%")

    data = data.replace("{top_five}", d_insert)    

    d_insert = ""
    for i in range(len(stock_list_org) - max, len(stock_list_org)):
        symbol = stock_list_org[i][0]
        qty = 0
        pct = 0

        for stock in short_list:
            if stock[0] == symbol:
                qty = stock[1]
                pct = stock[2]
        for stock in long_list:
            if stock[0] == symbol:
                qty = stock[1]
                pct = stock[2]

        if pct < 0:
            d_insert += gen_tb("", "red", symbol, qty, str(round(pct * 100, 2)) + "%")
        else:
            d_insert += gen_tb("", "green", symbol, qty, "+" + str(round(pct * 100, 2)) + "%")

    data = data.replace("{bottom_five}", d_insert)  

    stock_list_org = []

    for stock in long_list:
        stock_list_org.append([stock[0], stock[3]])
    for stock in short_list:
        stock_list_org.append([stock[0], stock[3]])

    stock_list_org.sort(key=lambda x: x[1])
    stock_list_org.reverse()

    d_insert = ""
    for i in range(0, max):
        symbol = stock_list_org[i][0]
        qty = 0
        pct = 0

        for stock in short_list:
            if stock[0] == symbol:
                qty = stock[1]
                pct = stock[3]
        for stock in long_list:
            if stock[0] == symbol:
                qty = stock[1]
                pct = stock[3]

        if pct < 0:
            d_insert += gen_tb("", "red", symbol, qty, "-$" + "{0:.2f}".format(round(-pct, 2)))
        else:
            d_insert += gen_tb("", "green", symbol, qty, "+$" + "{0:.2f}".format(round(pct, 2)))

    data = data.replace("{real_top_five}", d_insert)    

    d_insert = ""
    for i in range(len(stock_list_org) - max, len(stock_list_org)):
        symbol = stock_list_org[i][0]
        qty = 0
        pct = 0

        for stock in short_list:
            if stock[0] == symbol:
                qty = stock[1]
                pct = stock[3]
        for stock in long_list:
            if stock[0] == symbol:
                qty = stock[1]
                pct = stock[3]

        if pct < 0:
            d_insert += gen_tb("", "red", symbol, qty, "-$" + "{0:.2f}".format(round(-pct, 2)))
        else:
            d_insert += gen_tb("", "green", symbol, qty, "-$" + "{0:.2f}".format(round(pct, 2)))

    data = data.replace("{real_bottom_five}", d_insert)  

    # Handle portfolio data
    alpaca = tradeapi.REST(os.environ["APCA_API_KEY_ID"],
                                os.environ["APCA_API_SECRET_KEY"],
                                os.environ["APCA_API_BASE_URL"],
                                'v2')

    hist = alpaca.get_portfolio_history(period='1D', extended_hours=True, timeframe='5Min')
    hist = [i for i in hist.equity if i]

    eq_change_pic = charts.gen_plot(hist, 5)

    mailjet_send(data, t_date, eq_change_pic)

def mailjet_send(html_text, d_t, cid1):
    api_key = os.environ['MAILJET_API_KEY_ID']
    api_secret = os.environ['MAILJET_API_SECRET_KEY']
    sender = os.environ["MAILJET_API_SENDER"]
    reciever = os.environ["MAILJET_API_RECIEVER"]

    log_file = ""

    try:
        log_file = open("log_file.txt", "r").read()
    except:
        log_file = ""
    encoded_log = base64.b64encode(log_file.encode("utf-8")).decode("utf-8")

    mailjet = Client(auth=(api_key, api_secret), version='v3.1')
    data = {
        'Messages': [
				{
						"From": {
								"Email": sender,
								"Name": "RPi Bot - Jeeves"
						},
						"To": [
								{
										"Email": reciever,
										"Name": "Charles"
								}
						],
						"Subject": "RPi Daily Report - " + d_t,
						"TextPart": "Daily Report from RPi",
						"HTMLPart": html_text,
						"Attachments": [
								{
										"ContentType": "text/plain",
										"Filename": "log_file.txt",
										"Base64Content": encoded_log
								}
						],
						"InlinedAttachments": [
								{
										"ContentType": "image/png",
										"Filename": "logo.png",
										"ContentID": "id1",
										"Base64Content": "iVBORw0KGgoAAAANSUhEUgAAAMgAAAD8CAMAAAAFbRsXAAAA8FBMVEX///8AAAC8EUJ1qSjBEUTEEkV3rCl5rynFEkW6EUF6sSqpDzuxED54CyquED2RDTOgDjiYDjVwCidZCB+LDDHx8fFzpic8BRViCSKjDzlTBx0gAwtnCSSWlpbp6ene3t7Ly8tRUVFXfh4VHgdQcxtkkSK+vr40BRJEYhdjjyKzs7NMbhpdhyBqamo1NTXQ0NCkpKQrBA8lAw11dXUcHBwySRE9WBVqmiQlNg1IBhkPAQWQkJBwcHA7OzuAgIAsQA8aJgkSGgYaAgleXl4MEQQ6VBQhMAsoKCgWFhYvRBAFCAEaJQlHR0c2NjYUHAYNAATvfuJ+AAAY40lEQVR4nO1daVsayRa2oRcRUEFEJRqRYATRuCQGl4lGo2ad8f//m9tLLaf2U41O5j5P3g93cqW7uk7V2c/p6rm5P/iD/xBWV1dfZNiXGFSD/tbhzvvj13PbX4Ig+Hp19KyDr159Skf9dLw6t7p/vXO41X/W0SH2A4Iv9B9f9/vXX379lZI2C95eH76/OtqigwZ/0X8cP9PEGVav3gXBu53AjJ3t0mO/twz761O2Rc9Gx1vLo/gyfvrw63Dfh8e3jw93dt7/cA/9rfQqUbx+e3z9fmvL/SiOLTQZOx6jHm+9v956W1YT9H0exbCDGxy1yzIOy2iX1S/asc5G5+Rfk4+Gp6EWyTDV4Xfyj/PRG93vf3lSsb392rQqBwvVwU3+r2m3eOr5o/Sw6+sr1wPk5SFrszAs/u8gXjAs0wc8f23/pRvg52B0U8jlMI6TafaYs2RhfJ/9pTpRLv9qVshHysW303z+N90kzslJ/5sQ0oI3D5+lkbeurlDScqVfieAxTpJpvvPVajVOumcpIdW4mj1wunCQXfFDWMS3hvEF1fFACBhlC5Sk4wbBqJr9d5z/MBl3F9RFyrDjtFzH4g1vzlMUa/KQzjslYHBTzZGMp/l/JsFtXI2n2W5VR/DWfe34h/CSfCeycXeDYJxkC3QwTfLRp8HNQboxcaKnI4VLJYtXD5MMcXc6PAs+F4+Ii/+k/yAEDcfpv+JpymSJ+FidIdsR6EgGOR3ZckyL4WIyapxSkY8eZHI/mHZTTIV1Cux0yNpkl46fdKdVPYpnx9NUeFKq7HvyCfx6201vvL1JBAKUwQeDbrqScf4E0Xbqd5xiP5Bgmr76yHxNszVO50hu7kuj/yJ/zzTrfUZHddp1DUspTFdKhF3NF3bqfjAZ5ZhMDgxLZULOXVNqa0TtQi3TIOORqefA8XgwnKTTmgwHB/nWfLISsl08arSQMlO2paYtN2NhFLyJq0RnvoNjU301yZScLx3Z3hAsFKr5i5WQuW+CbJRB8pBami6Z9DUfmdqPj0k1+Wdcfvx4UIzj8OqI+v1c/kG5OssUag7uHZE/nMf0mrIgAzksCTXrw1keVSWykuIrHfiaDOySbuzA72xUAPX7ZkZCqsmNwAFE+AJf5aGCztAeb+0w7TbrE5m6FAY+W5iRjJhbKish7KrMk5oNlAfyLaGS7s1Y8nIm3NXuW+hYLS65ubk5P5OG6E59dXH8hq8c2ZCh3+qkbvaBbJE/3tycfXfzVvG8x4XUiMijdoej3cSHlPigGG2fSYiX4KVe0fDjgfLnzLzdQunT42vxxJFu5eLu5HHS9aBloWCDX0xlechdkhycn4+1D6OxitXZol68/pFxPAm+H8RY/qBb8ppsNNo4pSw1Ch53F7TXMxfbbkjIlphciKSb+kkj7LYsFDywT0R9gLsrqQ7Og88HejJIzBU4cwOrH4rL/jHpl6SbBoJnOGmJi8U73MKrrFQyJj+Cnwem8bkT7Ap36XWPxpkm01RrPA4wOow89V3+vw9uliTZgKFx7Lh7j1C+GXj25Nw40Tg5SDXrrflxDMl5wOEU9XhhN1OsD10zxd2fdDRXJrBQlD8yj//GPF5chIITl/MXw9jXwVlxspt5NY+7lo2LMz1YCN61gxBiEocHQ1WFQ2RpFDcpVG/lvGrlLEJGajLtA44H0wmKkDki7FOnNCcH2dLc2xmsywn5aCOEkHFm4SpCSTLGsRbNa71xq5i4miey3gxsNN8zQibmq5JunuC6P0CoA6q1nGlgwls2CeET2M3dKQtbx9zHM1qRmOTDPnYxKp04cF9ddPBECsbjjuMiu2hkCaC2DITEC4MizTPGOAxsYfpuQpibgnLkkyKlkTKO3qnhO6KPOZNpccV3TPQbs+FQZRhmSmRPXj84ycnf6leUC7vOEaVcFQwwAVfcpXQ4VVaObfZshMRXqyy9+KDyOMyqnauEFIov/WmK8kP5YO9RhJAdGY2GY1xAl0yL+fwYyPOxGsS4S/zxETZi2x0ORx6EkNzWPT70iKuk0PRd2pTkJyBEEpIFaiwV8s3PWSBZJmShl5ZIPLKBLEgQTAHNpRW4h8PF1Yfir//4PIXSji3zBrpZOZ5Bw4QHqH4CAUDckzGxlGceiQCW60cWXEF1bIKnJJ4SU3XP1Fd8LhLCFyYZlXhA/EDHwTdaHNFA8QZlbYsHVW/oyhdZ0fh7IKOgJO5SCvHikWoUVkz0KVJzFYyMT/MJ0iLieUo+tXQiMrvJOP2HzWOXwcpVljqrBqvs0efoUg8Q+XSKYp2M4efuAv3lM363q/Eu216cMWQg0WlXzW9ZKWHxx31gAv3l3CvfFydJXJgdzx4bki9AuUCQkrF+9iq++1asqH/i2WFDeevWh4+rmlKfAb6p5YSapF9+dICC+8hvU5gatgKRURHIoN6Mn8oqwEr799YQUEMJYj+8qgsxcNmcXS4a8PagR1PaT/vYXd3URfz0ICSOh1xzOCqgBoB2jlt8/jkx9PUIwDtYMexB8FS9HEVK5f7nzdCjQoOgw55SEdEd3jwWYvepX5YOIif3wwTPCiZLKAG/MPECteoztDbS2uj9sIpdwq5x7gKw6jfO8/8FytMBiqP3yBJPovOwdMD4i3EaSTGXt5TCYlgFj74ZdJ3Ky9TBp4FT3lMqhMbGWeiA2fl8XxzKCykgKErE8HImCSkAO6XP7I9GaV4OR0ouhqsyexNzGptsEdN4O4wTi8uaTOWI0IWJRexSd7c7RFdDsGCm8Xwyzjva1AnEml5TJx51Jbysw6o6HXxkVOw/41sR8Ok/H0YHu6IdiJPq0ByB2HAzlhXIdDx5+Ay7/tCpBgyUDvBRDBdw7CccArLaPdgX1vHL8AzSASB1+p/l3XVZ2FYdD5VHe9MyOujGRcNeHMeSJXrul0jefgODf5zu7o4PBsPRmdQnXR63Nx+Hg4PdDILOePaXYebm9r98Nc3CjL1eM0V7Za8ceeVfsLHi2P1kiItOvRYSRLWNti8xh29ne+XJBKUn2Iq9TkpEBSIM620/Sq5f4iW47V/uB3OsLUciFYSWSvPSi5TnlxAvrtpbntdQQbal6UXJu+flrtUdZa4rzU6rnqHVaa6cCL81Q91uMFJqK9JYl6d7e3snp4a9svfA+2H7mzD0SbtVizIJJmschvNr/NfTuo2MDFGLX91bWmzUogxhrVHvtC9USkoH6gqEVxgu2/VQWfHwlM+s4qIjvbzBFNiGcHWm3Vryhvnn5AyA7slTRzfPkC9xO3KSkd9BZ9tUhgvDWkdkVUx3AAJwPwzcH96xC3B0pOy1Se6o6caLOncCJR+egQ5eKQnWGnquidbpFetYOtKbyJ70tLfIys3+jgUGIGg3cU3YoVecuMUD3EbkpKO/KawL/FUuxQjAXyZaMtFRZ5ds+BBSaZC7DFourAhSP1MOhb9jEATLpkk2nhjr4RkrnylxWC4bhgsiwaPpz0LHkZuOyit2jaqB7KBbcmK6IBIEZRZCPtBBWsY5ApfWwO1GhNSMrplunId74vueLgALC83WAbrmvjvCjEnQM1IC5aR0DoJpLOOKCXT4ykgl7AVOSkKguxwv8ZjBJH3RNJW1QICf1hImuWJahEUwvun9X+yGmFimJod8e36ENOC9JkqgZSzpqlAJuTQ8oXYayNj0YS7uEFi5K+RqseSW2DckXHwKVKB9rXSAZeneC8N1S/ySUrk65vTq3Dpoz8tREi4q9+4ZrgSiVCZepG8kbuo2BMZGIjDxSDa7Dc2GntS0gX6HX1EmmU3v3dDR0VFnQXFncsoQA9wtaleBX1BCA1Pv5JUmjxDZEwgXdW0KhS/xfH3NdK/OFYqAVfTnLaqzNJwFDJkBay0zKWHU0gTmDB11P6G4+6ciaBpL8bLCxol2BiJeaUP7FPWm43aNO1Tjv6JOXRFAEyeyzlK0ppmWXmejFkYkZRpFtcZyZ+WV+z7VoETc8noLCS2C3knrYxNzHU7Xeivr6yu9i7U9dI5xTVZe4Sb/0ZcQKuvy8jjFwwN3F+ub7fbm+oXsIjxtiMsHFbBvep6mSAVZDxdVr4TgUmfnbVjpsEx9KkuttpSsFCkB7OzrpVBCoH+iZavLXrNVz1OF0WKradNHABdLkiZIhai+KVwh2FXgXvqmtan25VGflAzIcdfeiMCU0umELTfz9fR2JqxB83QJcxIh/7uvbaexyBIdLmqJObMUJx1Nvi6Mak07m5ndsbAGHWLADIAQ30ww9bSIGVFT6MGTjgxysdFwB+a0UrFcy0A/rzGHJeRLg3zjgoE2buSEhGFHWWSrc2ix/RrLLdwp6EWaouU5WW9CKGulhKQ+hWqMHfOJTFLvdvMjKPSvWrmrB7L9voRQrdWr1ZuKcBizg05KLoylLI55wSW9WM7qL5whfDOO18ocAO4M2WwBOmfEEDXLiyDWTPeaHfAHzyBxO7DgEkOHNoRcQgVdgt+uwM9t1B8JSIChQ0x/EFygI3qbh+wjJdrz9CjM6VOJEmU2dSwdpoxAAXSJ4fUH2zDI4ppQkCugr+loEVlbC5DtdKbDIAuc4pNwkZTAM2f0NbAHLphA0dGp4TEbGKL6LUGWZbFPw+07Oloc1r1mI9za9kqoSszVa0rmzOU8wv1Y31Bq3qc+cxEiu3Qvve6FSaDMQUudFTHFat8TIB939agSzktC58XmQkAUBL7VExD9FDnlSGRVW4gF2pV7hb8WCTEh3hCQycxwL/QUSQYkbAizsegurnepcxcKUSHaENC5AI9Lm3q13swsKtDbMED4ZqSDN12DoGGmRQWc6VthBAEuvBVSYrLxXECATwQXFWvT+c2dGW7mHrRQMYP+Qt/BWDDYgIvqPRUo7b5KCyyD8FehzqWlg9VwhboTWFQvG6I8VZfVd4CUUMSKnuD56KwJr+GackpIJxwCZG1LEFIp9JYkmkIIqWnfZEcvSx0VfFFNrRY4QvxZqxIVkr0iLyCw8ZqkCv1JLhmyuXj5SgSAtUrsJ/EMZMUt+HDKllAfS2lVYoR4K98UwPXz7YuoMEuiOGkhcKsVT4W2i6sLR29RdhgxE7B2JVQFUTSKKYXDynUGGqRresdoOcDPey2eCMLdU/8NNREi1N6lDhUq6hr7e2n+yTkTmG3TlrkxhKh7CRdIEnfKWZrhghkIgXGev7ST+Wp4GigRkbeoEdF0hDBhLyGtghX2CNlFQjTNHTCKFgq9tM1Bs2qMEG/3Vc4IefNWWIRSGnUJHSchfqciohmNraqxp8qIeTH74L2lZN017WLQTxGEZKf424lm95kp8GxiSiFlp155D1DomVeaX4DLIKS5iKxrdD2g3XcaSubTV11smB8cgRoxJOSbcfOB9+vr9gminuHJT0qYiGmcPBgmaZSWRtaBWHnyuCYV7dFyXgGeiMbfDMHgIHanSQdNFAfu8Gu+1LZIeIWJTMQ0LAkzTUcqIRrmCUGQbGzS1EJTH/KSMz5XjXMECemrhGiyJDCj4+NtGWocxm5SFVwxaRS/gxDNjggSi6dDScVToJkLCKdGb4cg7aghRJUqcUJ4cQ9N2fQnbJwJV1AzPnBHNTKiLpfoZTxh6ZgX87QQ5rZucQRYTVUXGDpbMONI/qSqB6lijtSfoa0Z6gJDiTiCygnz4FeNZVf9QnhDvjaoWdib0xBusFR7U6UdNttCQkjxU7UUcnfuJcI4u4o0CO5qSLpbLs/DYFd4/4om55ToWOERN2MYFRbHib4tlkHpVpftAlRaQgaYxiOytIeqNXBZAkcvLYGxI6eibf+UhQT6jEI8Qp0tJYWk6ViydvKHNbV340nXXmd4vzqbZF29XOZ5yLximaQ4BTC4DM03MPTMqyk12V20lxYLoao1Ws2e2J55sTyvMXTzda1LIIomfNFBetmSConIW6G+3L1neFs92oDVi5VWCBv+iqZfQYhPmo1IuCKqdAytXqJhAGGVXCSheS0xPjba571ORTk/oNIBRuqpWdMRG0YtcaZ7m0sbtUre+1Vfapsb1gTeEta3LxJCeUvUDzY9utJp0O7kdCUbHYEj2sa2NG331+WJ1lWGgJ433BDlNV7WoAWLPGZHI8fpxXo7O2OjtyaqS9NLvXTvPI9+yAE8b6HqrfZv0V+A7a5pBkTA6VpG6LZ0DtDqJVh99fUFmhHi1QPP4xkoEI562ED0yEtgyyN0HWnesmQVK2Ynym2Is0uwGBvzyoMI4v8LBSttrZ3VEEkKInJIyCx0lKGkUFxip46+QM2OqMg9IYTLpAE+u6Aki7STb3eWlppEK2esIjnW+hNgeJ091TqRtYnNBHRXGsJHzg67KfQ7fZWpV6+JdJjatlgH4F1ro5Sge2VV7V1ywUkLmFx9KsPccWrtAUQAKyBkT4wvcQRZ04IwlpYRzUcL6bpkV5Ya89F8Y7npPozJL5Fok0LFpOqMaN9Ih6afscdcpjBadLGbbwEkNPlWmgSaagvsnWdSB7YYXof2Nyq8q6WmLdG90KC4S45GZnFL7pThapuBEf6dEVopedJLmqzkHI2mq8LFmuxxtGHyLnwPGKjonaBT0zEykgV19f7C88C0+bjQ5BOXqPrKNa0UeyZBk8XdQYfwWXNDs4LUJElRoudG5S3Dq+AZRN5y9vrD78CbKuNhXRMH+VcIK6oIW+iQuojdvdjgYmM9JNS4fP5F34oiJMajXjJEgrJ2n7PHPwUvp1QglIMryvQTVKTOYHsaUwgMEe/s8l5sexuMTEkZWZek3Z5/FHYP8YYSV8AOfSpxl38XaYYafgTBfGJevNihFzs6zSQ5KdHql4EP4AwBABuiTkhhvOWycKJHWqLVrwKz/e4QAOhf1LtvjLf2HISIqfpZZcRdMgbyhHulh74p5ux5E8Id/+ahClwLhMfJCUEeSUdrDDb1S+YBDCOyNigN0EY/C8oI9l1wer3T6RBSAWUIYUYOwZhAa2FPnaVBibuLBjJXGf1L9cUrhOfM2RD9TiXlLcQyAc1VQkhYkgqjKbhlR58yQEN3RKsu9Bv8CaEvVtxhbuXvMePPfSA3YJrIwZb4K2BqRVB+Gvd+8efu0OgK0Q4EpMRld9Sp0e1EhTLMHnqcbEqlHbNSQHH5Gne6m6hGWu4zerw/TVMQGNsAsvye7zOwzUTpO9594nMQEr0HwVvQu/aKSZhdwLXqcLvuczTVF4+ZwZDCJ2fK3AIcZzH1+LcHHcySYPRiBPwUXYuu6TamTVHajgcufmfVeMivkEBAvy0DcvEYnQUY2O9UfKq3dL3Z8jMEbx7VjSV0rGDcE7AhnkeFsbd2EVsiJpwMxy0a6UC9KQQKh77nUtFkCiJdJSXKlXO+VISGM4KM1/O18j57nW2Ju+ghd9ldthzH6iwKGRiMFeH5Zv+zctkbyE7mipSc+rrlYCHl6wruYGGeN1aWOeSb3ewyDpGmXmP6vkIYLsnZfKfRhQJV5gxQlk0xnr5NH6Q9J6i9qJxvGIYNzWc7XNoXVtbLfc9qh95uTcnqdyTDXrsFGojCmqEM6SAEhtNeRp2D5xxtSfKUEEtjyUnRQLTZWzN2OthZS0gLlP0YCS8x6M99pc8y04GBVdgFOsp/ioQfkmI7iapUjwSHzdUSakqzHOYPirxG41CyG4rBkhkQmiNm+7wCr5YEbZNGtTUwIGDMzYUNqEVm/eQbOGnrZFm3KdaGfhT0vCUZztk/XQc/7NhbVEjRnG3tiztNoUru4Zz5sx1zYp03WF8Um12iZd9DTDVQj5MNl0TbNMN3FQDEg6ouaBdVZuUWLQd+nqy0O62NRsbrS62lpU5z0/zFt6xLOCQ0hPMbbWl1nuu7XNvS1+r21ptLrdZSZ9M4sV6nHvIvRFUY4fMN08Gta81WvVFZ3Gg11bV5xi9UWk87lPCqvaGeIg24Jgo3EC1THL5HTNqx/cn9xBzry9bvilFRrmM7P/9+xu0osI9pr2vjjj7MaGlY+owYvr3Adx0RpFygycgQmc9zJvjwnN95E6B8A1VAB3FQqbApStOBiBcjI4PlSE3Mpwgk2Hp/P73EVx0BjKcGenZm5rA0ez/fN/dMkI0Khe+xbhnMjnP/xemYE70vDv/zW9IdMTgGX16YrSi0h4SW6XwwyEjJjwqVgcbSowqamA15HgcRi+0dZQLe0q6NZD69zCeBLei/k+fg8aWhnA5NrP/tRW2HCfuy/vJ46UIfkb2IQ4IiRXJaPA4D0+zHbyNDQwqipFBA+ezSy7iHPujvCBPCOSpyW/VO/zdTkeP1MRSWntsFDhtClPh162W++l0GgonctPNXKKndf9H8IXAkzK1tJkV5V/e/RYdMSbC+qHlZPSdDikH+a3So72etdeQXwcOo0ZSDwv7vnrYGq4qpX2sus0xQWNHkTj78d6RcgO5LBie99WYnK/RofnuOPOjLwB7Ty/gtfhUSq4fu+dPt+JeCp7I4wmXy/u7/7om68VYRegW/x1v3x5E+qqc47P/uCXpg35QA2zn+j8uGiqOrXxIRv676/3dUEKwe7R9vXV1fbR3vH/2/0vAHf/AHf/AHVvwPyEZidbQ7dZ0AAAAASUVORK5CYII="
								},
                                {
                                        "ContentType": "image/png",
                                        "Filename": "equity_change.png",
                                        "ContentID": "eq_change_pic",
                                        "Base64Content": cid1    
                                }
						]
				}
		]
    }
    result = mailjet.send.create(data=data)
    print("Email sent with status code: " + str(result.status_code))

def gen_tb(main_color, end_color, arg1, arg2, arg3):
    output = ""
    if len(main_color) > 0:
        output += "<tr style='color: " + str(main_color) + ";'>"
    else:
        output += "<tr>"
    
    # <td>AAPL</td>
    # <td>-2</td>
    # <td>+0.05</td>
    output += "<td style='text-align: left'>" + str(arg1) + "</td>"
    output += "<td style='text-align: left'>" + str(arg2) + "</td>"

    if len(end_color) > 0:
        output += "<td style='text-align: right; color: " + str(end_color) + "'>" + str(arg3) + "</td>"
    else:
        output += "<td style='text-align: right'>" + str(arg3) + "</td>"

    output += "</tr>"
    return output
