#!/usr/bin/env python3
# -*- coding: utf-8 -*-
from download import get_definition_soup, bs4_get_text


def get_foclóir_candidates(word):
    candidates = set()
    soup = get_definition_soup(word, 'foclóir', lang='ga', page_no=0)
    result_lists = soup.find_all(class_='result-list')
    if not result_lists:
        if 'No matches found.' in soup.get_text():
            return set()
    lis = result_lists[0].find_all('li')
    for result in lis:
        if result.find(class_='lang_ga').string.strip() == word:
            candidates.add(result.find(class_='lang_en').string.strip())
    return candidates


def foclóir_score_definition(en, ga):
    """
Estimate of how important a GA definition is in terms of the Englis
we count what percentage of translations use the word
between 0.0 and 1.0
lower is better
    """
    soup = get_definition_soup(en, 'foclóir', lang='en')
    senses = soup.find_all(class_="sense")
    found_count = 0
    lang_gas_count = 0
    for i, sense in enumerate(senses):
        lang_gas = sense.find_all(attrs={
            'xml:lang': 'ga',
            'class': 'cit_translation'
        })
        for lang_ga in lang_gas:
            lang_gas_count += 1
            if lang_ga.find(class_='quote', text=ga) or \
               ga in bs4_get_text(lang_ga.find(class_='quote')):
                found_count += 1
                break
    return 1 - (found_count / lang_gas_count)
