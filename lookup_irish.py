#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import sys
import argparse

from teanglann import get_teanglann_definition
from teanglann import assign_verbal_noun, assign_plural_genitive
from irish_lang import format_declensions

parser = argparse.ArgumentParser(
    description="Lookup English definitions of Irish words from the wonderful "
    "https://www.teanglann.ie/ and https://www.focloir.ie/")

arg = parser.add_argument
arg(
    '-v', '--verbose',
    help='List of matching words from foclóir '
    'and full definition from teanglann',
    action='store_true')
arg(
    'irish-word',
    help="Irish word to look up")

if __name__ == '__main__':
    args = vars(parser.parse_args())
    if args:
        GA = args['irish-word']
        PoS, EN, Gender = get_teanglann_definition(GA, verbose=args['verbose'])
        print()
        print(PoS, Gender)
        if 'Noun' in PoS and ' ' not in GA:
            declensions = assign_plural_genitive(GA, html=True)
            print(format_declensions(declensions, format='bash'))
        if 'Verb' in PoS and 'ransitive' in PoS and ' ' not in GA:
            print('ag ' + assign_verbal_noun(GA))
        print(EN)
