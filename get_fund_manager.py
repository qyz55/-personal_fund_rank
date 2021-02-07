# coding:UTF-8
import pandas as pd
import sys
import csv
import io
import math
import os
import os.path as osp
import re
import requests
import time
from bs4 import BeautifulSoup
import collections
import pickle
from utils import get_HTML, get_name_list, convert_percent, convert_day, calc_annual, calc_rank

day_thre=365
# sys.stdout = io.TextIOWrapper(sys.stdout.buffer,encoding='gb18030')
url = "http://fund.eastmoney.com/Company/f10/jjjl_80000229.html"
cur_t = time.strftime("%Y-%m-%d",time.localtime())
os.makedirs("cache",exist_ok=True)
f_name = osp.join("cache",cur_t+"_"+url.split("/")[-1][5:-5]+"_fund_manager.pkl")

if osp.isfile(f_name):
    with open(f_name, "rb") as f:
        dic = pickle.load(f)
else:
    tb = pd.read_html(url,encoding='utf-8')
    text = get_HTML(url)
    soup = BeautifulSoup(text,"html.parser")
    name_list=get_name_list(soup)
    dic = collections.OrderedDict()
    for i,j in zip(name_list, tb[2:]):
        dic[i]=j
    with open(f_name, "wb") as f:
        pickle.dump(dic, f)
name_list = list(dic.keys())
dd = list(dic.values())
print("Last manager:",name_list[-1])
print("Last manager's fund:\n",dd[-1])
rank_list = []
rank_rank = []
for name, d in zip(name_list, dd):
    an = []
    rn = []
    for i in range(len(d)):
        if convert_day(d["任职天数"][i]) >= day_thre and not "-" in d["任职回报"][i]:
            an.append(calc_annual(d["任职回报"][i], d["任职天数"][i]))
            rn.append(calc_rank(d["同类排名"][i]))
    if len(an) >= 3:
        rank_list.append([name,sum(an)/len(an)])
        rank_rank.append([name,sum(rn)/len(rn)])
rank_list = sorted(rank_list, key=lambda x:x[1], reverse=True)
rank_rank = sorted(rank_rank, key=lambda x:x[1])
print("profit")
for i in range(len(rank_list)):
    print (rank_list[i])
print("\nrank")
for i in range(len(rank_rank)):
    print (rank_rank[i])
    