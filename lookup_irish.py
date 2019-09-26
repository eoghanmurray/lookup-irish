#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import sys
import argparse

from teanglann import get_teanglann_senses

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
arg(
    '--focloir-sort', '--foclóir-sort',
    help="Loose ordering of definitions according to importance of GA word on foclóir.ie",
    action='store_true'
)

if __name__ == '__main__':
    args = vars(parser.parse_args())
    if args:
        GA = args['irish-word']
        for sense in get_teanglann_senses(GA,
                                          verbose=args['verbose'],
                                          sort_by_foclóir=args['focloir_sort'],
                                          format='bash'):
            if sense['definitions']:
                print()
                print(sense['pos'], sense['gender'])
                if 'genitive-plural' in sense:
                    print(sense['genitive-plural'])
                if 'verbal-noun' in sense:
                    print(sense['verbal-noun'])
                print('\n'.join(sense['definitions']))
