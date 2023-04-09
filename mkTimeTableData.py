#!/usr/bin/env python3
# mkTimeTable.py
#
# 2023-03-31
# manontanto
'''
    目黒線の急行通過駅の時刻表DataをAWS用に用意する
'''

from datetime import datetime
import requests
import bs4

RR_NAME = '東急目黒線'
RR_CODE = '00000791'
STATIONS = {'00007857': "不動前",'00004800': "西小山", '00005276': "洗足",\
        '00000803': "奥沢", '00004200': "新丸子", '00002117': "元住吉"}
DT_FILE = "mg_timetable.txt"

def get_timetable(st_code, dt, updn):
    url = "https://transfer.navitime.biz/tokyu/pc/diagram/TrainDiagram?stCd=" +\
            st_code + "&rrCd=" + RR_CODE + "&updown=" + updn
    res = requests.get(url, timeout=6.5)
    res.raise_for_status()
    exp_soup = bs4.BeautifulSoup(res.text, 'html.parser')
    if dt == "平日":
        daytype = "weekday"
        BIAS = 0
    else:
        daytype = "saturday"
        BIAS = 20  # 40 for sunday, but same.

    if updn == "1":
        UD = "下り"
    else:
        UD = "上り"
    
    st_name = exp_soup.select('.nodeName')[0].string
    nowt = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    write_tbl(f'"{st_code}_{daytype}_{updn}": ' + "{" +\
            f'"title": "目黒線 {st_name}駅 {dt} {UD} 時刻表  取得日時: {nowt}"')
    hourdt = exp_soup.select(f'#diagram-table-{daytype} > dl > dt > div')
    timedt = exp_soup.select('dd')

    for i in range(0,20):
        h = int(hourdt[i * 2].string)
        write_tbl(f',{h}:[')
        t = [ ]
        for l in timedt[i + BIAS].select('.minute'):
            m = l.string
            t.append(int(m)) # t:[5,9,21,...]
        write_tbl(','.join(map(str, t)))
        write_tbl(']')
    write_tbl("},\n")

def write_tbl(d):
    with open(DT_FILE, 'a', encoding='utf-8') as f:
        f.write(d)

def main():
    write_tbl("{\n")
    for st in STATIONS:
        for d in ('平日', '土日祝'):
            for updn in ('0', '1'):
                get_timetable(st, d, updn)
                print('.', end='', flush=True)
    print('')
    write_tbl("}\n")

if __name__ == '__main__':
    main()
