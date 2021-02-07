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
import numpy as np
import pickle

def get_HTML(url):
    header = {"User-Agent": "Mozilla/5.0 (Linux; Android 6.0; Nexus 5 Build/MRA58N) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/68.0.3440.106 Mobile Safari/537.36"}
    try:
        r = requests.get(url,timeout = 30,headers=header)
        r.raise_for_status()
        r.encoding = r.apparent_encoding   #指定编码形式
        return r.text
    except:
        return "please inspect your url or setup"

def get_name_list(soup):
    a = soup.find_all('p', class_='table-content-title text-left')
    s=">[\u4e00-\u9fa5_a-zA-Z0-9\(\)\s]*?</a"
    p = re.compile(s)
    name_list=[]
    for i in a:
        d=p.findall(str(i))
        d=d[0][1:-3]
        assert len(d)>0
        name_list.append(d)
    return name_list

def convert_percent(s):
    if s[-1]=="%":
        return float(s[:-1])
    else:
        return float(s)
        
def convert_day(s):
    ss=s.split("年又")
    if len(ss)>=2:
        return int(ss[0])*365+int(ss[1].split("天")[0])
    else:
        return int(ss[0].split("天")[0])

def calc_annual(s, days):
    return math.pow(1+convert_percent(s)/100.0, 365.0/convert_day(days))

def calc_rank(s):
    ss = s.split("|")
    return float(ss[0])/float(ss[1])

def gen_year_season_key(year, season):
    if type(year) == int:
        year=str(year)
    if type(season) == int:
        season=str(season)
    return year[2:4]+season

def gen_year_key(year):
    if type(year) == int:
        year=str(year)
    return year[2:4]

def time_convert(serve_time):
    start_time, end_time = serve_time.split("~")
    start_year, start_month, _ = start_time.split(".")
    start_season = (int(start_month)-1) // 3 + 1
    start_year = int(start_year)

    if end_time == "至今":
        end_year = int(time.strftime("%Y",time.localtime()))
        end_season = (int(time.strftime("%m",time.localtime()))-1)//3 + 1
    else:
        end_year, end_month, _ = end_time.split(".")
        end_season = (int(end_month)-1) // 3 + 1
        end_year = int(end_year)
    valid_ys = []
    for y in range(start_year, end_year+1):
        ss = start_season if y == start_year else 1
        es = end_season if y == end_year else 4
        for s in range(ss,es+1):
            stry = str(y)
            valid_ys.append(stry[2:4] + str(s))
    return valid_ys

def preprocess(score, ave):
    return min(((100+score)/(100+ave)-1)*100, 6)

def coefficient(l):
    c=[1,1,1,1]
    return c[min(len(c),l)-1]

def calc_score(data_season, data_year, time_dic):
    valid_data = []
    for key, (num, valid_num, num_s, _, _, valid_s) in data_season.items():
        if key in time_dic and valid_num and (data_year[key[:2]][3] or valid_s):
            if valid_s:
                ave = num_s
            else:
                ave = (math.sqrt(math.sqrt(1+data_year[key[:2]][1]/100.0))-1)*100
            valid_data.append(preprocess(num, ave))
    if len(valid_data):
        return coefficient(len(valid_data)) * np.mean(valid_data), True
    else:
        return 0.0, False

