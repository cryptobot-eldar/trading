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

TICK_INTERVAL = 60  # seconds



#The main function
def main():
    print('Starting sell module')

    # Running clock forever
    while True:
        start = time.time()
        tick()
        end = time.time()
        # Sleep the thread if needed
        if end - start < TICK_INTERVAL:
            time.sleep(TICK_INTERVAL - (end - start))

################################################################################################################
#what will be done every loop iteration
def tick():
    buy_size = parameters()[0] #The size for opening orders for STOP_LOSS mode
    stop_bot_force = parameters()[4]  #If stop_bot_force==1 we  stop bot and close all orders
    stop_bot = int(parameters()[11])
    market_summ = c.get_market_summaries().json()['result']
    BTC_price = c.get_ticker('USDT-BTC').json()['result']['Last']
    currtime = int(time.time())
    btc_trend = parameters()[12]
    current_order_count = order_count()
    debug_mode=parameters()[10]
    print "Global sell parameters configured, moving to market loop"



    #global active
    for summary in market_summ: #Loop trough the market summary
        try:
            if available_market_list(summary['MarketName']):
                market = summary['MarketName']

                #Candle analisys
                lastcandle = get_candles(market, 'thirtymin')['result'][-1:]
                currentlow = float(lastcandle[0]['L'])
                currentopen = float(lastcandle[0]['O'])
                currenthigh = float(lastcandle[0]['H'])
                previouscandle = get_candles(market, 'thirtymin')['result'][-2:]
                prevclose = float(previouscandle[0]['C'])
                lastcandle5 = get_candles(market, 'fivemin')['result'][-1:]
                currentlow5 = float(lastcandle5[0]['L'])
                currentopen5 = float(lastcandle5[0]['O'])
                currenthigh5 = float(lastcandle5[0]['H'])
                previouscandle5 = get_candles(market, 'fivemin')['result'][-2:]
                prevclose5 = float(previouscandle5[0]['C'])
                hourlastcandle = get_candles(market, 'hour')['result'][-1:]
                hourcurrentopen = float(hourlastcandle[0]['O'])
                hourcurrenthigh = float(hourlastcandle[0]['H'])
                hourprevcandle = get_candles(market, 'hour')['result'][-2:]
                hourprevopen = float(hourprevcandle[0]['O'])
                hourprevclose = float(hourprevcandle[0]['C'])
                fivemin='NONE'
                thirtymin='NONE'
                hour='NONE'
                candles_signal_short = str(heikin_ashi(market, 29))
                candles_signal_long = str(heikin_ashi(market, 30))

                timestamp = int(time.time())
                day_close = summary['PrevDay']   #Getting day of closing order
            #Current prices
                last = float(summary['Last'])  #last price
                bid = float(summary['Bid'])    #sell price
                ask = float(summary['Ask'])    #buy price
            #How much market has been changed


            #HOW MUCH TO BUY
                buy_quantity = buy_size / last
            #BOUGHT PRICE

                newbid=bid - bid*0.002


                #bought_price = get_closed_orders(market, 'PricePerUnit')
                #print market
            #Bought Quantity need for sell order, to know at which price we bought some currency
                bought_price_sql = float(status_orders(market, 3))
                bought_quantity_sql = float(status_orders(market, 2))
                sell_signal=status_orders(market, 23)
                sell_quantity_sql = bought_quantity_sql
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
                ai_time_second = heikin_ashi(market, 8)
                profit = parameters()[3]
                slow_market=heikin_ashi(market, 3)
                normal_candles=heikin_ashi(market, 19)

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

                print "Market prameters configured, moving to selling for ", market

                try:
                    db = MySQLdb.connect("database-service", "cryptouser", "123456", "cryptodb")
                    cursor = db.cursor()

                    serf = (newbid * bought_quantity_sql - bought_price_sql * bought_quantity_sql)
                    serf_usd = float("{0:.4f}".format(serf * BTC_price))
                    if bought_price_sql!=0:

                        #procent_serf = float(((newbid / bought_price_sql) - 1) * 100)
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
                        (last, market))
                    db.commit()
                except MySQLdb.Error, e:
                    print "Error %d: %s" % (e.args[0], e.args[1])
                    sys.exit(1)
                finally:
                    db.close()
                    ########

                #max_percent_sql = status_orders(market, 15)
                max_percent_sql = float("{0:.2f}".format(status_orders(market, 15)))
                min_percent_sql = float("{0:.2f}".format(status_orders(market, 24)))
                #print market, procent_serf
                print "Updated sell serf and procent serf stuff for", market

# Force Stop
                if stop_bot_force==1:
                        print ('    33 -Selling ' + str(format_float(sell_quantity_sql)) + ' units of ' + market + ' for ' + str(format_float(newbid)) + '  and getting or loosing  ' + str(format_float(serf * BTC_price)) + ' USD')
                        # print ('22 - Selling ' + str(format_float(sell_quantity_sql)) + ' units of ' + market + ' for ' + str(format_float(ask)) + '  and losing  ' + str(format_float(ask * bought_quantity_sql - bought_price_sql * bought_quantity_sql)) + ' BTC' ' or ' + str(format_float((ask * bought_quantity_sql - bought_price_sql * bought_quantity_sql) * BTC_price)) + ' USD')
                        try:
                            printed = ('    33 -Selling ' + str(format_float(sell_quantity_sql)) + ' units of ' + market + ' for ' + str(format_float(newbid)) + '  and getting or loosing  ' + str(format_float(serf*BTC_price)) + ' USD')
                            db = MySQLdb.connect("database-service", "cryptouser", "123456", "cryptodb")
                            cursor = db.cursor()
                            cursor.execute('insert into logs(date, log_entry) values("%s", "%s")' % (currenttime, printed))
                            cursor.execute('update orders set reason_close =%s where active=1 and market =%s', ("33 , Force_stop_bot p:    " + str(format_float(newbid)) + "    t:   " + str(currenttime),market))
                            cursor.execute('update orders set active = 0 where market =("%s")' % market)
                            db.commit()
                        except MySQLdb.Error, e:
                            print "Error %d: %s" % (e.args[0], e.args[1])
                            sys.exit(1)
                        finally:
                            db.close()
                        #Mail("egaraev@gmail.com", "egaraev@gmail.com", "New sell", printed, "database-service")




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


# AI_HA MODE SELL START
                print "Strarting selling mechanizm for ", market
                if bought_price_sql != None:
                    if bought_quantity_sql is None or bought_quantity_sql == 0.0:
                        # print market, bought_quantity_sql, current_balance
                        pass
                        # If curent balance of this currency more then zero
                    elif bought_quantity_sql > 0:
                        ##Check if we have completelly green candle


                        if ((serf_usd > 0 and max_percent_sql - procent_serf >= 0.2 and 1.5>=max_percent_sql >= 1.0 and fivemin=='D') or (serf_usd > 0 and max_percent_sql - procent_serf >= 0.1 and 1.0>=max_percent_sql >= 0.7 )  or (serf_usd > 0 and max_percent_sql - procent_serf >= 0.5 and 2.0>=max_percent_sql >= 1.5 and fivemin=='D') or (serf_usd > 0 and max_percent_sql - procent_serf >= 1.0 and 3.0>=max_percent_sql >= 2.0 and fivemin=='D') or max_percent_sql>7.0 and slow_market==1)\
                                    or  ((serf_usd > 0 and max_percent_sql - procent_serf >= 0.2 and 1.5>=max_percent_sql >= 0.8) or (serf_usd > 0 and max_percent_sql - procent_serf >= 1.5 and 3.0>=max_percent_sql >= 2.0 and fivemin=='D') or max_percent_sql>10.0  and slow_market==0):
                            print ('   6 -Selling ' + str(format_float(
                                sell_quantity_sql)) + ' units of ' + market + ' for ' + str(
                                format_float(newbid)) + '  and getting  +' + str(format_float(
                                ask * bought_quantity_sql - bought_price_sql * bought_quantity_sql)) + ' BTC' + ' or ' + str(
                                format_float((
                                                 newbid * bought_quantity_sql - bought_price_sql * bought_quantity_sql) * BTC_price)) + ' USD')
                            try:
                                printed = ('   6 -Selling ' + str(format_float(
                                    sell_quantity_sql)) + ' units of ' + market + ' for ' + str(
                                    format_float(newbid)) + '  and getting  +' + str(format_float(
                                    ask * bought_quantity_sql - bought_price_sql * bought_quantity_sql)) + ' BTC' + ' or ' + str(
                                    format_float((
                                                     newbid * bought_quantity_sql - bought_price_sql * bought_quantity_sql) * BTC_price)) + ' USD')
                                db = MySQLdb.connect("database-service", "cryptouser", "123456", "cryptodb")
                                cursor = db.cursor()
                                cursor.execute('insert into logs(date, log_entry) values("%s", "%s")' % (
                                    currenttime, printed))
                                # cursor.execute('update orders set active = 0, reason_close = "12 Take profit" where market =("%s")' % market)
                                cursor.execute(
                                    'update orders set reason_close =%s where active=1 and market =%s', (
                                        "4  TP , price:    " + str(
                                            format_float(newbid)) + "    time:   " + str(currenttime) +
                                        '  BTC: ' + str(btc_trend) + '  HAD: ' + str(HAD_trend) + ' HA: ' + str(
                                            HA_trend) + ' HAH: ' + str(HAH_trend) + ' HC: ' + str(
                                            hour) + ' 30mC: ' + str(thirtymin) + ' 5mC: ' + str(fivemin) + ' CS ' + str(
                                            candles_signal_short) + ' ' + str(candles_signal_long) + '  AI:' + str(
                                            ai_prediction(market)),
                                        market))
                                if sell_signal == 0:
                                    cursor.execute(
                                        'update orders set sell = 4 where active=1 and market =("%s")' % market)
                                if max_percent_sql > profit / 1.5:
                                    cursor.execute(
                                        "update markets set strike_time= %s  where market = %s",
                                        (currtime, market))
                                cursor.execute(
                                    "update orders set open_sell = %s, sell_time=%s  where market = %s and active =1",
                                    (1, currtime, market))
                                newvalue = summ_serf() + serf * BTC_price
                                cursor.execute('insert into statistics(date, serf, market) values("%s", "%s", "%s")' % (currenttime, newvalue, market))
                                db.commit()
                            except MySQLdb.Error, e:
                                print "Error %d: %s" % (e.args[0], e.args[1])
                                sys.exit(1)
                            finally:
                                db.close()
                                # Mail("egaraev@gmail.com", "egaraev@gmail.com", "New sell", printed,"database-service")


                        if serf_usd > 0  and (((currentopen == currentlow and prevclose <= currentopen and currentopen < currenthigh and last > prevclose and thirtymin=='U') or (currentopen == currentlow and currentopen < currenthigh and last > prevclose and thirtymin=='U') )):  #and slow_market==1

                                print ("We have GREEN candle for " + market + " and it is better to wait, before sell")
                                try:
                                    printed = (
                                        "    7 - We have GREEN candle for " + market + " and let`s wait it to be up")
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
                                pass




                        elif serf_usd > 0  and (((currentopen5 == currentlow5 and prevclose5 <= currentopen5 and currentopen5 < currenthigh5 and last > prevclose5 and fivemin=='U') or (currentopen5 == currentlow5 and currentopen5 < currenthigh5 and last > prevclose5 and fivemin=='U'))): #and normal_candles==1
                                print ("We have good trend for " + market)

                                try:
                                    printed = ("   8  - We have good short term trend for " + market)
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
                                pass


                        else:

                            if  (serf_usd > 0 and max_percent_sql - procent_serf >= 1.0 and max_percent_sql >= 3.0 and slow_market==1) or (serf_usd > 0 and max_percent_sql - procent_serf >= 1.5 and max_percent_sql >= 3.0 and slow_market==0):    # # WAS profit2
                                print ('    10  - Trying to Sell ' + str(
                                    format_float(
                                        sell_quantity_sql)) + ' units of ' + market + ' for ' + str(
                                    format_float(ask)) + '  and get  + ' + str(
                                    format_float(serf * BTC_price)) + ' USD')
                                try:
                                    printed = ('    10  - Trying to Sell ' + str(
                                        format_float(
                                            sell_quantity_sql)) + ' units of ' + market + ' for ' + str(
                                        format_float(ask)) + '  and get  + ' + str(
                                        format_float(serf * BTC_price)) + ' USD')
                                    db = MySQLdb.connect("database-service", "cryptouser", "123456",
                                                         "cryptodb")
                                    cursor = db.cursor()
                                    cursor.execute(
                                        'insert into logs(date, log_entry) values("%s", "%s")' % (
                                            currenttime, printed))
                                    # cursor.execute('update orders set reason_close = "225 AI take profit" where active=1 and market =("%s")' % market)
                                    cursor.execute(
                                        'update orders set reason_close =%s where active=1 and market =%s',
                                        (
                                            "6 Good TP SELL, price:  " + str(
                                                format_float(last)) + "  time:   " + str(
                                                currenttime) +
                                            '  BTC: ' + str(btc_trend) + '  HAD: ' + str(HAD_trend) + ' HA: ' + str(
                                                HA_trend) + ' HAH: ' + str(HAH_trend) + ' HC: ' + str(
                                                hour) + ' 30mC: ' + str(thirtymin) + ' 5mC: ' + str(
                                                fivemin) + ' CS ' + str(candles_signal_short) + ' ' + str(
                                                candles_signal_long) + '  AI:' + str(
                                                ai_prediction(market)), market))
                                    cursor.execute(
                                        'update orders set sell = 6 where active=1 and market =("%s")' % market)
                                    if max_percent_sql > profit / 1.5:
                                        cursor.execute(
                                            "update markets set strike_time= %s  where market = %s",
                                            (currtime, market))
                                    cursor.execute(
                                        "update orders set open_sell = %s, sell_time=%s  where market = %s and active =1",
                                        (1, currtime, market))
                                    newvalue = summ_serf() + serf * BTC_price
                                    cursor.execute(
                                        'insert into statistics(date, serf, market) values("%s", "%s", "%s")' % (
                                        currenttime, newvalue, market))
                                    db.commit()
                                except MySQLdb.Error, e:
                                    print "Error %d: %s" % (e.args[0], e.args[1])
                                    sys.exit(1)
                                finally:
                                    db.close()




                            if serf_usd<0 and max_percent_sql<=0.5 and procent_serf==min_percent_sql and  timestamp - timestamp_old > 7200:
                                    print ('  12 -Selling ' + str(format_float(
                                    sell_quantity_sql)) + ' units of ' + market + ' for ' + str(
                                    format_float(newbid)) + '  and losing  ' + str(format_float(
                                    ask * bought_quantity_sql - bought_price_sql * bought_quantity_sql)) + ' BTC' + ' or ' + str(
                                    format_float((
                                                     newbid * bought_quantity_sql - bought_price_sql * bought_quantity_sql) * BTC_price)) + ' USD')
                                    # print ('22 - Selling ' + str(format_float(sell_quantity_sql)) + ' units of ' + market + ' for ' + str(format_float(ask)) + '  and losing  ' + str(format_float(ask * bought_quantity_sql - bought_price_sql * bought_quantity_sql)) + ' BTC' ' or ' + str(format_float((ask * bought_quantity_sql - bought_price_sql * bought_quantity_sql) * BTC_price)) + ' USD')
                                    try:
                                        printed = ('  12 -Selling ' + str(format_float(
                                            sell_quantity_sql)) + ' units of ' + market + ' for ' + str(
                                            format_float(newbid)) + '  and losing  ' + str(format_float(
                                            ask * bought_quantity_sql - bought_price_sql * bought_quantity_sql)) + ' BTC' + ' or ' + str(
                                            format_float((
                                                         newbid * bought_quantity_sql - bought_price_sql * bought_quantity_sql) * BTC_price)) + ' USD')
                                        db = MySQLdb.connect("database-service", "cryptouser", "123456", "cryptodb")
                                        cursor = db.cursor()
                                        cursor.execute('insert into logs(date, log_entry) values("%s", "%s")' % (
                                            currenttime, printed))
                                        # cursor.execute('update orders set active = 0, reason_close = "12 Take profit" where market =("%s")' % market)
                                        cursor.execute(
                                            'update orders set reason_close =%s where active=1 and market =%s', (
                                                "3  fast SL, price:    " + str(
                                                    format_float(newbid)) + "    time:   " + str(currenttime) +
                                                '  BTC: ' + str(btc_trend) + '  HAD: ' + str(HAD_trend) + ' HA: ' + str(
                                                    HA_trend) + ' HAH: ' + str(
                                                    HAH_trend) + ' HC: ' + hour + ' 30mC: ' + thirtymin + ' 5mC: ' + fivemin + ' CS ' + str(
                                                    candles_signal_short) + ' ' + str(
                                                    candles_signal_long) + '  AI:' + str(
                                                    ai_prediction(market)),
                                                market))
                                        cursor.execute(
                                            'update orders set sell = 3 where active=1 and market =("%s")' % market)
                                        cursor.execute(
                                            "update orders set open_sell = %s, sell_time=%s  where market = %s and active =1",
                                            (1, currtime, market))
                                        newvalue = summ_serf() + serf * BTC_price
                                        cursor.execute(
                                            'insert into statistics(date, serf, market) values("%s", "%s", "%s")' % (
                                            currenttime, newvalue, market))
                                        db.commit()
                                    except MySQLdb.Error, e:
                                        print "Error %d: %s" % (e.args[0], e.args[1])
                                        sys.exit(1)
                                    finally:
                                        db.close()




                            elif (ai_prediction(market) != 'NEUTRAL' and ai_prediction(market) == 'DOWN') and newbid > bought_price_sql * ( 1 + profit/3) and currtime-ai_time_second<7200 and last<hourcurrentopen:  # #WAS profit2
                                    print ('    14  - Trying to sell ' + str(
                                    format_float(
                                        sell_quantity_sql)) + ' units of ' + market + ' for ' + str(
                                    format_float(newbid)) + '  and get  + ' + str(
                                    format_float(serf * BTC_price)) + ' USD')
                                    # print ('22 - Selling ' + str(format_float(sell_quantity_sql)) + ' units of ' + market + ' for ' + str(format_float(ask)) + '  and losing  ' + str(format_float(ask * bought_quantity_sql - bought_price_sql * bought_quantity_sql)) + ' BTC' ' or ' + str(format_float((ask * bought_quantity_sql - bought_price_sql * bought_quantity_sql) * BTC_price)) + ' USD')
                                    try:
                                        printed = ('    14  - Trying to sell ' + str(
                                            format_float(
                                                sell_quantity_sql)) + ' units of ' + market + ' for ' + str(
                                            format_float(newbid)) + '  and get  + ' + str(
                                            format_float(serf * BTC_price)) + ' USD')
                                        db = MySQLdb.connect("database-service", "cryptouser", "123456",
                                                             "cryptodb")
                                        cursor = db.cursor()
                                        cursor.execute(
                                            'insert into logs(date, log_entry) values("%s", "%s")' % (
                                                currenttime, printed))
                                        # cursor.execute('update orders set reason_close = "225 AI take profit" where active=1 and market =("%s")' % market)
                                        cursor.execute(
                                            'update orders set reason_close =%s where active=1 and market =%s',
                                            (
                                                "5 AI SELL, price:  " + str(
                                                    format_float(newbid)) + "  time:   " + str(
                                                    currenttime) +
                                                '  BTC: ' + str(btc_trend) + '  HAD: ' + str(HAD_trend) + ' HA: ' + str(
                                                    HA_trend) + ' HAH: ' + str(
                                                    HAH_trend) + ' HC: ' + hour + ' 30mC: ' + thirtymin + ' 5mC: ' + fivemin + ' CS ' + str(
                                                    candles_signal_short) + ' ' + str(candles_signal_long), market))
                                        cursor.execute(
                                            "update orders set open_sell = %s, sell_time=%s  where market = %s and active =1",
                                            (1, currtime, market))
                                        cursor.execute(
                                            'update orders set sell = 5 where active=1 and market =("%s")' % market)
                                        newvalue = summ_serf() + serf * BTC_price
                                        cursor.execute(
                                            'insert into statistics(date, serf, market) values("%s", "%s", "%s")' % (
                                            currenttime, newvalue, market))
                                        cursor.execute(
                                            "update markets set strike_time= %s  where market = %s",
                                            (currtime, market))
                                        db.commit()
                                    except MySQLdb.Error, e:
                                        print "Error %d: %s" % (e.args[0], e.args[1])
                                        sys.exit(1)
                                    finally:
                                        db.close()
                                #Mail("egaraev@gmail.com", "egaraev@gmail.com", "New sell", printed,"database-service")




#                            elif (active == 1) and  last > bought_price_sql * (1 + profit/1.5 ):  # #WAS profit2

                                        # print ('22 - Selling ' + str(format_float(sell_quantity_sql)) + ' units of ' + market + ' for ' + str(format_float(ask)) + '  and losing  ' + str(format_float(ask * bought_quantity_sql - bought_price_sql * bought_quantity_sql)) + ' BTC' ' or ' + str(format_float((ask * bought_quantity_sql - bought_price_sql * bought_quantity_sql) * BTC_price)) + ' USD')
#                                try:

#                                    printed = ('    12 -Selling ' + str(
#                                        format_float(
#                                            sell_quantity_sql)) + ' units of ' + market + ' for ' + str(
#                                        format_float(newbid)) + '  and getting   ' + str(
#                                        format_float(serf*BTC_price)) + ' USD')
#                                    db = MySQLdb.connect("database-service", "cryptouser", "123456",
#                                                         "cryptodb")
#                                    cursor = db.cursor()
#                                    cursor.execute(
#                                        'insert into logs(date, log_entry) values("%s", "%s")' % (
#                                            currenttime, printed))

#                                    cursor.execute(
#                                        'update orders set reason_close =%s where active=1 and market =%s',
#                                        (
#                                            "12 TP SELL, price:  " + str(
#                                                format_float(newbid)) + "  time:   " + str(
#                                                currenttime), market))
#                                    cursor.execute(
#                                        "update orders set sell_time=%s  where market = %s and active =1",
#                                        (currtime, market))

#                                    cursor.execute(
#                                        'update orders set active = 0 where market =("%s")' % market)

#                                    newvalue = summ_serf() + serf

#                                    cursor.execute(
#                                        'insert into statistics(date, serf, market) values("%s", "%s", "%s")' % (
#                                        currenttime, newvalue, market))
#                                    db.commit()

#                                except MySQLdb.Error, e:
#                                    print "Error %d: %s" % (e.args[0], e.args[1])
#                                    sys.exit(1)
#                                finally:
#                                    db.close()
                                #Mail("egaraev@gmail.com", "egaraev@gmail.com", "New sell", printed,"database-service")


#                            elif serf >= buy_size * profit / 3 and (
#                                        HAD_trend == "DOWN" or HA_trend == "DOWN" or HA_trend == "Revers-DOWN"):
#                                try:

#                                    printed = ('   132 Selling ' + str(
#                                        format_float(
#                                            sell_quantity_sql)) + ' units of ' + market + ' for ' + str(
#                                        format_float(newbid)) + '  and losing  ' + str(
#                                        format_float(serf)) + ' USD' )
#                                    db = MySQLdb.connect("database-service", "cryptouser", "123456",
#                                                         "cryptodb")
#                                    cursor = db.cursor()
#                                    cursor.execute(
#                                        'insert into logs(date, log_entry) values("%s", "%s")' % (
#                                            currenttime, printed))
#                                    cursor.execute(
#                                        'update orders set reason_close =%s where active=1 and market =%s',
#                                        ("132  SL, p:   " + str(
#                                            format_float(newbid)) + " t:    " + str(currenttime), market))
#                                    cursor.execute(
#                                        'update orders set active = 0 where market =("%s")' % market)
#                                    newvalue = summ_serf() + serf
#                                    cursor.execute(
#                                        'insert into statistics(date, serf, market) values("%s", "%s", "%s")' % (
#                                        currenttime, newvalue, market))
#                                    db.commit()
#                                except MySQLdb.Error, e:
#                                    print "Error %d: %s" % (e.args[0], e.args[1])
#                                    sys.exit(1)
#                                finally:
#                                    db.close()



                            elif (max_percent_sql==0 and timestamp-timestamp_old> 1800 and fivemin=='D'):   # #WAS profit2

                                    print ('    144 - Trying to Sell ' + str(
                                    format_float(
                                        sell_quantity_sql)) + ' units of ' + market + ' for ' + str(
                                    format_float(newbid)) + '  and lose   ' + str(
                                    format_float(serf * BTC_price)) + ' USD')
                                            # print ('Selling ' + str(format_float(sell_quantity_sql)) + ' units of ' + market + ' for ' + str(format_float(ask)) + '  and losing  ' + str(format_float(ask * bought_quantity_sql - bought_price_sql * bought_quantity_sql)) + ' BTC' ' or ' + str(format_float((ask * bought_quantity_sql - bought_price_sql * bought_quantity_sql) * BTC_price)) + ' USD')
                                    try:
                                         printed = ('    144 - Trying to Sell ' + str(
                                             format_float(
                                                 sell_quantity_sql)) + ' units of ' + market + ' for ' + str(
                                             format_float(newbid)) + '  and lose   ' + str(
                                             format_float(serf * BTC_price)) + ' USD')
                                         db = MySQLdb.connect("database-service", "cryptouser", "123456",
                                                              "cryptodb")
                                         cursor = db.cursor()
                                         cursor.execute(
                                             'insert into logs(date, log_entry) values("%s", "%s")' % (
                                                 currenttime, printed))

                                         cursor.execute(
                                             'update orders set reason_close =%s where active=1 and market =%s',
                                             (
                                                 "144 Zero SL SELL, price:  " + str(
                                                     format_float(newbid)) + "  time:   " + str(
                                                     currenttime), market))

                                         cursor.execute(
                                             "update orders set open_sell = %s, sell_time=%s  where market = %s and active =1",
                                             (1, currtime, market))
                                         newvalue = summ_serf() + serf * BTC_price
                                         cursor.execute(
                                             'insert into statistics(date, serf, market) values("%s", "%s", "%s")' % (
                                             currenttime, newvalue, market))
                                         db.commit()
                                    except MySQLdb.Error, e:
                                         print "Error %d: %s" % (e.args[0], e.args[1])
                                         sys.exit(1)
                                    finally:
                                         db.close()
                                #Mail("egaraev@gmail.com", "egaraev@gmail.com", "New sell", printed,"database-service")

                            elif ((newbid * (1 + profit / 3) < (bought_price_sql )) or procent_serf==min_percent_sql) and (sell_signal != 0): # #WAS profit2

                                     print ('   16  -Trying to Sell ' + str(format_float(sell_quantity_sql)) + ' units of ' + market + ' for ' + str(format_float(newbid)) + '  and lose  ' + str(format_float(serf * BTC_price)) + ' USD')
                                # print ('Selling ' + str(format_float(sell_quantity_sql)) + ' units of ' + market + ' for ' + str(format_float(ask)) + '  and losing  ' + str(format_float(ask * bought_quantity_sql - bought_price_sql * bought_quantity_sql)) + ' BTC' ' or ' + str(format_float((ask * bought_quantity_sql - bought_price_sql * bought_quantity_sql) * BTC_price)) + ' USD')
                                     try:
                                         printed = ('   16  -Trying to Sell ' + str(
                                             format_float(
                                                 sell_quantity_sql)) + ' units of ' + market + ' for ' + str(
                                             format_float(newbid)) + '  and lose  ' + str(
                                             format_float(serf * BTC_price)) + ' USD')
                                         db = MySQLdb.connect("database-service", "cryptouser", "123456",
                                                              "cryptodb")
                                         cursor = db.cursor()
                                         cursor.execute(
                                             'insert into logs(date, log_entry) values("%s", "%s")' % (
                                                 currenttime, printed))
                                         cursor.execute(
                                             'update orders set reason_close =%s where active=1 and market =%s',
                                             ("13 small SL, p:   " + str(
                                                 format_float(newbid)) + " t:    " + str(currenttime) +
                                              '  BTC: ' + str(btc_trend) + '  HAD: ' + str(
                                                 HAD_trend) + ' HA: ' + str(
                                                 HA_trend) + ' HAH: ' + str(HAH_trend) + ' HC: ' + str(
                                                 hour) + ' 30mC: ' + str(thirtymin) + ' 5mC: ' + str(
                                                 fivemin) + ' CS ' + str(candles_signal_short) + ' ' + str(
                                                 candles_signal_long) + '  AI:' + str(
                                                 ai_prediction(market)), market))
                                         cursor.execute(
                                             "update orders set open_sell = %s, sell_time=%s  where market = %s and active =1",
                                             (1, currtime, market))
                                         newvalue = summ_serf() + serf * BTC_price
                                         cursor.execute(
                                             'insert into statistics(date, serf, market) values("%s", "%s", "%s")' % (
                                             currenttime, newvalue, market))
                                         db.commit()
                                     except MySQLdb.Error, e:
                                         print "Error %d: %s" % (e.args[0], e.args[1])
                                         sys.exit(1)
                                     finally:
                                         db.close()
                                #Mail("egaraev@gmail.com", "egaraev@gmail.com", "New sell", printed, "database-service")


                            elif serf_usd >= 0 and procent_serf<0.4 and (sell_signal != 0) and last<hourcurrentopen:   # # WAS profit2
                                    print ('  18  - Trying to Sell ' + str(
                                    format_float(
                                        sell_quantity_sql)) + ' units of ' + market + ' for ' + str(
                                    format_float(newbid)) + '  and get + ' + str(
                                    format_float(serf * BTC_price)) + ' USD')
                                    # print ('22 - Selling ' + str(format_float(sell_quantity_sql)) + ' units of ' + market + ' for ' + str(format_float(ask)) + '  and losing  ' + str(format_float(ask * bought_quantity_sql - bought_price_sql * bought_quantity_sql)) + ' BTC' ' or ' + str(format_float((ask * bought_quantity_sql - bought_price_sql * bought_quantity_sql) * BTC_price)) + ' USD')
                                    try:
                                        printed = ('  18  - Trying to Sell ' + str(
                                            format_float(
                                                sell_quantity_sql)) + ' units of ' + market + ' for ' + str(
                                            format_float(newbid)) + '  and get + ' + str(
                                            format_float(serf * BTC_price)) + ' USD')
                                        db = MySQLdb.connect("database-service", "cryptouser", "123456",
                                                             "cryptodb")
                                        cursor = db.cursor()
                                        cursor.execute(
                                            'insert into logs(date, log_entry) values("%s", "%s")' % (
                                                currenttime, printed))
                                        cursor.execute(
                                            'update orders set reason_close =%s where active=1 and market =%s',
                                            ("14  ha TP, p:   " + str(
                                                format_float(newbid)) + " t:    " + str(currenttime) +
                                             '  BTC: ' + str(btc_trend) + '  HAD: ' + str(HAD_trend) + ' HA: ' + str(
                                                HA_trend) + ' HAH: ' + str(HAH_trend) + ' HC: ' + str(
                                                hour) + ' 30mC: ' + str(thirtymin) + ' 5mC: ' + str(
                                                fivemin) + ' CS ' + str(candles_signal_short) + ' ' + str(
                                                candles_signal_long) + '  AI:' + str(
                                                ai_prediction(market)), market))

                                        cursor.execute(
                                            "update orders set open_sell = %s, sell_time=%s  where market = %s and active =1",
                                            (1, currtime, market))
                                        newvalue = summ_serf() + serf * BTC_price
                                        cursor.execute(
                                            'insert into statistics(date, serf, market) values("%s", "%s", "%s")' % (
                                            currenttime, newvalue, market))
                                        db.commit()
                                    except MySQLdb.Error, e:
                                        print "Error %d: %s" % (e.args[0], e.args[1])
                                        sys.exit(1)
                                    finally:
                                        db.close()
                                    #Mail("egaraev@gmail.com", "egaraev@gmail.com", "New sell", printed, "database-service")



 ## AI_HA MODE SL
                            elif (sell_signal == 7):  # #WAS profit2
                                    print ('  20 - Trying to Sell ' + str(
                                    format_float(
                                        sell_quantity_sql)) + ' units of ' + market + ' for ' + str(
                                    format_float(newbid)) + '  and get or lose  ' + str(
                                    format_float(serf * BTC_price)) + ' USD')

                                    # print ('Selling ' + str(format_float(sell_quantity_sql)) + ' units of ' + market + ' for ' + str(format_float(ask)) + '  and losing  ' + str(format_float(ask * bought_quantity_sql - bought_price_sql * bought_quantity_sql)) + ' BTC' ' or ' + str(format_float((ask * bought_quantity_sql - bought_price_sql * bought_quantity_sql) * BTC_price)) + ' USD')
                                    try:
                                        printed = ('  20 - Trying to Sell ' + str(
                                            format_float(
                                                sell_quantity_sql)) + ' units of ' + market + ' for ' + str(
                                            format_float(newbid)) + '  and get or lose  ' + str(
                                            format_float(serf * BTC_price)) + ' USD')
                                        db = MySQLdb.connect("database-service", "cryptouser", "123456",
                                                             "cryptodb")
                                        cursor = db.cursor()
                                        cursor.execute(
                                            'insert into logs(date, log_entry) values("%s", "%s")' % (
                                                currenttime, printed))
                                        cursor.execute(
                                            'update orders set reason_close =%s where active=1 and market =%s',
                                            ("7  BTC SL, p:   " + str(
                                                format_float(newbid)) + " t:    " + str(currenttime) +
                                             '  BTC: ' + str(btc_trend) + '  HAD: ' + str(HAD_trend) + ' HA: ' + str(
                                                HA_trend) + ' HAH: ' + str(HAH_trend) + ' HC: ' + str(
                                                hour) + ' 30mC: ' + str(thirtymin) + ' 5mC: ' + str(
                                                fivemin) + ' CS ' + str(candles_signal_short) + ' ' + str(
                                                candles_signal_long) + '  AI:' + str(
                                                ai_prediction(market)), market))

                                        cursor.execute(
                                            "update orders set open_sell = %s, sell_time=%s  where market = %s and active =1",
                                            (1, currtime, market))
                                        newvalue = summ_serf() + serf * BTC_price
                                        cursor.execute(
                                            'insert into statistics(date, serf, market) values("%s", "%s", "%s")' % (
                                            currenttime, newvalue, market))
                                        db.commit()
                                    except MySQLdb.Error, e:
                                        print "Error %d: %s" % (e.args[0], e.args[1])
                                        sys.exit(1)
                                    finally:
                                        db.close()
                                #Mail("egaraev@gmail.com", "egaraev@gmail.com", "New sell", printed, "database-service")

                            elif (newbid * bought_quantity_sql * (1 + profit) < (bought_price_sql * bought_quantity_sql)): # #WAS profit2
                                        print ('  22 Prod - Trying to sell ' + str(format_float(sell_quantity_sql)) + ' units of ' + market + ' for ' + str(format_float(newbid)) + '  and lose  ' + str(format_float(serf * BTC_price)) + ' USD')
                                        # print ('Selling ' + str(format_float(sell_quantity_sql)) + ' units of ' + market + ' for ' + str(format_float(ask)) + '  and losing  ' + str(format_float(ask * bought_quantity_sql - bought_price_sql * bought_quantity_sql)) + ' BTC' ' or ' + str(format_float((ask * bought_quantity_sql - bought_price_sql * bought_quantity_sql) * BTC_price)) + ' USD')
                                        try:
                                            printed = ('  22 Prod - Trying to sell ' + str(
                                                format_float(
                                                    sell_quantity_sql)) + ' units of ' + market + ' for ' + str(
                                                format_float(newbid)) + '  and lose  ' + str(
                                                format_float(serf * BTC_price)) + ' USD')
                                            db = MySQLdb.connect("database-service", "cryptouser", "123456",
                                                                 "cryptodb")
                                            cursor = db.cursor()
                                            cursor.execute(
                                                'insert into logs(date, log_entry) values("%s", "%s")' % (
                                                    currenttime, printed))
                                            cursor.execute(
                                                'update orders set reason_close =%s where active=1 and market =%s',
                                                (" 22  SL, p:   " + str(
                                                    format_float(newbid)) + " t:    " + str(currenttime) +
                                        '  BTC: ' + str(btc_trend) + '  HAD: ' + str(HAD_trend) + ' HA: ' + str(
                                            HA_trend) + ' HAH: ' + str(HAH_trend)  + ' HC: ' + str(hour) + ' 30mC: ' + str(thirtymin) + ' 5mC: ' + str(fivemin)+' CS '+str(candles_signal_short) +' '+str(candles_signal_long) + '  AI:'  + str(
                                        ai_prediction(market)), market))
                                            cursor.execute(
                                                "update orders set open_sell = %s, sell_time=%s  where market = %s and active =1",
                                                (1, currtime, market))
                                            newvalue = summ_serf() + serf * BTC_price
                                            cursor.execute(
                                                'insert into statistics(date, serf, market) values("%s", "%s", "%s")' % (
                                                currenttime, newvalue, market))
                                            db.commit()
                                        except MySQLdb.Error, e:
                                            print "Error %d: %s" % (e.args[0], e.args[1])
                                            sys.exit(1)
                                        finally:
                                            db.close()

                            else:

                                pass

                else:
                    pass


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


def percent_serf_min(marketname):
    db = MySQLdb.connect("database-service", "cryptouser", "123456", "cryptodb")
    cursor = db.cursor()
    market=marketname
    cursor.execute("SELECT percent_serf_min FROM orders WHERE active =1 and market = '%s'" % market)
    r = cursor.fetchall()
    for row in r:
        return float(row[0])
    return 0



#Allowed currencies function for SQL
def available_market_list(marketname):
    db = MySQLdb.connect("database-service", "cryptouser", "123456", "cryptodb")
    cursor = db.cursor()
    market = marketname
    cursor.execute("SELECT * FROM orders WHERE active =1 and market = '%s'" % market)
    r = cursor.fetchall()
    for row in r:
        if row[1] == marketname:
            return True

    return False




def parameters():
    db = MySQLdb.connect("database-service", "cryptouser", "123456", "cryptodb")
    cursor = db.cursor()
    cursor.execute("SELECT * FROM parameters")
    r = cursor.fetchall()
    for row in r:
        return (row[1]), (row[2]), (row[3]), (row[4]), (row[5]), (row[6]), (row[7]), (row[8]), (row[9]), (row[10]), (row[11]), (row[12]), (row[13]), (row[14]), (row[15]), (row[16]), (row[17]), (row[18]), (row[19]), (row[20]), (row[21]), (row[22]), (row[23]), (row[24])

    return 0



def ai_prediction(marketname):
    db = MySQLdb.connect("database-service", "cryptouser", "123456", "cryptodb")
    cursor = db.cursor()
    market = marketname
    cursor.execute("SELECT ai_direction FROM markets WHERE active =1 and market = '%s'" % market)
    r = cursor.fetchall()
    for row in r:
        return (row[0])

    return 0

def ai_prediction_price(marketname):
    db = MySQLdb.connect("database-service", "cryptouser", "123456", "cryptodb")
    cursor = db.cursor()
    market = marketname
    cursor.execute("SELECT ai_price FROM markets WHERE active =1 and ai_direction='UP' and market = '%s'" % market)
    r = cursor.fetchall()
    for row in r:
        return (row[0])

    return 0









def summ_serf():
    db = MySQLdb.connect("database-service", "cryptouser", "123456", "cryptodb")
    cursor = db.cursor()
    #market=marketname
    cursor.execute("SELECT SUM(serf_usd) FROM orders where active=0")
    r = cursor.fetchall()
    for row in r:
        if row[0] is not None:
            return float(row[0])
            # return 0
        else:
            return 0







def order_count():
    db = MySQLdb.connect("database-service", "cryptouser", "123456", "cryptodb")
    cursor = db.cursor()
    #market=marketname
    cursor.execute("SELECT COUNT(*) FROM orders where active=1")
    r = cursor.fetchall()
    for row in r:
        return row[0]
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


#Check first iteration orders in mysql
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
    orderhistory = c.get_order_history(currency).json()
    orders = orderhistory['result']
    for order in orders:
        if order['Exchange'] == currency:
                return order[value]
        else:
            return False


#Check the market prices
def get_balance_from_market(market_type):
    markets_res = c.get_markets().json()
    markets = markets_res['result']
    #print markets
    for market in markets:
        if market['MarketName'] == market_type:
            return get_balance(market['MarketCurrency'])
            # Return a fake response of 0 if not found
    return {'result': {'Available': 0}}

#Getting balance for currency
def get_balance(currency):
    res =c.get_balance(currency).json()
    if res['result'] is not None and len(res['result']) > 0:
        return res
        # If there are no results, than your balance is 0
    return {'result': {'Available': 0}}



#get the orders
def get_open_orders(market):
    return c.get_open_orders(market).json()


#check if order opened or not
def has_open_order(market, order_type):
    orders_res = c.get_open_orders(market).json()
    orders = orders_res['result']
    if orders is None or len(orders) == 0:
        return False
# Check all orders for a LIMIT_BUY
    for order in orders:
        if order['OrderType'] == order_type:
            return True
    return False


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



def format_float(f):
    return "%.4f" % f


if __name__ == "__main__":
    main()
