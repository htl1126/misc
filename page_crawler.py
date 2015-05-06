#!/usr/bin/env python
# -*- coding: utf-8 -*-

import sys
import locale
import codecs
import urllib
import json
from BeautifulSoup import BeautifulSoup
from urllib2 import urlopen, build_opener

# ref: http://xiaosu.blog.51cto.com/2914416/1340932
reload(sys)
sys.setdefaultencoding('utf8')

# ref: http://stackoverflow.com/questions/4545661/unicodedecodeerror
#      -when-redirecting-to-file
sys.stdout = codecs.getwriter(locale.getpreferredencoding())(sys.stdout)

#imcomplete
class text_classifier(object):
    def __init__(self):
        self.keyword_dict = {u'火鍋': [u'鍋', u'涮'],
                             u'中式': [u'牛肉麵', u'雞排', u'便當', u'鍋貼', u'炒麵', u'炒飯',
                                       u'燴飯', u'羹', u'米糕', u'割包', u'刈包', u'豆漿', u'蛋餅',
                                       u'豆花', u'麵線', u'貴州', u'黔', u'廣東', u'粵', u'福建',
                                       u'閩', u'浙江', u'浙', u'上海', u'山東', u'魯', u'東北',
                                       u'新疆', u'疆', u'蒙古', u'蒙', u'四川', u'川', u'湖南',
                                       u'湘', u'小籠', u'湯包', u'包子', u'魚翅', u'湯圓', u'菜飯',
                                       u'雲南', u'滇', u'緬'],
                             u'西式': [u'咖啡', u'早午餐', u'brunch', u'Brunch', u'帕尼尼',
                                       u'鬆餅', u'義大利麵', u'漢堡', u'三明治', u'海鮮飯',
                                       u'燉飯', u'薯條', u'吐司'],
                             u'日韓': [u'拉麵', u'丼', u'韓式泡菜', u'日式', u'韓式', u'壽司',
                                       u'生魚片', u'天婦羅'],
                             u'吃到飽': [u'Buffet', u'buffet', u'自助餐', u'吃到飽'],
                             u'東南亞': [u'河粉', u'越式', u'泰式', u'清真']}
    def get_text_category(self, text):
        for category in self.keyword_dict:
            for term in self.keyword_dict[category]:
                if term in text:
                    return category

class ptt_crawler(object):

    def remove_colon(self, s):
        if ':' in s:
            s = s.split(':')[-1]
            if u'：' in s:
                s = s.split(u'：')[-1]
        elif u'：' in s:
            s = s.split(u'：')[-1]
        return s

    def get_page(self, url):
        try:
            data = urlopen(url)
            return data.read()
        # ref: http://stackoverflow.com/questions/9265616/why-does-this-url-raise-badstatusline
        #      -with-httplib2-and-urllib2
        except:
            opener = build_opener()
            headers = {'User-Agent': ('Mozilla/5.0 (Windows NT 5.1;'
                                    ' rv:10.0.1) Gecko/20100101 Firefox/10.0.1')}
            opener.addheaders = headers.items()
            response = opener.open(url)
            return response.read()

    def get_title_list(self, data):
        title_lst = data.findAll('div', {'class': 'title'})
        return title_lst

    def extract_store_info(self, data, store_info):
        for line in data:
            if ((u'址：' in line or u'址:' in line or u'點：' in line or u'點：' in line)
                and u'網址' not in line):
                line = self.remove_colon(line.lstrip()).lstrip()
                store_info['address'] = line
                store_info['position'] = self.get_pos(line)
            elif u'話：' in line or u'話:' in line:
                line = self.remove_colon(line.lstrip()).lstrip()
                store_info['phone'] = line
            elif u'稱：' in line or u'稱:' in line:
                line = self.remove_colon(line.lstrip()).lstrip()
                store_info['name'] = line
            elif u'位：' in line or u'位:' in line:
                line = self.remove_colon(line.lstrip()).lstrip()
                store_info['price_range'] = line
            if (store_info['address'] and store_info['phone'] and store_info['name']
                and store_info['price_range']):
                break
        return store_info

    def get_store_info(self, data):
        store_info = {'name': None, 'url': None, 'phone': None, 'address': None,
                      'price_range': None, 'category': None, 'position': None}
        raw_text = data.text.split('\n')
        text = [raw_text_elem for raw_text_elem in raw_text if raw_text_elem != '']
        try:
            metadata = data.findAll(attrs={'name': 'description'})[0]['content'].split('\n')
            metadata = [meta for meta in metadata if meta != '']
            store_info = self.extract_store_info(metadata, store_info)
        except:
            pass
        store_info.update(self.extract_store_info(text, store_info))
        return store_info

    def get_pos(self, addr):
        # ref: http://stackoverflow.com/questions/16002213/
        #      getting-lat-and-long-from-google-maps-api-v3
        # WARNING: You may exceed your daily request quota
        params = {'sensor': 'false', 'address': addr}
        params = urllib.urlencode(params)
        data = urlopen('http://maps.googleapis.com/maps/api/geocode/json?{0}'.format(params)).read()
        addr = json.loads(data)
        try:
            location = addr['results'][0]['geometry']['location']
            return (location['lng'], location['lat'])
        except:
            return (None, None)

def main(url):
    crawler = ptt_crawler()
    classifier = text_classifier()
    root_page = crawler.get_page(url)
    root_page_data = BeautifulSoup(root_page)
    count = 0
    store_info = None
    end_reached = False
    while True:
        title_lst = crawler.get_title_list(root_page_data)
        for title in title_lst:
            if u'食記' in title.text and not title.text.startswith('Re:'):
                store_info = None
                # List of 'blackholes'
                if title.a['href'] in ['/bbs/Food/M.1376585048.A.EAA.html',
                                       '/bbs/Food/M.1345599928.A.C5E.html',
                                       '/bbs/Food/M.1335827893.A.E6C.html',
                                       '/bbs/Food/M.1334503278.A.239.html']:
                    continue
                if title.a['href'] == '/bbs/Food/M.1327665674.A.407.html':
                    print "Reached 2012/1/1"
                    end_reached = True
                    break
                sub_page_data = BeautifulSoup(crawler.get_page("https://www.ptt.cc/{0}"
                                                       .format(title.a['href'])))
                store_info = crawler.get_store_info(sub_page_data)
                # only consider restaurants in the Taiwan Island
                if store_info['position']:
                    if not (120.035699 < store_info['position'][0] < 122.007088
                            and 21.897077 < store_info['position'][1] < 25.299467):
                        continue
                if store_info:
                    store_info['url'] = "https://www.ptt.cc{0}".format(title.a['href'])
                    store_info['category'] = classifier.get_text_category(sub_page_data.text)
                    if not store_info['name']:
                        store_info['name'] = title.text.split(']')[-1]
                    for key in store_info:
                        print key, store_info[key]
                    count += 1
                    print
        if end_reached:
            break
        next_mark = root_page_data.findAll('a', {'class': 'btn wide'})[1]
        if not next_mark:
            break
        else:
            root_page_data = BeautifulSoup(crawler.get_page("https://www.ptt.cc/{0}"
                                                    .format(next_mark['href'])))
    print "Total {0} blogs extracted".format(count)

if __name__ == "__main__":
    url = 'https://www.ptt.cc/bbs/Food/index.html'
    main(url)
