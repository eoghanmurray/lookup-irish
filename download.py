#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import time
from random import randint
import os
from bs4 import BeautifulSoup
import codecs
import requests

cum_sleep = 0

def get_definition_soup(word, dictionary, lang='ga', page_no=1):
    global cum_sleep
    if cum_sleep:
        # a little bit of backoff between requests
        time.sleep(cum_sleep + randint(1, 4))
        cum_sleep += 0.25

    headers = {
        'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36'
        ' (KHTML, like Gecko) Ubuntu Chromium/76.0.3809.100 Chrome/76'
        '.0.3809.100 Safari/537.36'
    }
    if dictionary == 'teanglann':
        href = 'https://www.teanglann.ie'
        if lang == 'ga':
            href += '/en/fgb/' + word
        elif lang == 'ga-fb':
            # a separate dictionary rather than a separate language
            href += '/en/fb/' + word
        elif lang == 'ga-gram':
            # grammar page
            href += '/en/gram/' + word
    elif dictionary == 'foclóir':
        href = 'https://www.focloir.ie'
        if lang == 'en':
            href += '/en/dictionary/ei/' + word
        else:
            href += f'/en/search/ei/adv?inlanguage=ga&page={page_no}&q=' + word
    local_dir = os.path.join(
        os.path.dirname(__file__),
        '.webcache',
        dictionary + '-' + lang
    )
    if page_no != 1:
        filename = f'{word}-{page_no}.html'
    else:
        filename = f'{word}.html'
    filename = filename.replace('/', '_')
    local_path = os.path.join(local_dir, filename)
    if not os.path.exists(local_dir):
        os.makedirs(local_dir)
    if os.path.exists(local_path):
        contents = codecs.open(local_path, 'r', encoding='utf8').read()
        soup = BeautifulSoup(contents, features='html5lib')
    else:
        print('Downloading', href)
        page = requests.get(href, headers=headers)
        soup = BeautifulSoup(page.text, features='html5lib')
        # writing the soup rather than raw response as it converts to utf8
        codecs.open(local_path, 'w', encoding='utf-8').write(str(soup))
    return soup


def bs4_get_text(node_or_string):
    if node_or_string is None:
        return ''
    elif hasattr(node_or_string, 'get_text'):
        return node_or_string.get_text()
    else:
        return node_or_string.string
