#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import time
from random import randint
import os
from bs4 import BeautifulSoup
import codecs
import requests
from mechanize import Browser
from populate_google_sheet import get_sheet, get_range
from collections import defaultdict
from urllib.parse import quote
import re

cum_sleep = 0
br = None


def create_browsing_context():
    if not os.path.exists('corpas.focloir.ie.credentials'):
        # untried
        username = input('corpas.focloir.ie username:')
        password = input('corpas.focloir.ie password:')
        with open('corpas.focloir.ie.credentials', 'rw') as f:
            f.write(username + '\n' + password)
    with open('corpas.focloir.ie.credentials', 'r') as f:
        username, password = f.read().split('\n')
    br = Browser()
    br.set_handle_robots(False)
    #br.open('http://corpas.focloir.ie/')
    br.open('http://focloir.sketchengine.co.uk/')
    br.add_password('http://focloir.sketchengine.co.uk/auth/run.cgi/simple_search?home=1',
                    username,
                    password)
    for link in br.links():
        if link.text.lower().replace(' ', '') == 'login':
            br.follow_link(link)
    return br


def search_corpas(word_or_phrase, page_no=1):
    global br, cum_sleep
    local_dir = os.path.join(
        os.path.dirname(__file__),
        '.webcache',
        'corpas_focloir'
    )
    if page_no != 1:
        filename = f'{word_or_phrase}-{page_no}.html'
    else:
        filename = f'{word_or_phrase}.html'
    filename = filename.replace('/', '_')
    local_path = os.path.join(local_dir, filename)
    if not os.path.exists(local_dir):
        os.makedirs(local_dir)
    if os.path.exists(local_path):
        contents = codecs.open(local_path, 'r', encoding='utf8').read()
        soup = BeautifulSoup(contents, features='html5lib')
    else:
        if page_no == 2:
            # already have result from clicking '>> more'
            pass
        else:
            print('Searching', word_or_phrase)
            if cum_sleep:
                # a little bit of backoff between requests
                time.sleep(cum_sleep + randint(1, 4))
                cum_sleep += 0.25
            if not br:
                br = create_browsing_context()
            for form in br.forms():
                try:
                    form.find_control('iquery')
                except:
                    continue
                br.form = form  # select_form
                form['iquery'] = word_or_phrase
                br.submit()
                break
        soup = BeautifulSoup(br.response().read(), features='html5lib')
        # writing the soup rather than raw response as it converts to utf8
        codecs.open(local_path, 'w', encoding='utf-8').write(str(soup))
    return soup


def urlEncodeNonAscii(b):
    return re.sub('[\x80-\xFF]', lambda c: '%%%02x' % ord(c.group(0)), b)



def get_corpas_frequency(word_or_phrase):
    global br
    page_no = 1
    soup = search_corpas(word_or_phrase)
    hits = soup.find(id="toolbar-info").find(text="Hits: ")
    if not hits:
        return '', 0
    occurrences = defaultdict(int)
    while True:
        conclines = soup.find(id="conclines")
        for tr in conclines.find_all('tr'):
            coll = tr.find('b', class_="coll")
            if not coll:
                if tr['height'] != '10px':
                    print('Missing 1', word_or_phrase)
            else:
                occurrences[coll.string.strip().lower()] += 1
        more_link = conclines.find_next_sibling('a')
        if page_no >= 3:
            break
        if False and more_link.string.strip() == '>> More':
            page_no += 1
            for link in br.links():
                if link.url.endswith(';viewmode=sen'):
                    with open('corpas.focloir.ie.credentials', 'r') as f:
                        username, password = f.read().split('\n')
                    br.add_password('http://focloir.sketchengine.co.uk/auth/run.cgi/simple_search?home=1',
                                    username,
                                    password)
                    br.follow_link(link)
                    break
            else:
                import pdb; pdb.set_trace();
            soup = search_corpas(word_or_phrase, page_no)
        else:
            break

    maxv = None
    maxc = 0
    total = 0
    as_sorted = []
    for coll, c in occurrences.items():
        if c > maxc:
            maxc = c
            maxv = coll
        total += c
        as_sorted.append((c, coll))
    print(sorted(as_sorted, reverse=True)[:10])
    print(maxv)
    return maxv, int(hits.parent.find('strong').string)


if __name__ == '__main__':
    sheet = get_sheet()
    rows = get_range(
        sheet,
        '1kiZlZp8weyILstvtL0PfIQkQGzuG7oZfP8n_qkMFAWo',
        'periphrases!A1:B'
    )
    values = []
    cols = 'B', 'B'
    for n, row in enumerate(rows):
        if cols == ('C', 'D'):
            coll, f = get_corpas_frequency(row.GA)
            values.append([f, coll])
        elif cols == ('E', 'G'):
            if row.GA.startswith('cuir'):
                alt = row.GA.replace('cuir ', 'cur ')
                coll, f = get_corpas_frequency(alt)
                values.append([alt, f, coll])
            else:
                values.append(['','',''])
        elif cols == ('B', 'B'):
            from teanglann import get_teanglann_senses
            senses = get_teanglann_senses(row.GA)
            EN = '\n'.join([
                '\n'.join(sense['definitions'])
                for sense in senses if
                sense['definitions']
            ])
            values.append([EN])
    body = {
        'values': values,
    }
    sheet.values().update(
        spreadsheetId='1kiZlZp8weyILstvtL0PfIQkQGzuG7oZfP8n_qkMFAWo',
        range=f'periphrases!{cols[0]}2:{cols[1]}320',
        valueInputOption='RAW',
    body=body).execute()
