#Imports from modules, libraries and config files
import config
from pybittrex.client import Client
import requests
import time
import datetime
import hmac
import hashlib
import MySQLdb
import sys
import smtplib
#c = Client(api_key=config.key, api_secret=config.secret)   #Configuring bytrex client with API key/secret from config file
c=Client(api_key="", api_secret="")
c1 = Client(api_key=config.key, api_secret=config.secret)   #Configuring bytrex client with API key/secret from config file
#The main function
def main():
    print('Starting buy module')
    tick()

################################################################################################################
#what will be done every loop iteration
def tick():
    buy_size = parameters()[0] #The size for opening orders for STOP_LOSS mode
    max_buy_timeout = parameters()[1]
    stop_bot_force = parameters()[4]  #If stop_bot_force==1 we  stop bot and close all orders
    stop_bot = int(parameters()[11])
    market_summ = c.get_market_summaries().json()['result']
    BTC_price = c.get_ticker('USDT-BTC').json()['result']['Last']
    currtime = int(time.time())
    btc_trend = parameters()[12]
    debug_mode=parameters()[10]
    max_orders = parameters()[5]
    current_order_count = order_count()
    bot_mode=parameters()[23]
    print "Global buy parameters configured, moving to market loop"


    #global active
    if bot_mode==0:
        for summary in market_summ: #Loop trough the market summary
            try:
                if available_market_list(summary['MarketName']):
                    market = summary['MarketName']
                    #Candle analisys
                    lastcandle = get_candles(market, 'thirtymin')['result'][-1:]
                    currentopen = float(lastcandle[0]['O'])
                    currenthigh = float(lastcandle[0]['H'])
                    hourpreviouscandle4 = get_candles(market, 'hour')['result'][-5:]
                    hourprevopen4 = float(hourpreviouscandle4[0]['O'])
                    fivehourcurrentopen = hourprevopen4
                    hourpreviouscandle9 = get_candles(market, 'hour')['result'][-10:]
                    hourprevopen9 = float(hourpreviouscandle9[0]['O'])
                    hourpreviouscandle5 = get_candles(market, 'hour')['result'][-6:]
                    hourprevclose5 = float(hourpreviouscandle5[0]['C'])
                    fivehourprevopen = hourprevopen9
                    fivehourprevclose = hourprevclose5
                    lastcandle5 = get_candles(market, 'fivemin')['result'][-1:]
                    currentlow5 = float(lastcandle5[0]['L'])
                    currentopen5 = float(lastcandle5[0]['O'])
                    currenthigh5 = float(lastcandle5[0]['H'])
                    hourlastcandle = get_candles(market, 'hour')['result'][-1:]
                    hourcurrentopen = float(hourlastcandle[0]['O'])
                    hourcurrenthigh = float(hourlastcandle[0]['H'])


                    timestamp = int(time.time())
                    day_close = summary['PrevDay']   #Getting day of closing order
                #Current prices
                    last = float(summary['Last'])  #last price
                    bid = float(summary['Bid'])    #sell price
                    ask = float(summary['Ask'])    #buy price
                #How much market has been changed
                    percent_chg = float(((last / day_close) - 1) * 100)

                #HOW MUCH TO BUY
                    buy_quantity = buy_size / last
                #BOUGHT PRICE

                    newbid=bid - bid*0.002
                    newask=ask + ask*0.002

                    #bought_price = get_closed_orders(market, 'PricePerUnit')
                    #print market
                #Bought Quantity need for sell order, to know at which price we bought some currency
                    bought_price_sql = float(status_orders(market, 3))
                    bought_quantity_sql = float(status_orders(market, 2))
                    active = active_orders(market)
                    iteration = int(iteration_orders(market))
                    timestamp_old = int(timestamp_orders(market))
                    now = datetime.datetime.now()
                    currenttime = now.strftime("%Y-%m-%d %H:%M")
                    HA_trend=heikin_ashi(market, 10)
                    HAD_trend=heikin_ashi(market, 18)
                    HAH_trend = heikin_ashi(market, 20)
                    ha_time_second=heikin_ashi(market, 23)
                    percent_sql=float(heikin_ashi(market, 21))
                    volume_sql=int(heikin_ashi(market, 22))
                    strike_time = heikin_ashi(market, 24)
                    strike_time2 = heikin_ashi(market, 27)
                    percent_sql=float("{0:.2f}".format(heikin_ashi(market, 21)))
                    volume_sql=int(heikin_ashi(market, 22))
                    candles = str(heikin_ashi(market, 28))
                    candles_signal_short = str(heikin_ashi(market, 29))
                    candles_signal_long = str(heikin_ashi(market, 30))


                    fivemin='NONE'
                    thirtymin='NONE'
                    hour='NONE'
                    candles_status='OK'


                    if last>currentopen5:
                        fivemin='U'
                    elif last==currenthigh5:
                        fivemin='H'
                    else:
                        fivemin='D'

                    if last>currentopen:
                        thirtymin='U'
                    elif last==currenthigh:
                        thirtymin='H'
                    else:
                        thirtymin='D'

                    if last>hourcurrentopen:
                        hour='U'
                    elif last==hourcurrenthigh:
                        hour='H'
                    else:
                        hour='D'

                    if fivemin=='D' and thirtymin=='D' and fivemin=='D':
                        candles_status='DOWN'
                    else:
                        candles_status='OK'





                    print "Market parameters configured, moving to buy for ", market


                    try:
                        db = MySQLdb.connect("database-service", "cryptouser", "123456", "cryptodb")
                        cursor = db.cursor()

                        serf = float("{0:.8f}".format(newbid * bought_quantity_sql - bought_price_sql * bought_quantity_sql))
                        if bought_price_sql!=0:

                            procent_serf = float("{0:.2f}".format(((newbid / bought_price_sql) - 1) * 100))
                            #print market, procent_serf

                            if procent_serf>=percent_serf_max(market):
                                cursor.execute("update orders set percent_serf_max=%s where market = %s and active =1 and open_sell=0 ",(procent_serf, market))
                            elif procent_serf<percent_serf_min(market):
                                cursor.execute(
                                "update orders set percent_serf_min=%s where market = %s and active =1 and open_sell=0 ",
                                (procent_serf, market))
                            else:
                                cursor.execute("update orders set percent_serf=%s where market = %s and active =1 and open_sell=0 ",(procent_serf, market))

                        cursor.execute("update orders set serf = %s where market = %s and active =1" , (serf, market))
                        #cursor.execute("update orders set serf_usd = %s where market = %s and active =1", (serf, market))   - for usd trading
                        cursor.execute("update orders set serf_usd = %s where market = %s and active =1", (serf*BTC_price, market))
                        cursor.execute(
                            "update markets set current_price = %s  where market = %s and active =1",
                            (newbid, market))
                        db.commit()
                    except MySQLdb.Error, e:
                        print "Error %d: %s" % (e.args[0], e.args[1])
                        sys.exit(1)
                    finally:
                        db.close()
                        ########

                    max_percent_sql = status_orders(market, 15)
                    print "Updated serf and procent serf stuff for" , market







    #FIRST ITERATION - BUY
                    #spread=((ask/bid)-1)*100
                    print "Starting buying mechanizm for " , market

                    if ((stop_bot == 0) and (HA_trend == "UP" or HA_trend == "Revers-UP" or HA_trend == "STABLE") and (
                                    HAD_trend == "UP" or HAD_trend == "Revers-UP" or HAD_trend == "STABLE") and (HAH_trend == "UP" or HAH_trend == "Revers-UP") and stop_bot_force == 0) and (
                                currtime - ha_time_second < 2000) and (currtime - strike_time > 36000)  and current_order_count<=max_orders and last>fivehourcurrentopen and fivehourprevopen<fivehourprevclose and last>currentopen and (currtime - strike_time2 > 36000): # and fivemin!='D' and hour!='D' and percent_sql>0.0 and candles_status!='DOWN' :
                            #balance_res = get_balance_from_market(market)
                            #current_balance = balance_res['result']['Available']

                            # If we have some currency on the balance
                            if bought_quantity_sql !=0.0:
                                print ('    2 - We already have ' + str(
                                        format_float(bought_quantity_sql)) + '  ' + market + ' on our balance')
                                try:
                                    printed = ('    2 - We already have ' + str(
                                        format_float(bought_quantity_sql)) + '  ' + market + ' on our balance')
                                    db = MySQLdb.connect("database-service", "cryptouser", "123456", "cryptodb")
                                    cursor = db.cursor()
                                    cursor.execute(
                                        'insert into logs(date, log_entry) values("%s", "%s")' % (currenttime, printed))
                                    db.commit()
                                except MySQLdb.Error, e:
                                    print "Error %d: %s" % (e.args[0], e.args[1])
                                    sys.exit(1)
                                finally:
                                    db.close()
                            # if we have some active orders in sql
                            elif active == 1 and iteration != 0:
                                print  ('    3 - We already have ' + str(float(status_orders(market, 2))) + ' units of ' + market + ' on our balance')
                                try:
                                    printed = ('    3 - We already have ' + str(
                                        float(status_orders(market, 2))) + ' units of ' + market + ' on our balance')
                                    db = MySQLdb.connect("database-service", "cryptouser", "123456", "cryptodb")
                                    cursor = db.cursor()
                                    cursor.execute(
                                        'insert into logs(date, log_entry) values("%s", "%s")' % (currenttime, printed))
                                    db.commit()
                                except MySQLdb.Error, e:
                                    print "Error %d: %s" % (e.args[0], e.args[1])
                                    sys.exit(1)
                                finally:
                                    db.close()
                            else:
                                # Buy some currency by market analize first time
                                try:
                                    print ('    4- Purchasing (by ai_ha) '  + str(format_float(buy_quantity)) + ' units of ' + market + ' for ' + str(format_float(newask)))
                                    printed = ('    4- Purchasing (by ai_ha) '  + str(
                                        format_float(buy_quantity)) + ' units of ' + market + ' for ' + str(
                                        format_float(newask)))
                                    db = MySQLdb.connect("database-service", "cryptouser", "123456", "cryptodb")
                                    cursor = db.cursor()
                                    cursor.execute(
                                        'insert into logs(date, log_entry) values("%s", "%s")' % (currenttime, printed))
                                    cursor.execute(
                                        'insert into orders(market, quantity, price, active, date, timestamp, iteration, btc_direction, params, heikin_ashi) values("%s", "%s", "%s", "%s", "%s", "%s", "%s", "%s", "%s", "%s")' % (
                                        market, buy_quantity, newask, "1", currenttime, timestamp, "1", btc_trend, '  BTC: ' + str(btc_trend) + '  HAD: ' + str(HAD_trend) + ' HA: ' + str(HA_trend) + ' HAH: ' + str(HAH_trend) + '  %  ' + str(percent_sql) + '  vol  ' + str(volume_sql)  + ' HC: ' + str(hour) + ' 30mC: ' + str(thirtymin) + ' 5mC: ' + str(fivemin)+' CS '+str(candles_signal_short) +' '+str(candles_signal_long) + '  AI   ' + str(ai_prediction(market)),
                                        HA_trend))
                                    cursor.execute("update orders set serf = %s, one_step_active =1 where market = %s and active =1",
                                                   (serf, market))
                                    db.commit()
                                except MySQLdb.Error, e:
                                    print "Error %d: %s" % (e.args[0], e.args[1])
                                    sys.exit(1)
                                finally:
                                    db.close()
                                #Mail("egaraev@gmail.com", "egaraev@gmail.com", "New purchase", printed, "database-service")
                                break


    ### BUY FOR HA_AI mode - END

                                ##DEBUG MESSAGE
                    if debug_mode == 1:
                        try:
                            printed = ("    XXX - Bot is working with " + market)
                            db = MySQLdb.connect("database-service", "cryptouser", "123456", "cryptodb")
                            cursor = db.cursor()
                            cursor.execute(
                                'insert into logs(date, log_entry) values("%s", "%s")' % (
                                    currenttime, printed))
                            db.commit()
                        except MySQLdb.Error, e:
                            print "Error %d: %s" % (e.args[0], e.args[1])
                            sys.exit(1)
                        finally:
                            db.close()





                else:
                    pass
            except:
                continue


##############################################################################
###############################################################################

    else:

        for summary in market_summ:  # Loop trough the market summary
            try:
                if available_market_list(summary['MarketName']):
                    market = summary['MarketName']

                    # Candle analisys
                    lastcandle = get_candles(market, 'thirtymin')['result'][-1:]

                    currentopen = float(lastcandle[0]['O'])
                    currenthigh = float(lastcandle[0]['H'])

                    hourpreviouscandle4 = get_candles(market, 'hour')['result'][-5:]
                    hourprevopen4 = float(hourpreviouscandle4[0]['O'])
                    fivehourcurrentopen = hourprevopen4

                    hourpreviouscandle9 = get_candles(market, 'hour')['result'][-10:]
                    hourprevopen9 = float(hourpreviouscandle9[0]['O'])

                    hourpreviouscandle5 = get_candles(market, 'hour')['result'][-6:]
                    hourprevclose5 = float(hourpreviouscandle5[0]['C'])

                    fivehourprevopen = hourprevopen9
                    fivehourprevclose = hourprevclose5

                    lastcandle5 = get_candles(market, 'fivemin')['result'][-1:]
                    currentlow5 = float(lastcandle5[0]['L'])
                    currentopen5 = float(lastcandle5[0]['O'])
                    currenthigh5 = float(lastcandle5[0]['H'])
                    hourlastcandle = get_candles(market, 'hour')['result'][-1:]
                    hourcurrentopen = float(hourlastcandle[0]['O'])
                    hourcurrenthigh = float(hourlastcandle[0]['H'])

                    timestamp = int(time.time())

                    # Current prices
                    last = float(summary['Last'])  # last price
                    bid = float(summary['Bid'])  # sell price
                    ask = float(summary['Ask'])  # buy price
                    newbid = bid - bid * 0.002
                    newask = ask + ask * 0.002
                    # How much market has been changed

                    # HOW MUCH TO BUY
                    buy_quantity = buy_size / last
                    # BOUGHT PRICE
                    # Bought Quantity need for sell order, to know at which price we bought some currency
                    bought_quantity = get_balance_from_market(market)['result']['Available']
                    bought_price_sql = float(status_orders(market, 3))
                    bought_quantity_sql = float(status_orders(market, 2))
                    active = active_orders(market)
                    timestamp_old = int(timestamp_orders(market))
                    now = datetime.datetime.now()
                    currenttime = now.strftime("%Y-%m-%d %H:%M")
                    HA_trend = heikin_ashi(market, 10)
                    HAD_trend = heikin_ashi(market, 18)
                    HAH_trend = heikin_ashi(market, 20)
                    ha_time_second = heikin_ashi(market, 23)
                    strike_time = heikin_ashi(market, 24)
                    strike_time2 = heikin_ashi(market, 27)
                    percent_sql = float("{0:.2f}".format(heikin_ashi(market, 21)))
                    volume_sql = int(heikin_ashi(market, 22))
                    candles = str(heikin_ashi(market, 28))
                    # print get_balance_from_market(market)['result']
                    balance_res = get_balance_from_market(market)
                    current_balance = balance_res['result']['Balance']
                    current_available = balance_res['result']['Available']
                    # print market, candles
                    btc_quantity = float(bought_quantity * newbid)
                    candles_signal_short = str(heikin_ashi(market, 29))
                    candles_signal_long = str(heikin_ashi(market, 30))

                    fivemin = 'NONE'
                    thirtymin = 'NONE'
                    hour = 'NONE'
                    candles_status = 'OK'

                    if last > currentopen5:
                        fivemin = 'U'
                    elif last == currenthigh5:
                        fivemin = 'H'
                    else:
                        fivemin = 'D'

                    if last > currentopen:
                        thirtymin = 'U'
                    elif last == currenthigh:
                        thirtymin = 'H'
                    else:
                        thirtymin = 'D'

                    if last > hourcurrentopen:
                        hour = 'U'
                    elif last == hourcurrenthigh:
                        hour = 'H'
                    else:
                        hour = 'D'

                    if fivemin == 'D' and thirtymin == 'D' and fivemin == 'D':
                        candles_status = 'DOWN'
                    else:
                        candles_status = 'OK'

                    # if open_sell(market)!=1:

                    try:
                        db = MySQLdb.connect("database-service", "cryptouser", "123456", "cryptodb")
                        cursor = db.cursor()
                        # cursor.execute("update parameters set usdt_btc_price = %s, btc_ha_direction_day =%s where id = %s", (BTC_price, btc_trend, 1))
                        # prev_serf = previous_serf(market)
                        serf = float(
                            "{0:.8f}".format(newbid * bought_quantity_sql - bought_price_sql * bought_quantity_sql))
                        if bought_price_sql != 0:
                            procent_serf = float("{0:.2f}".format(((newbid / bought_price_sql) - 1) * 100))
                            cursor.execute(
                                "update orders set percent_serf=%s where market = %s and active =1 and open_sell=0 ",
                                (procent_serf, market))
                            if procent_serf >= percent_serf_max(market):
                                cursor.execute(
                                    "update orders set percent_serf_max=%s where market = %s and active =1 and open_sell=0 ",
                                    (procent_serf, market))
                            elif procent_serf < percent_serf_min(market):
                                cursor.execute(
                                    "update orders set percent_serf_min=%s where market = %s and active =1 and open_sell=0 ",
                                    (procent_serf, market))
                            else:
                                cursor.execute(
                                    "update orders set percent_serf=%s where market = %s and active =1 and open_sell=0 ",
                                    (procent_serf, market))
                        # print market, procent_serf
                        cursor.execute("update orders set serf = %s where market = %s and active =1 and open_sell=0 ",
                                       (serf, market))
                        cursor.execute(
                            "update orders set serf_usd = %s where market = %s and active =1  and open_sell=0 ",
                            (serf * BTC_price, market))
                        cursor.execute("update markets set current_price = %s  where market = %s and active =1",
                                       (newbid, market))
                        db.commit()
                    except MySQLdb.Error, e:
                        print "Error %d: %s" % (e.args[0], e.args[1])
                        sys.exit(1)
                    finally:
                        db.close()
                        ########
                    max_percent_sql = status_orders(market, 15)

                    # print market, max_percent_sql, procent_serf, last, fivehourprevopen, last, currentopen



                    # print market, bought_quantity
                    if bought_quantity is not None:
                        if has_open_order(market, 'LIMIT_SELL'):
                            print('Order already opened to sell  ' + market)
                            try:
                                printed = ('    1 - Order already opened to sell  ' + market)
                                uuid = order_uuid(market)
                                db = MySQLdb.connect("database-service", "cryptouser", "123456", "cryptodb")
                                cursor = db.cursor()
                                cursor.execute(
                                    'insert into logs(date, log_entry) values("%s", "%s")' % (currenttime, printed))
                                cursor.execute(
                                    'update orders set uuid =%s where active=1 and open_sell=1 and market =%s',
                                    (uuid, market))
                                db.commit()
                            except MySQLdb.Error, e:
                                print "Error %d: %s" % (e.args[0], e.args[1])
                                sys.exit(1)
                            finally:
                                db.close()

                        elif has_open_order(market, 'LIMIT_BUY'):
                            print('Order already opened to buy  ' + market)
                            try:
                                printed = ('    2 - Order already opened to buy  ' + market)
                                db = MySQLdb.connect("database-service", "cryptouser", "123456", "cryptodb")
                                cursor = db.cursor()
                                cursor.execute(
                                    'insert into logs(date, log_entry) values("%s", "%s")' % (currenttime, printed))
                                db.commit()
                            except MySQLdb.Error, e:
                                print "Error %d: %s" % (e.args[0], e.args[1])
                                sys.exit(1)
                            finally:
                                db.close()
                        else:
                            # print market, bought_quantity,
                            if timestamp - timestamp_old < 1800:
                                try:
                                    db = MySQLdb.connect("database-service", "cryptouser", "123456", "cryptodb")
                                    cursor = db.cursor()
                                    cursor.execute("update orders set quantity = %s where market = %s and active =1",
                                                   (bought_quantity, market))
                                    db.commit()
                                except MySQLdb.Error, e:
                                    print "Error %d: %s" % (e.args[0], e.args[1])
                                    sys.exit(1)
                                finally:
                                    db.close()
                                    ########
                            else:
                                pass
                    else:
                        pass

                        # print market, candles


                        # What if we have sent the buy order to bittrex?

                    if open_buy(market) == 2:

                        if has_open_order(market, 'LIMIT_BUY'):
                            if currtime - buy_time(market) < max_buy_timeout:
                                print('Order already opened to buy  ' + market)
                                try:
                                    printed = ('    8 - Order already opened to buy  ' + market)
                                    db = MySQLdb.connect("database-service", "cryptouser", "123456", "cryptodb")
                                    cursor = db.cursor()
                                    cursor.execute(
                                        'insert into logs(date, log_entry) values("%s", "%s")' % (currenttime, printed))
                                    db.commit()
                                except MySQLdb.Error, e:
                                    print "Error %d: %s" % (e.args[0], e.args[1])
                                    sys.exit(1)
                                finally:
                                    db.close()

                            else:
                                print(' Order cancelled  ' + market)
                                try:
                                    printed = ('    9 - Order has been cancelled  ' + market)
                                    db = MySQLdb.connect("database-service", "cryptouser", "123456", "cryptodb")
                                    cursor = db.cursor()
                                    cursor.execute(
                                        'insert into logs(date, log_entry) values("%s", "%s")' % (currenttime, printed))
                                    cursor.execute(
                                        'delete from orders  where active=2 and market =("%s")' % market)
                                    db.commit()
                                except MySQLdb.Error, e:
                                    print "Error %d: %s" % (e.args[0], e.args[1])
                                    sys.exit(1)
                                finally:
                                    db.close()
                                #########################################CANCEL OLD ORDER#####
                                uuid = order_uuid(market)
                                print c1.market_cancel(uuid)
                                Mail("egaraev@gmail.com", "egaraev@gmail.com", "Cancel order", printed,
                                     "database-service")
                                #############################################################


                        elif current_available == 0.0 or current_balance == 0.0 and currtime - buy_time(
                                market) > max_buy_timeout:
                            print(' Order failed  ' + market)
                            try:
                                printed = ('    6- Order has been failed to buy  ' + market)
                                db = MySQLdb.connect("database-service", "cryptouser", "123456", "cryptodb")
                                cursor = db.cursor()
                                cursor.execute(
                                    'insert into logs(date, log_entry) values("%s", "%s")' % (currenttime, printed))
                                cursor.execute(
                                    'update orders set active= 3  where active=2 and market =("%s")' % market)
                                db.commit()
                            except MySQLdb.Error, e:
                                print "Error %d: %s" % (e.args[0], e.args[1])
                                sys.exit(1)
                            finally:
                                db.close()
                            Mail("egaraev@gmail.com", "egaraev@gmail.com", "Failed order", printed, "database-service")



                        else:
                            try:
                                print ('    10 Prod -This currency has been bought ' + market)
                                printed = ('    10 Prod -This currency has been bought   ' + market)
                                db = MySQLdb.connect("database-service", "cryptouser", "123456", "cryptodb")
                                cursor = db.cursor()
                                cursor.execute(
                                    'insert into logs(date, log_entry) values("%s", "%s")' % (currenttime, printed))
                                cursor.execute(
                                    "update orders set quantity = %s, price=%s, active=1, date=%s, timestamp=%s, iteration=1, btc_direction=%s, params=%s, heikin_ashi=%s  where market = %s and active =2",
                                    (buy_quantity, newbid, currenttime, timestamp, btc_trend,
                                     '  BTC: ' + str(btc_trend) + '  HAD: ' + str(HAD_trend) + ' HA: ' + str(
                                         HA_trend) + ' HAH: ' + str(HAH_trend) + '  %  ' + str(
                                         percent_sql) + '  vol  ' + str(volume_sql) + ' HC: ' + str(
                                         hour) + ' 30mC: ' + str(thirtymin) + ' 5mC: ' + str(fivemin) + ' CS ' + str(
                                         candles_signal_short) + ' ' + str(candles_signal_long), HA_trend, market))
                                db.commit()
                            except MySQLdb.Error, e:
                                print "Error %d: %s" % (e.args[0], e.args[1])
                                sys.exit(1)
                            finally:
                                db.close()
                            Mail("egaraev@gmail.com", "egaraev@gmail.com", "Currency bought", printed,
                                 "database-service")

                            break
                            # print market


                    # if  ((stop_bot == 0) and (HA_trend == "UP" or HA_trend == "Revers-UP") and (HAD_trend=="UP" or HAD_trend == "Revers-UP" or HAD_trend == "STABLE") and stop_bot_force == 0) and last>currentopen5 and percent_chg>0 and (currtime-ha_time_second<1500) and current_order_count<=max_orders: # and (currtime-strike_time>5000):  # and ((dayprevclose>=daycurrentopen or daycurrentopen==daycurrenthigh) is not True) and (currenthigh>currentopen or currentopen<currentclose):  # 0.8 - 3.5  #
                    if ((stop_bot == 0) and (HA_trend == "UP" or HA_trend == "Revers-UP" or HA_trend == "STABLE") and (
                                        HAD_trend == "UP" or HAD_trend == "Revers-UP" or HAD_trend == "STABLE") and (
                            HAH_trend == "UP" or HAH_trend == "Revers-UP") and stop_bot_force == 0) and (
                                    currtime - ha_time_second < 2000) and (currtime - strike_time > 36000) and (
                            currtime - strike_time2 > 36000) and current_order_count <= max_orders and last > fivehourcurrentopen and fivehourprevopen < fivehourprevclose and last > currentopen:  # and fivemin!='D' and hour!='D' and percent_sql>0.0 and candles_status!='DOWN':
                        # If we have opened order on bitrex
                        if has_open_order(market, 'LIMIT_BUY'):
                            # print('Order already opened to buy  ' + market)
                            try:
                                printed = ('    2 .1 - Order already opened to buy  ' + market)
                                db = MySQLdb.connect("database-service", "cryptouser", "123456", "cryptodb")
                                cursor = db.cursor()
                                cursor.execute(
                                    'insert into logs(date, log_entry) values("%s", "%s")' % (currenttime, printed))
                                db.commit()
                            except MySQLdb.Error, e:
                                print "Error %d: %s" % (e.args[0], e.args[1])
                                sys.exit(1)
                            finally:
                                db.close()
                        # If we have some currency on the balance

                        elif ((current_balance != 0.0) or (current_available != 0.0)) and btc_quantity > 0.0005:
                            print market, current_balance, current_available
                            # print('We already have ' + str(format_float(current_balance)) + ' units of  ' + market + ' on our balance')
                            try:
                                printed = ('    3.1 - We already have ' + str(
                                    format_float(bought_quantity_sql)) + '  ' + market + ' on our balance')
                                db = MySQLdb.connect("database-service", "cryptouser", "123456", "cryptodb")
                                cursor = db.cursor()
                                cursor.execute(
                                    'insert into logs(date, log_entry) values("%s", "%s")' % (currenttime, printed))
                                db.commit()
                            except MySQLdb.Error, e:
                                print "Error %d: %s" % (e.args[0], e.args[1])
                                sys.exit(1)
                            finally:
                                db.close()
                        # if we have some active orders in sql
                        elif active == 1 or (active == 1 and order_uuid(market) != 0):
                            # print ('We already have ' + str(float(status_orders(market, 2))) + ' units of ' + market + ' on our balance')
                            try:
                                printed = ('    3.2 - We already have ' + str(
                                    float(status_orders(market, 2))) + ' units of ' + market + ' on our balance')
                                db = MySQLdb.connect("database-service", "cryptouser", "123456", "cryptodb")
                                cursor = db.cursor()
                                cursor.execute(
                                    'insert into logs(date, log_entry) values("%s", "%s")' % (currenttime, printed))
                                db.commit()
                            except MySQLdb.Error, e:
                                print "Error %d: %s" % (e.args[0], e.args[1])
                                sys.exit(1)
                            finally:
                                db.close()
                        else:
                            # Buy some currency by market analize first time
                            try:
                                printed = ('    4.1 - Prod - Trying to Purchase  ' + str(
                                    format_float(buy_quantity)) + ' units of ' + market + ' for ' + str(
                                    format_float(bid)))
                                db = MySQLdb.connect("database-service", "cryptouser", "123456", "cryptodb")
                                cursor = db.cursor()
                                cursor.execute(
                                    'insert into logs(date, log_entry) values("%s", "%s")' % (currenttime, printed))
                                cursor.execute(
                                    'insert into orders(market, quantity, price, active, date, timestamp, iteration, btc_direction, params, heikin_ashi) values("%s", "%s", "%s", "%s", "%s", "%s", "%s", "%s", "%s", "%s")' % (
                                        market, buy_quantity, newask, "2", currenttime, timestamp, "1", btc_trend,
                                        '  BTC: ' + str(btc_trend) + '  HAD: ' + str(HAD_trend) + ' HA: ' + str(
                                            HA_trend) + ' HAH: ' + str(HAH_trend) + '  %  ' + str(
                                            percent_sql) + '  vol  ' + str(volume_sql) + ' HC: ' + str(
                                            hour) + ' 30mC: ' + str(thirtymin) + ' 5mC: ' + str(fivemin) + ' CS ' + str(
                                            candles_signal_short) + ' ' + str(candles_signal_long) + '  AI   ' + str(
                                            ai_prediction(market)),
                                        HA_trend))
                                cursor.execute(
                                    "update orders set serf = %s where market = %s and active =2",
                                    (serf, market))
                                db.commit()
                            except MySQLdb.Error, e:
                                print "Error %d: %s" % (e.args[0], e.args[1])
                                sys.exit(1)
                            finally:
                                db.close()
                            Mail("egaraev@gmail.com", "egaraev@gmail.com", "New purchase", printed, "database-service")
                            #########!!!!!!!!! BUYING MECHANIZM, DANGER !!!!###################################
                            # print c.buy_limit(market, fiboquantity*2, last).json()
                            print c1.buy_limit(market, buy_quantity, newask).json()
                            #########!!!!!!!!! BUYING MECHANIZM, DANGER !!!!##################################
                            break

                            ### FOR HA_AI mode - END
                            # print market, percent_sql
                            ##DEBUG MESSAGE
                    if debug_mode == 1:
                        try:
                            printed = ("    XXX - Bot is working with " + market)
                            db = MySQLdb.connect("database-service", "cryptouser", "123456", "cryptodb")
                            cursor = db.cursor()
                            cursor.execute(
                                'insert into logs(date, log_entry) values("%s", "%s")' % (
                                    currenttime, printed))
                            db.commit()
                        except MySQLdb.Error, e:
                            print "Error %d: %s" % (e.args[0], e.args[1])
                            sys.exit(1)
                        finally:
                            db.close()





                else:
                    pass
            except:
                continue


### FUNCTIONS
###############################################################################################################

def heikin_ashi(marketname, value):
    db = MySQLdb.connect("database-service", "cryptouser", "123456", "cryptodb")
    cursor = db.cursor()
    market = marketname
    cursor.execute("SELECT * FROM markets WHERE market = '%s'" % market)
    r = cursor.fetchall()
    for row in r:
        if row[1] == marketname:
            return row[value]

    return False





def Mail(FROM,TO,SUBJECT,TEXT,SERVER):

# Prepare actual message
    message = """\
    From: %s
    To: %s
    Subject: %s

    %s
    """ % (FROM, TO, SUBJECT, TEXT)
# Send the mail
    server = smtplib.SMTP(SERVER)
    server.sendmail(FROM, TO, message)
    server.quit()



#Allowed currencies function for SQL
def available_market_list(marketname):
    db = MySQLdb.connect("database-service", "cryptouser", "123456", "cryptodb")
    cursor = db.cursor()
    market = marketname
    cursor.execute("SELECT * FROM markets WHERE active =1 and market = '%s'" % market)
    r = cursor.fetchall()
    for row in r:
        if row[1] == marketname:
            return True

    return False







def order_count():
    db = MySQLdb.connect("database-service", "cryptouser", "123456", "cryptodb")
    cursor = db.cursor()
    #market=marketname
    cursor.execute("SELECT COUNT(*) FROM orders where active=1")
    r = cursor.fetchall()
    for row in r:
        return row[0]
    return 0


def parameters():
    db = MySQLdb.connect("database-service", "cryptouser", "123456", "cryptodb")
    cursor = db.cursor()
    cursor.execute("SELECT * FROM parameters")
    r = cursor.fetchall()
    for row in r:
        return (row[1]), (row[2]), (row[3]), (row[4]), (row[5]), (row[6]), (row[7]), (row[8]), (row[9]), (row[10]), (row[11]), (row[12]), (row[13]), (row[14]), (row[15]), (row[16]), (row[17]), (row[18]), (row[19]), (row[20]), (row[21]), (row[22]), (row[23]), (row[24])

    return 0





def percent_serf(marketname):
    db = MySQLdb.connect("database-service", "cryptouser", "123456", "cryptodb")
    cursor = db.cursor()
    market=marketname
    cursor.execute("SELECT percent_serf FROM orders WHERE active =1 and market = '%s'" % market)
    r = cursor.fetchall()
    for row in r:
        return float(row[0])
    return 0




def percent_serf_max(marketname):
    db = MySQLdb.connect("database-service", "cryptouser", "123456", "cryptodb")
    cursor = db.cursor()
    market=marketname
    cursor.execute("SELECT percent_serf_max FROM orders WHERE active =1 and market = '%s'" % market)
    r = cursor.fetchall()
    for row in r:
        return float(row[0])
    return 0


def percent_serf_min(marketname):
    db = MySQLdb.connect("database-service", "cryptouser", "123456", "cryptodb")
    cursor = db.cursor()
    market=marketname
    cursor.execute("SELECT percent_serf_min FROM orders WHERE active =1 and market = '%s'" % market)
    r = cursor.fetchall()
    for row in r:
        return float(row[0])
    return 0







def open_buy(marketname):
    db = MySQLdb.connect("database-service", "cryptouser", "123456", "cryptodb")
    cursor = db.cursor()
    market=marketname
    cursor.execute("SELECT active FROM orders WHERE active =2 and market = '%s'" % market)
    r = cursor.fetchall()
    for row in r:
        return (row[0])
    return 0









def buy_time(marketname):
    db = MySQLdb.connect("database-service", "cryptouser", "123456", "cryptodb")
    cursor = db.cursor()
    market=marketname
    cursor.execute("SELECT timestamp FROM orders WHERE active =2 and market = '%s'" % market)
    r = cursor.fetchall()
    for row in r:
        return (row[0])
    return 0







#Check active orders in mysql
def timestamp_orders(marketname):
    db = MySQLdb.connect("database-service", "cryptouser", "123456", "cryptodb")
    cursor = db.cursor()
    market=marketname
    cursor.execute("SELECT * FROM orders WHERE active = 1 and market = '%s'" % market)
    #cursor.execute("SELECT o.*, m.market FROM orders o, markets m WHERE o.active = 1 and o.market_id = m.id and m.market like '%%'" % market)
    r = cursor.fetchall()
    for row in r:
        return int(row[6])

    return 0





#Check active orders in mysql
def active_orders(marketname):
    db = MySQLdb.connect("database-service", "cryptouser", "123456", "cryptodb")
    cursor = db.cursor()
    market=marketname
    cursor.execute("SELECT * FROM orders WHERE active = 1 and market = '%s'" % market)
    #cursor.execute("SELECT o.*, m.market FROM orders o, markets m WHERE o.active = 1 and o.market_id = m.id and m.market like '%%'" % market)
    r = cursor.fetchall()
    for row in r:
        return int(row[4])

    return 0







#Check the status of active orders
# 2 - is quantity, 3 -is price, 4 - active/passive
def status_orders(marketname, value):
    db = MySQLdb.connect("database-service", "cryptouser", "123456", "cryptodb")
    cursor = db.cursor()
    market=marketname
    cursor.execute("SELECT * FROM orders WHERE active = 1 and market = '%s'" % market)
    #cursor.execute("SELECT o.*, m.market FROM orders o, markets m WHERE o.active = 1 and o.market_id = m.id and m.market like '%%'" % market)
    r = cursor.fetchall()
    for row in r:
        if row[1] == marketname:
            return row[value]

    return 0




#Function for checking the history of orders
def get_closed_orders(currency, value):
    orderhistory = c1.get_order_history(currency).json()
    orders = orderhistory['result']
    for order in orders:
        if order['Exchange'] == currency:
                return order[value]
        else:
            return False

def ai_prediction(marketname):
    db = MySQLdb.connect("database-service", "cryptouser", "123456", "cryptodb")
    cursor = db.cursor()
    market = marketname
    cursor.execute("SELECT ai_direction FROM markets  WHERE market = '%s'" % market)
    r = cursor.fetchall()
    for row in r:
        return (row[0])

    return 0


#Check the market prices
def get_balance_from_market(market_type):
    markets_res = c1.get_markets().json()
    markets = markets_res['result']
    #print markets
    for market in markets:
        if market['MarketName'] == market_type:
            return get_balance(market['MarketCurrency'])
            # Return a fake response of 0 if not found
    return {'result': {'Available': 0}}

#Getting balance for currency
def get_balance(currency):
    res =c1.get_balance(currency).json()
    if res['result'] is not None and len(res['result']) > 0:
        return res
        # If there are no results, than your balance is 0
    return {'result': {'Available': 0}}



#get the orders
def get_open_orders(market):
    return c1.get_open_orders(market).json()


#check if order opened or not
def has_open_order(market, order_type):
    orders_res = c1.get_open_orders(market).json()
    orders = orders_res['result']
    if orders is None or len(orders) == 0:
        return False
# Check all orders for a LIMIT_BUY
    for order in orders:
        if order['OrderType'] == order_type:
            return True
    return False


def order_uuid(market):
    orders_res = c1.get_open_orders(market).json()
    orders = orders_res['result']
    if orders is None or len(orders) == 0:
        return False
    else:
        return c1.get_open_orders(market).json()['result'][0]['OrderUuid']





def get_candles(market, tick_interval):
    url = 'https://bittrex.com/api/v2.0/pub/market/GetTicks?apikey=' + config.key + '&MarketName=' + market +'&tickInterval=' + str(tick_interval)
    return signed_request(url)


def signed_request(url):
    now = time.time()
    url += '&nonce=' + str(now)
    signed = hmac.new(config.secret, url.encode('utf-8'), hashlib.sha512).hexdigest()
    headers = {'apisign': signed}
    r = requests.get(url, headers=headers)
    return r.json()

def iteration_orders(marketname):
    db = MySQLdb.connect("database-service", "cryptouser", "123456", "cryptodb")
    cursor = db.cursor()
    market=marketname
    cursor.execute("SELECT * FROM orders WHERE active = 1 and market = '%s'" % market)
    #cursor.execute("SELECT o.*, m.market FROM orders o, markets m WHERE o.active = 1 and o.market_id = m.id and m.market like '%%'" % market)
    r = cursor.fetchall()
    for row in r:
        return int(row[7])

    return 0




def format_float(f):
    return "%.4f" % f


if __name__ == "__main__":
    main()
