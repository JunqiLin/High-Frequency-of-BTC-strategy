#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Mon Dec  2 10:53:26 2019

@author: linjunqi
"""

import requests
import pandas as pd 
import numpy as np
board_len = 20
cb_r = 0            #coinbase handling fee
bf_r = 0            #bitflyer handling fee
cb_btc = 50         #coibase origin btc
bf_btc = 50         #bitflyer origin btc
cb_usdt = 700000    #coinbase origin usdt
bf_usdt = 700000    #bitflyer origin usdt


cb_burl = 'https://api.pro.coinbase.com'
bf_burl = 'https://api.bitflyer.com'

cb_query = '/products/BTC-USD/book?level=2'
bf_query = '/v1/getboard?product_code=BTC_USD'

cb_ticker = cb_burl + cb_query
bf_ticker = bf_burl + bf_query
#board = pd.read_csv('./temp.csv')
#记录结果
record = pd.DataFrame(columns=['cb_price','cb_size','bf_price','bf_size','handling','net_profit','cb_btc','cb_usdt','bf_btc','bf_usdt'])
#
while(1):
    cb_resp = requests.get(cb_ticker)
    bf_resp = requests.get(bf_ticker)
    cb_data = cb_resp.json()
    bf_data = bf_resp.json()

    board = pd.DataFrame(columns=['cb_ask','cb_ask_size','cb_bid','cb_bid_size', 'bf_ask','bf_ask_size', 'bf_bid','bf_bid_size'])

    board['cb_ask'] = np.array(cb_data['asks'])[:board_len,0].astype(np.float64)
    board['cb_ask_size'] = np.array(cb_data['asks'])[:board_len,1].astype(np.float64)
    board['cb_bid'] = np.array(cb_data['bids'])[:board_len,0].astype(np.float64)
    board['cb_bid_size'] = np.array(cb_data['bids'])[:board_len,1].astype(np.float64)
    pa =[]
    sa = []
    pb = []
    sb = []

    for i, (d1, d2) in enumerate(zip(bf_data['asks'], bf_data['bids'])):
        if i<board_len:
            pa.append(d1['price'])
            sa.append(d1['size'])
            pb.append(d2['price'])
            sb.append(d2['size'])
        
    board['bf_ask'] = pa
    board['bf_ask_size'] = sa
    board['bf_bid'] = pb
    board['bf_bid_size'] = sb  
    ##套利1
    if board['bf_bid'][0] > board['cb_ask'][0]:
        print("bitflyer buy > coinbase sell, check handling:")
    #    print("bitflyer 1st buy price is %s, size is %s"%(board['bf_bid'][0],board['bf_bid_size'][0]) )
    #    print("coinbase 1st sell price is %s, size is %s"%(board['cb_ask'][0], board['cb_ask_size'][0]) )
    #        df[df['one'] > 5]
        indexs = board[board['bf_bid'] > board['cb_ask'][0]].index
        amount = np.sum(board.loc[indexs,'bf_bid_size'])
        if amount < board['cb_ask_size'][0]:
            min_amount = amount
            t = 0
            for i in range(len(indexs)):
                tol_price = board.loc[i,'bf_bid'] * board.loc[i,'bf_bid_size']
                t = t + tol_price            
            avg_price = t/min_amount
        else:
            min_amount = board['cb_ask_size'][0]       
            temp_size = 0
            temp_price = 0
            for i in range(len(indexs)):
                if min_amount <= temp_size + board.loc[i,'bf_bid_size'] :
                    tol_price = temp_price +  (min_amount - temp_size)*board.loc[i,'bf_bid']
                    avg_price = tol_price / min_amount
                else:
                    temp_size = temp_size + board.loc[i,'bf_bid_size']
                    temp_price = temp_price + board.loc[i,'bf_bid_size'] * board.loc[i,'bf_bid']
    
    #    print("min trading amount is %s"%(min_amount))
        profit = abs((board['cb_ask'][0]-avg_price)) * min_amount
        cb_handling = cb_r * board['cb_ask'][0] * min_amount
        bf_handling = bf_r * avg_price * min_amount
        handling = cb_handling + bf_handling
        re =[]
        if profit > handling:
            print(",Profit, Now trading...")
            print("buy %s btc at %s btc/usdt in coinbase and sell %s btc at %s btc/usdt in bitflyer"%(min_amount,board['cb_ask'][0],min_amount,avg_price))
            net_profit = profit - handling
            cb_btc = cb_btc + min_amount
            cb_usdt = cb_usdt - board['cb_ask'][0]*min_amount
            bf_btc = bf_btc - min_amount
            bf_usdt = bf_usdt + avg_price * min_amount
    #        re = pd.DataFrame(np.array([(board['cb_ask'][0]),min_amount,avg_price,-min_amount,handling,net_profit,cb_btc,cb_usdt,bf_btc,bf_usdt])).T
            re = np.array([(board['cb_ask'][0]),min_amount,avg_price,-min_amount,handling,net_profit,cb_btc,cb_usdt,bf_btc,bf_usdt]).reshape(1,10)
            df = pd.DataFrame(re, columns=['cb_price','cb_size','bf_price','bf_size','handling','net_profit','cb_btc','cb_usdt','bf_btc','bf_usdt'])
            record = record.append(df,ignore_index=True)
        if len(record) > 10:
            record.to_csv('./record.csv')
            break
        
    ##套利2   
    elif board['cb_bid'][0] > board['bf_ask'][0]:
        print("coinbase buy > bitflyer sell, Check handling:")
        indexs = board[board['cb_bid'] > board['bf_ask'][0]].index
        amount = np.sum(board.loc[indexs,'cb_bid_size'])
        if amount < board['bf_ask_size'][0]:
            min_amount = amount
            t = 0
            for i in range(len(indexs)):
                tol_price = board.loc[i,'cb_bid'] * board.loc[i,'cb_bid_size']
                t = t + tol_price            
            avg_price = t/min_amount
        else:
            min_amount = board['bf_ask_size'][0]       
            temp_size = 0
            temp_price = 0
            for i in range(len(indexs)):
                if min_amount <= temp_size + board.loc[i,'cb_bid_size'] :
                    tol_price = temp_price +  (min_amount - temp_size)*board.loc[i,'cb_bid']
                    avg_price = tol_price / min_amount
                else:
                    temp_size = temp_size + board.loc[i,'cb_bid_size']
                    temp_price = temp_price + board.loc[i,'cb_bid_size'] * board.loc[i,'cb_bid']
    
    #    print("min trading amount is %s"%(min_amount))
        profit = abs((board['bf_ask'][0]-avg_price)) * min_amount
        bf_handling = bf_r * board['bf_ask'][0] * min_amount
        cb_handling = cb_r * avg_price * min_amount
        handling = cb_handling + bf_handling
        re =[]
        if profit > handling:
            print("Profit, Now trading...")
            print("buy %s btc at %s btc/usdt in bitflyer and sell %s btc at %s btc/usdt in coinbase"%(min_amount,board['bf_ask'][0],min_amount,avg_price))
            net_profit = profit - handling
            cb_btc = cb_btc - min_amount
            cb_usdt = cb_usdt + board['bf_ask'][0]*min_amount
            bf_btc = bf_btc + min_amount
            bf_usdt = bf_usdt - avg_price * min_amount
    #        re = pd.DataFrame(np.array([(board['cb_ask'][0]),min_amount,avg_price,-min_amount,handling,net_profit,cb_btc,cb_usdt,bf_btc,bf_usdt])).T
            re = np.array([(board['bf_ask'][0]),min_amount,avg_price,-min_amount,handling,net_profit,cb_btc,cb_usdt,bf_btc,bf_usdt]).reshape(1,10)
            df = pd.DataFrame(re, columns=['cb_price','cb_size','bf_price','bf_size','handling','net_profit','cb_btc','cb_usdt','bf_btc','bf_usdt'])
            record = record.append(df,ignore_index=True)
        if len(record) > 10:
            record.to_csv('./record.csv')
            break       
    #无套利机会
    else:
        print("No arbitrage")
        
    


    