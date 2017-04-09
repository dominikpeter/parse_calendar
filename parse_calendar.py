# coding: utf-8

import bs4 as bs
import urllib.request
import pandas as pd
import numpy as np
import re
import datetime
import json
import argparse
from collections import defaultdict



def lookup_month(string):
    lookup = {'Januar': "01", 'Februar': "02", 'März': "03",
            'April': "04", 'Mai': "05", 'Juni': "06",
            'Juli': "07", 'August': "08", 'September': "09",
            'Oktober': "10", 'November': "11", 'Dezember': "12"}
    return lookup[string]


def get_geos(html):
    source = urllib.request.urlopen(html)
    soup = bs.BeautifulSoup(source, 'lxml')
    index = soup.select(".col-sm-4")

    geos = []
    [geos.append(i) for i in [re.findall("geo=\d+", str(i)) for i in index] if i]

    clean_geos = []
    [clean_geos.append(re.findall("\d+", item)) for sublist in geos for item in sublist]

    return np.unique(np.asarray(clean_geos))


def parse_html(html):
    source = urllib.request.urlopen(html)
    soup = bs.BeautifulSoup(source, 'lxml')

    title = re.sub("Feiertage ", "", re.sub("  "," ",soup.find('title').text))
    part = soup.select(".list-group-item")

    return title, part

def to_pandas(list):
    df = pd.DataFrame(columns=["day", "month","month_int","year","day","week","date","desc","state"])
    for i in list.keys():
        for data in list[i].keys():
            d = pd.DataFrame(list[i][data], columns=["day","month","month_int","year","day","week","date","desc"])
            d['state'] = str(i)
            df = pd.concat([df, d],  axis=0)
    return df

def clean_string(string):
    day_year = re.findall("\d+",string)[0:2]
    month = re.findall("\. \w+ ",string)[0][2:-1]
    kw = re.findall("\(\w+ \d+\)", string)[0][1:-1]
    i = re.search("\)", string).start()
    desc = re.sub(r'[^\u00C0-\u017Fa-zA-Z\.\s:]',' ', string[i+1:])
    day = re.findall("\d{4}\w{2}", string)[0][4:]
    month_int = lookup_month(month)
    date = str(day_year[1]) + '-' + str(month_int) + '-' + str(day_year[0])
    #formatted =  day_year[1] + "-" + month + "-" + day_year[0]
    return [day_year[0], month, month_int, day_year[1], day, kw, date, desc.rstrip()]


def get_state(string):
    clean = re.sub(r'[^\u00C0-\u017Fa-zA-Z\.\s:]',' ', string)
    i = re.search("\  ", clean).start()
    kanton = re.sub("Kanton ","", clean[0:i])
    typ = clean[i:]
    return str(kanton), str(typ)

def html_to_list(start, end, lang = 'de'):
    if lang not in ['de', 'fr', 'it']:
        raise ValueError("Language must be 'de', 'fr' or 'it'")

    geos = get_geos("https://www.feiertagskalender.ch/index.php?jahr=2017&geo=3056&klasse=3&hl=de&hidepast=1")

    # l = {}
    # for i in range(start,end):
    #     for geo in geos:
    #         try:
    #             url = "https://www.feiertagskalender.ch/index.php?geo="+str(geo)+"&klasse=3&jahr="+str(i)+"&hl="+str(lang)
    #             title, part = parse_html(url)
    #             title, typ = get_kanton(title)
    #             array = []
    #             [array.append(clean_string(i.text)) for i in part]
    #             l[title][i] = array
    #             print("Parsing... %s, Year: %s" % (str(title), str(i)))
    #         except:
    #             pass
    # return l

    l = defaultdict(lambda: defaultdict(list))
    try:
        for geo in geos:
            try:
                for i in range(start, end):
                    url = "https://www.feiertagskalender.ch/index.php?geo="+str(geo)+"&klasse=3&jahr="+str(i)+"&hl="+str(lang)
                    title, part = parse_html(url)
                    title, typ = get_state(title)
                    array = []
                    [array.append(clean_string(i.text)) for i in part]
                    l[title][i] = array
                    print("Parsing... %s, Year: %s" % (str(title), str(i)))
            except:
                pass
    except:
        pass

    return l


if __name__ == '__main__':

    now = datetime.datetime.now()

    parser = argparse.ArgumentParser(description="Parse Webcalendar",
                                     formatter_class=argparse.ArgumentDefaultsHelpFormatter)

    parser.add_argument('--from', type=int,
                        dest='startyear', default=now.year-10, help='Year to begin parsing')

    parser.add_argument('--to', type=int,
                        dest='endyear', default=now.year+10, help='Year to stop parsing')

    parser.add_argument('--output', type=str,
                        dest='output', default = 'all', help='Excel, JSON or CSV')

    parser.add_argument('--language', type=str,
                        dest='language', default = 'de', help='DE, FR or IT')

    args = parser.parse_args()

    print("parsing page...")

    l = html_to_list(args.startyear, args.endyear+1, args.language)

    print("writing file...")

    if args.output == 'all':
        df = to_pandas(l)
        with open('data.json', 'w') as outfile:
            json.dump(l, outfile)
        df.to_excel("data.xlsx", index=False)
        df.to_csv("data.csv", sep=";", index=False)
    elif args.output == 'excel':
        df = to_pandas(l)
        df.to_excel("data.xlsx", index=False)
    elif args.output == 'csv':
        df = to_pandas(l)
        df.to_csv("data.csv", sep=";", index=False, quotechar='"')
    else:
        with open('data.json', 'w') as outfile:
            json.dump(l, outfile)
