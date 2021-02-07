import pickle
import os.path as osp
import numpy as np
from utils import calc_score, time_convert
from tqdm import tqdm
year = "2020"
season = "4"
day = "2020-10-18"
company_ids_pkl = year+"_season"+season+"_company_ids.pkl"
with open(osp.join("cache", company_ids_pkl), "rb") as f:
    company_ids = pickle.load(f)
    # company_ids[i] = ("code", "company name")
all_season = []
for cid, name in tqdm(company_ids):
    href_pkl = cid+"_href_dic.pkl"
    with open(osp.join("cache", "company_href", day, href_pkl), "rb") as f:
        href_dic = pickle.load(f)
    # href_dic["manager_name"][0] = ("fund_id", "fund_name", "href", "serve time")
    data_pkl = year+"_season"+season+"_"+cid+"_data.pkl"
    f_name = osp.join("cache", "company_data", data_pkl)
    if not osp.isfile(f_name):
        continue
    with open(f_name, "rb") as f:
        data_dic = pickle.load(f)
    # data_dic["manager_name"]["fund_id"]['season_empty/year_empty'] = True/False
    # data_dic["manager_name"]["fund_id"]['season']['203']=(self_improvement, True, same kind improvement, hs300 improvement, same kind rank, True)
    #                                                      (self_improvement, True, 0,0,0,False)
    #                                                      (0, False, 0,0,0,0 False)
    # data_dic["manager_name"]["fund_id"]['year']['19']=(self increase, same kind increase, rank, True)/(0.0, 0.0, 0.0, False)
     
    for manager in href_dic.keys():
        funds = href_dic[manager]
        all_score = []
        all_time_dic = []
        for fund_id, _, _, serve_time in funds:
            if fund_id in data_dic[manager].keys():
                data = data_dic[manager][fund_id]
                if not data['season_empty']:
                    time_dic = time_convert(serve_time)
                    score, valid_score = calc_score(data['season'], data['year'], time_dic)
                    if valid_score:
                        for st in time_dic:
                            if not st in all_time_dic:
                                all_time_dic.append(st)
                        all_score.append(score)
        if len(all_score) >= 2 and len(all_time_dic) >= 24:
            all_season.append((name, manager, "http://fund.eastmoney.com/Company/f10/jjjl_"+cid+".html", np.mean(all_score)))
all_season.sort(key=lambda x:x[3], reverse=True)
for i in range(len(all_season)):
    print("%.20s %.10s %.3f %s"%(all_season[i][0], all_season[i][1], all_season[i][3], all_season[i][2]))
    if all_season[i][3] <= 0:
        break

