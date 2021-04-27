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
from tqdm import tqdm
import pickle
from utils import get_HTML, get_name_list, gen_year_season_key, gen_year_key, convert_percent, calc_rank

def str_clean(str):
    return str.replace("\n", "").replace("\ue623", "")

def get_company_id(url):
    cur_year = time.strftime("%Y",time.localtime())
    cur_season = (int(time.strftime("%m",time.localtime()))-1)//3 + 1
    f_name = osp.join("cache", cur_year+"_season"+str(cur_season)+"_company_ids.pkl")
    if osp.isfile(f_name):
        with open(f_name, "rb") as f:
            cid = pickle.load(f)
    else:
        text = get_HTML(url)
        soup = BeautifulSoup(text,"html.parser")
        table=soup.findAll('table',{"class":"ttjj-table ttjj-table-hover common-sort-table"})
        table=table[0]
        trs = table.findAll('tr')
        trs = trs[1:]
        cid = []
        for tr in trs:
            cid.append((tr.findAll("a")[0]['href'].split("/")[-1].split(".")[0], tr.findAll("td")[1].get_text()))
        with open(f_name, "wb") as f:
            pickle.dump(cid, f)
    return cid

def get_href_dic(url):
    cur_t = time.strftime("%Y-%m-%d",time.localtime())
    os.makedirs(osp.join("cache","company_href",cur_t),exist_ok=True)
    f_name = osp.join("cache","company_href",cur_t,url.split("/")[-1][5:-5]+"_href_dic.pkl")
    if osp.isfile(f_name):
        with open(f_name, "rb") as f:
            dic = pickle.load(f)
    else:
        tb = pd.read_html(url,encoding='utf-8')
        text = get_HTML(url)
        soup = BeautifulSoup(text,"html.parser")
        name_list = get_name_list(soup)
        dic = collections.OrderedDict()
        table=soup.findAll('table',{"class":"ttjj-table ttjj-table-hover"})
        table=table[1:]
        for tb, name in zip(table, name_list):
            tr = tb.findAll('tr')
            tr = tr[1:]
            href = []
            for r in tr:
                href.append((str_clean(r.findAll('td')[0].get_text()), str_clean(r.findAll('td')[1].get_text()),\
                    r.findAll('a')[1]['href'], str_clean(r.findAll('td')[3].get_text())))
            dic[name] = href
        with open(f_name, "wb") as f:
            pickle.dump(dic, f)
    return dic

def grab_data(href_list, cid, name):
    dic = collections.OrderedDict()
    for fund, _, _, _ in href_list:
        fund_info = get_fund_info(fund, cid, name)
        dic[fund]=fund_info
    return dic

def get_fund_info(fund, cid, name):
    dic_a = collections.OrderedDict()
    dic_a["season_empty"] = True
    dic_a["year_empty"] = True
    url = "http://fundf10.eastmoney.com/FundArchivesDatas.aspx?type=jdndzf&code="+fund
    url2 = "http://fundf10.eastmoney.com/FundArchivesDatas.aspx?type=quarterzf&code="+fund
    url3 = "http://fundf10.eastmoney.com/FundArchivesDatas.aspx?type=yearzf&code="+fund
    no_except = False
    no_data = False
    while (not no_except):
        try:
            tb = pd.read_html(url, encoding='utf-8')
            tba = pd.read_html(url2, encoding='utf-8')
            tby = pd.read_html(url3, encoding='utf-8')
        except ValueError:
            print("No season data for fund" + fund)
            no_except = True
            no_data = True
        except (TimeoutError, urllib.error.URLError):
            print("Server no response, retry...")
        else:
            no_except = True
    if no_data:
        return dic_a
    tb=tb[0]
    tba=tba[0]
    tby=tby[0]
    years=len(tb)
    dic = collections.OrderedDict()
    dic_y = collections.OrderedDict()
    for i in range(years):
        year = tb["时间"][i]
        for j in range(4,0,-1):
            tr = str(j)+"季度涨幅"
            ysk = gen_year_season_key(year, j)
            if tb[tr][i] == "---":
                dic[ysk] = (0.0, False, 0.0, 0.0, 0.0, False)
            else:
                q_key = ysk[:2]+"年"+ysk[2]+"季度"
                if q_key in tba.keys() and not tba[q_key][1] == "---" and not tba[q_key][3] == "---":
                    dic[ysk] = (convert_percent(tb[tr][i]), True, convert_percent(tba[q_key][1]), convert_percent(tba[q_key][2]), calc_rank(tba[q_key][3]), True)
                else:
                    dic[ysk] = (convert_percent(tb[tr][i]), True, 0.0, 0.0, 0.0, False)
                dic_a["season_empty"] = False
        year += "度"
        if year in tby.keys():
            if tby[year][0] == "---" or tby[year][1] == "---" or tby[year][3] == "---":
                dic_y[gen_year_key(year)] = (0.0, 0.0, 0, False)
            else:
                dic_y[gen_year_key(year)] = (convert_percent(tby[year][0]), convert_percent(tby[year][1]), calc_rank(tby[year][3]), True)
                dic_a["year_empty"] = False
        else: #too early
            dic_y[gen_year_key(year)] = (0.0, 0.0, 0, False)
        # if tb["年度涨幅"][i] == "---" or tb["同类平均（年度）"][i] == "---" or tb["同类排名（年度）"][i] == "---":
        #     dic_y[gen_year_key(year)] = (0.0, 0.0, 0, False)
        # else:
        #     dic_y[gen_year_key(year)] = (convert_percent(tb["年度涨幅"][i]), convert_percent(tb["同类平均（年度）"][i]), calc_rank(tb["同类排名（年度）"][i]), True)
        #     dic_a["year_empty"] = False
    dic_a["season"] = dic
    dic_a["year"] = dic_y
    return dic_a

if __name__=="__main__":
    company_url = "http://fund.eastmoney.com/company/default.html"
    cur_year = time.strftime("%Y",time.localtime())
    cur_season = (int(time.strftime("%m",time.localtime()))-1)//3 + 1
    company_ids = get_company_id(company_url)
    os.makedirs("cache/company_data",exist_ok=True)
    for i, cid in enumerate(company_ids):
        print(i, cid[1])
        url = "http://fund.eastmoney.com/Company/f10/jjjl_"+ cid[0]+ ".html"
        dic_href = get_href_dic(url)
        # for i,j in dic.items():
        #     print(i,j)
        # dic[name][i]=(fund_id, fund_name, href)
        f_name = osp.join("cache", "company_data", cur_year+"_season"+str(cur_season)+"_"+url.split("/")[-1][5:-5]+"_data.pkl")
        if osp.isfile(f_name):
            with open(f_name, "rb") as f:
                dic = pickle.load(f)
        else:
            dic = collections.OrderedDict()
        name_list = list(dic_href.keys())
        exist_name_list = list(dic.keys())
        todo_name_list = [name for name in name_list if name not in exist_name_list]
        print("Names need to grab data:", todo_name_list)
        for name in tqdm(todo_name_list):
            # print("grab data for", name)
            dic_p = grab_data(dic_href[name], cid, name)
            dic[name] = dic_p
            with open(f_name, "wb") as f:
                pickle.dump(dic, f)
    print("done")
