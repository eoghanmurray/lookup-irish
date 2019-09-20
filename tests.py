#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from teanglann import get_teanglann_definition, assign_plural_genitive


if __name__ == '__main__':

    # TODO: these are not actually formal tests yet

    # adverb/preposition/adverb in a single entry
    get_teanglann_definition('anall')

    # make sure to pick up the 'Adjective'
    get_teanglann_definition('buan')

    # no adjective number defined in the main tab (TODO get from /fb/ tab)
    get_teanglann_definition('deas')

    # should have only one line with 'article'
    get_teanglann_definition('alt')

    # testing male/female:
    get_teanglann_definition('dóid')
    get_teanglann_definition('dogma')

    # should be nm4 not nm3 or multiple declensions:
    get_teanglann_definition('trumpa')

    # get back 'that'
    get_teanglann_definition('siúd')

    # has entry pointing to DUGA
    get_teanglann_definition('doic')

    # don't have 2 lines both saying 'knight'
    get_teanglann_definition('ridire')

    # no entry in fb (for noun declension)
    get_teanglann_definition('dóideog')

    # some monsters of definitions including verb & noun
    get_teanglann_definition('dóigh')
    get_teanglann_definition('súil')

    # has a non-translated '1. Dim. of BOTH.' in output
    get_teanglann_definition('bothán')

    # get a verbal noun
    # also an example with 5.(a), 5.(b) etc.
    # also an example with multiple class="trans" in 6.
    get_teanglann_definition('imeacht')

    # get more than 1 page of results (check if 'permission' is there)
    get_teanglann_definition('cead')

    # '(formal) application' to match with 'application'
    get_teanglann_definition('iarratas')

    # was not getting a1 -> adjective here
    # ensure don't get 'persist'
    # ('persistent' is in teanglann, 'persisting' is in focloir)
    get_teanglann_definition('leanúnach')

    # get '(proper) condition'
    get_teanglann_definition('bail')

    # get 'exact (measure, position)'
    # instead of 'exact (measure; exact position)'
    get_teanglann_definition('beacht')

    # some complex abbreviations here
    get_teanglann_definition('dírigh')

    # get 'volunteer (military)'
    get_teanglann_definition('óglach')

    # get 'warp (textiles)'
    get_teanglann_definition('dlúth')

    # TODO: get 'to illustrate'
    get_teanglann_definition('maisigh')

    # 'na gleonna' for plural
    assign_plural_genitive('gleo')

    # verb intransitive + transitive,
    # with extra entry with intransitive verb only
    # expecting to get 'Verb - Transitive & Intransitive' back
    get_teanglann_definition('lonnaigh')[0]

    # not getting 'cream'
    get_teanglann_definition('uachtar')

    # different senses king/forearm with nf4/nm4
    get_teanglann_definition('rí')

    # noun, but adjective there also (not currently picking that up
    get_teanglann_definition('indiach')

    # an tEorpach/na hEorpaigh & an Eorpaigh/na nEorpach
    get_teanglann_definition('indiach')

    # an t-ionsaí/an ionsaithe & na hionsaithe/na n-ionsaithe
    get_teanglann_definition('ionsaí')
