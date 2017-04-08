
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

    title = soup.find('title').text
    part = soup.select(".list-group-item")

    return title, part


def html_to_list(start, end, lang = 'de'):
    if lang not in ['de', 'fr', 'it']:
        raise ValueError("Language must be 'de', 'fr' or 'it'")
    l = {}
    for i in range(start,end):
        for geo in geos:
            try:
                url = "https://www.feiertagskalender.ch/index.php?geo="+str(geo)+"&klasse=3&jahr="+str(i)+"&hl="+str(lang)
                title, part = parse_html(url)
                array = []
                [array.append(i.text) for i in part]
                l[title] = array
            except:
                pass
    return l

def main():
    geos = get_geos("https://www.feiertagskalender.ch/index.php?jahr=2017&geo=3056&klasse=3&hl=de&hidepast=1")

    now = datetime.datetime.now()
    start = now.year-10
    end = now.year+20

    l = html_to_list(start, end)

    with open('data.json', 'w') as outfile:
        json.dump(l, outfile)

if __name__ == '__main__':
    main()
