#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import sys

from teanglann import get_teanglann_definition, assign_plural_genitive
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
    elif False:
        # adverb/preposition/adverb in a single entry
        get_teanglann_definition('anall')
    elif False:
        # make sure to pick up the 'Adjective'
        get_teanglann_definition('buan')
    elif False:
        # no adjective number defined in the main tab (TODO get from /fb/ tab)
        get_teanglann_definition('deas')
    elif False:
        # should have only one line with 'article'
        get_teanglann_definition('alt')
    elif False:
        # testing male/female:
        get_teanglann_definition('dóid')
        get_teanglann_definition('dogma')
    elif False:
        # should be nm4 not nm3 or multiple declensions:
        get_teanglann_definition('trumpa')
    elif False:
        # get back 'that'
        get_teanglann_definition('siúd')
    elif False:
        # has entry pointing to DUGA
        get_teanglann_definition('doic')
    elif False:
        # don't have 2 lines both saying 'knight'
        get_teanglann_definition('ridire')
    elif False:
        # no entry in fb (for noun declension)
        get_teanglann_definition('dóideog')
    elif False:
        # some monsters of definitions including verb & noun
        get_teanglann_definition('dóigh')
        get_teanglann_definition('súil')
    elif False:
        # has a non-translated '1. Dim. of BOTH.' in output
        get_teanglann_definition('bothán')
    elif False:
        # get a verbal noun
        # also an example with 5.(a), 5.(b) etc.
        # also an example with multiple class="trans" in 6.
        get_teanglann_definition('imeacht')
    elif False:
        # get more than 1 page of results (check if 'permission' is there)
        get_teanglann_definition('cead')
    elif False:
        # '(formal) application' to match with 'application'
        get_teanglann_definition('iarratas')
    elif False:
        # was not getting a1 -> adjective here
        # ensure don't get 'persist'
        # ('persistent' is in teanglann, 'persisting' is in focloir)
        get_teanglann_definition('leanúnach')
        # get '(proper) condition'
        get_teanglann_definition('bail')
        # get 'exact (measure, position)'
        # instead of 'exact (measure; exact position)'
        get_teanglann_definition('beacht')
    elif False:
        # some complex abbreviations here
        get_teanglann_definition('dírigh')
    elif False:
        # get 'volunteer (military)'
        get_teanglann_definition('óglach')
        # get 'warp (textiles)'
        get_teanglann_definition('dlúth')
    elif False:
        # TODO: get 'to illustrate'
        get_teanglann_definition('maisigh')
    elif False:
        # 'na gleonna' for plural
        assign_plural_genitive('gleo')
    elif False:
        # verb intransitive + transitive,
        # with extra entry with intransitive verb only
        # expecting to get 'Verb - Transitive & Intransitive' back
        print(get_teanglann_definition('lonnaigh')[0])
    else:
        # not getting 'cream'
        get_teanglann_definition('uachtar')
