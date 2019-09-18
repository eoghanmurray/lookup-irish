#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import sys

from teanglann import get_teanglann_definition
from teanglann import assign_verbal_noun
import argparse

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
        if 'Verb' in PoS and 'ransitive' in PoS and ' ' not in GA:
            print('ag ' + assign_verbal_noun(GA))
        print(EN)
