#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import sys

from teanglann import get_teanglann_definition
from teanglann import assign_verbal_noun


if __name__ == '__main__':
    if len(sys.argv) > 1:
        GA = sys.argv[-1]
        PoS, EN, Gender = get_teanglann_definition(GA, verbose=True)
        print()
        print(PoS, Gender)
        if 'Verb' in PoS and 'ransitive' in PoS and ' ' not in GA:
            print('ag ' + assign_verbal_noun(GA))
        print(EN)
