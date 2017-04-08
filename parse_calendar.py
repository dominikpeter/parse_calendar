# coding: utf-8

import bs4 as bs
import urllib.request
import pandas as pd
import numpy as np
import re
import datetime
import json


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

    title = re.sub("  "," ",soup.find('title').text)
    part = soup.select(".list-group-item")

    return title, part


def clean_string(string):
    day_year = re.findall("\d+",string)[0:2]
    month = re.findall("\. \w+ ",string)[0][2:-1]
    kw = re.findall("\(\w+ \d+\)", string)[0][1:-1]
    i = re.search("\)", string).start()
    desc = re.sub(r'[^a-zA-Z\.\s:]',' ', string[i+1:])
    day = re.findall("\d{4}\w{2}", string)[0][4:]
    return [day_year[0], month, day_year[1], day, kw, desc.rstrip()]


def html_to_list(start, end, lang = 'de'):
    if lang not in ['de', 'fr', 'it']:
        raise ValueError("Language must be 'de', 'fr' or 'it'")

    geos = get_geos("https://www.feiertagskalender.ch/index.php?jahr=2017&geo=3056&klasse=3&hl=de&hidepast=1")

    l = {}
    for i in range(start,end):
        for geo in geos:
            try:
                url = "https://www.feiertagskalender.ch/index.php?geo="+str(geo)+"&klasse=3&jahr="+str(i)+"&hl="+str(lang)
                title, part = parse_html(url)
                array = []
                [array.append(clean_string(i.text)) for i in part]
                l[title] = array
                print("Parsing: "+str(title))
            except:
                pass
    return l

def main():
    now = datetime.datetime.now()
    start = now.year-10
    end = now.year+10

    print("parsing page...")

    l = html_to_list(start, end)

    print("writing json...")

    with open('data.json', 'w') as outfile:
        json.dump(l, outfile)

if __name__ == '__main__':
    main()
