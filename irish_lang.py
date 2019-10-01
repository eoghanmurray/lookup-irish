#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from colorama import Fore, Back, Style


def eclipse(word, html=False):
    """
http://www.nualeargais.ie/gnag/gram.htm?1dekl.htm
    """
    initial = word[0]
    eclipses = {
        'b': 'm',
        'c': 'g',
        'd': 'n',
        'f': 'bh',
        'g': 'n',
        'p': 'b',
        't': 'd',
    }
    if initial in eclipses:
        if html:
            return '<i>' + eclipses[initial] + '</i>' + word
        else:
            return eclipses[initial] + word
    return word


def lenite(word, html=False):
    """
http://www.nualeargais.ie/gnag/lenition.htm
    """
    if word[0] in 'bcdfgmpst':
        if html:
            return word[0] + '<i>h</i>' + word[1:]
        else:
            return word[0] + 'h' + word[1:]
    return word


def apply_article(word, gender, part_of_speech, html=True):
    """
http://nualeargais.ie/gnag/artikel.htm
    """
    preceding_s = word[0] == 's'
    preceding_a_vowel = word[0] in 'aeiouáéíóú'
    preceding_upcase_vowel = word[0] in 'AEIOUÁÉÍÓÚ'
    preceding_a_vowel = preceding_a_vowel or preceding_upcase_vowel
    preceding_dt = word[0] in 'dt'
    preceding_a_consonant = \
        not preceding_s and \
        not preceding_a_vowel and \
        not preceding_dt
    nf = gender.startswith('nf')
    nm = gender.startswith('nm')
    nominative = 'nominative' in part_of_speech
    genitive = 'genitive' in part_of_speech
    if 'plural' in part_of_speech:
        ret = 'na '
    elif genitive:
        if nf:
            ret = '<i>na</i> '
        else:
            # although this shows that it's a genitive
            # of a masculine noun, the .weak class
            # here allows us to turn off masculine highlighting,
            # from the pov that a singular article is 'the norm'
            # i.e. what you'd expect from the nominative
            ret = '<i class="weak">an</i> '
    else:
        ret = 'an '
    if 'plural' in part_of_speech:
        # no html needed here as same in both genders
        if preceding_s:
            ret += word
        elif preceding_a_vowel:
            if genitive:
                if preceding_upcase_vowel:
                    ret += 'n' + word
                else:
                    ret += 'n-' + word
            else:
                ret += 'h' + word
        elif genitive:
            ret += eclipse(word, html=False)
        else:
            ret += word
    else:
        if preceding_dt:
            ret += word
        else:
            if preceding_s and \
               word[1].lower() in 'aeiouáéíóúlnr' and (
                    (nominative and nf) or
                    (genitive and nm)):
                ret += '<i>t</i>' + word
            elif (preceding_a_vowel and
                  nf and genitive):
                ret += '<i>h</i>' + word
            elif (preceding_a_vowel and
                  nm and nominative):
                if preceding_upcase_vowel:
                    ret += '<i>t</i>' + word
                else:
                    ret += '<i>t</i>-' + word
            elif preceding_a_consonant and (
                    (nm and genitive) or
                    (nf and nominative)):
                ret += lenite(word, html=True)
            else:
                ret += word
    if not html:
        ret = ret.replace('<i class="weak">', '')
        return ret.replace('<i>', '').replace('</i>', '')
    return ret


def apply_gender_hints(singular, actual_gender, wd=None):

    # numbers show confidence i.e. count(nf) / (count(nf) + count(nm))
    # data collected in noun-declensions.json

    strong_feminine_endings = {

# 'cht' masculine on short words!
        'cht': 0.91,

# 'irt' more nf2 than nf3 as would be indicated by
# http://nualeargais.ie/foghlaim/nouns.php
        'irt': 0.97,

# 'úil' 6 in top 6,500 again more nf2 and only one nf3 contrary to nualeargais
        'úil': 1.0,

# 'int': nualeargais has this as úint/áint
# but we've also got tairiscint/ léirthuiscint/ míthuiscint
# which are nf3 in the top 6000
# with one mismatch: sáirsint nm4
        'int': 0.93,

# Earcail/Uncail are masculine, again lots of nf2/nf5/nf, and only 2 nf3
# not using, as too easily confused with ['áil', 'íl', 'aíl'] endings
# which could be m/f http://nualeargais.ie/gnag/3dekl.htm
        # 'ail': 0.88,

# following supposed to be nf2 according to nualeargais
        'lann': 0.89,  # exceptions: nm1 salann, nm1 anlann
        'eog': 1.0,
        'óg': 0.98,  # exception: nm4 dallamullóg

# https://thegeekygaeilgeoir.wordpress.com/2017/08/28/making-sense-of-irish-gender/
        #'lis' TODO
        #'chan' TODO
    }

    # http://nualeargais.ie/foghlaim/nouns.php?teanga= says
    # "abstract nouns ending in -e, -í are likely to be f4
    # because of the high proportion of nm here, there's no point
    # in highlighting these endings as feminine (plus they are too short)
    # they are all declension 4 though, with only one nf5: 'leite'
    declension_4_endings = {
        'e': 0.41,  # f: 107, m: 152
        'í': 0.18,  # f: 15, m: 69
    }

    strong_masculine_endings = {
        'ín': 0.9,  # diminutive, turns feminine words masculine

        # professions:
        'éir': 0.74,  # 'éir' exceptions are short:
                      # nf2: réir/spéir/comhréir/cléir/mistéir
                      # nf5: céir
        'eoir': 0.93,  # ditto nf2:deoir nf5:beoir/treoir/míthreoir
        'óir': 0.93,  # ditto nf2:glóir nf3:tóir/onóir/éagóir/altóir/seanmóir
        'úir': 1.0,
        'aeir': 1.0,

# https://thegeekygaeilgeoir.wordpress.com/2017/08/28/making-sense-of-irish-gender/
        #'eir'  # TODO
        #'án'  # TODO
        #'oir'  # TODO
        #'uir'  # TODO
        #'ste'  # TODO (exception: timpiste)
    }
    exception_explanation = None
    for ending in strong_feminine_endings:
        if singular.endswith(ending):
            a, b = singular[:-len(ending)], singular[-len(ending):]
            if actual_gender[:2] == 'nf':
                wd['nominative singular'] = a + '<i>' + b + '</i>'
            else:
                wd['nominative singular'] = a + '<u>' + b + '</u>'
            return
    for ending in strong_masculine_endings:
        if singular.endswith(ending):
            a, b = singular[:-len(ending)], singular[-len(ending):]
            if actual_gender[:2] == 'nm':
                wd['nominative singular'] = a + '<i>' + b + '</i>'
            else:
                wd['nominative singular'] = a + '<u>' + b + '</u>'
            return

    pos = -2
    vowels = 'aáeéiíoóuú'
    if singular[-1] in vowels:
        # probably m4/f4
        # Q: with a final vowel, is there a pattern according
        # to the penultimate slender/broad consonent?
        # A: no
        # slender: {'nf': 68, 'nm': 96}
        # broad: {'nf': 34, 'nm': 180}
        return

    # http://nualeargais.ie/gnag/1dekl.htm
    # nm1 'end in broad consonants'
    # http://nualeargais.ie/gnag/2dekl.htm
    # nf1 'end in slender or broad consonants'
    # a slender consonant is 11x more likely to be feminine
    # slender: {'nf': 316, 'nm': 28} (count of nouns that get
    #     this far out of the 6,500)
    # broad: {'nf': 99, 'nm': 864}
    while (abs(pos) < len(singular) and
           singular[pos] not in vowels):
        pos -= 1
    if abs(pos) > len(singular) or (
            abs(pos) == len(singular) and singular[pos] not in vowels):
        print(f"Can't determine broad/slender: {singular}")
        return
    # not highlighting broad as a masculine signifier
    # as although there are 8.7 times as many, that is still 99 exceptions
    slender_vowels = 'eiéí'
    if singular[pos] in slender_vowels:
        # slender consonant is determined by slender vowel
        a, b, c = singular[:pos], singular[pos], singular[pos + 1:]
        if actual_gender[:2] != 'nf':
            wd['nominative singular'] = a + '<u>' + b + '</u>' + c
        else:
            wd['nominative singular'] = a + '<i>' + b + '</i>' + c


def format_declensions(decl, gender=None, format='html'):
    if gender is None:
        if 'gender' not in decl:
            raise Exception('Need a gender set to properly set declensions')
        gender = decl['gender']
    middle = gender
    if False and 'nominative plural' in decl:
        is_weak_plural = decl['plural strength'] == 'weak'
        is_strong_plural = decl['plural strength'] == 'strong'
        # http://nualeargais.ie/gnag/subst2.htm#oben
        # weak plural is almost exclusively present in
        # the 1st + 2nd declension, but is quite common.
        if len(gender) > 2 and (
                (is_weak_plural and gender[-1] not in ['1', '2']) or
                (is_strong_plural and gender[-1] in ['1', '2'])):
                middle += ' <u class="nm12">but</u>'
        if is_weak_plural:
            middle += ' weak plural'
        elif is_strong_plural:
            middle += ' strong plural'
    word = decl['nominative singular'][3:]  # remove 'an '
    if 'nominative singular' in decl and word in [
            # http://nualeargais.ie/gnag/0dekl.htm
            'bean', 'deirfiúr', 'siúr', 'dia', 'lá', 'leaba', 'mí', 'olann', 'talamh',
            # https://en.wikipedia.org/wiki/Irish_declension
            'deoch', 'muir', 'olann', 'teach',
    ]:
        #if len(gender) != 2:
        #    print(f'CHECK irregular:', gender, decl['nominative singular'])
        middle += ', <u class="irr">irregular</u>'

    if format == 'html':
        middle = '<div class="decl">' + middle + '</div>'
    elif format == 'bash':
        middle = '\n'
    r = ''
    if ('nominative singular' in decl and
          'genitive singular' in decl):
        r += decl['nominative singular']
        if 'nominative plural' in decl:
            r += '/' + decl['nominative plural']
        r += middle
        r += decl['genitive singular']
        if 'genitive plural' in decl:
            r += '/' + decl['genitive plural']
    if not r:
        pass
    elif format == 'html':
        r = f'<div class="{gender[:2]} d{gender[2:]}">' + r + '</div>'
    elif format == 'bash':
        r = r.replace('<u>', Back.RED)
        r = r.replace('</u>', Style.RESET_ALL)
        if 'nf' in gender:
            r = r.replace('<i>', Fore.MAGENTA)
        else:
            r = r.replace('<i>', Fore.BLUE)
            r = r.replace('<i class="weak">', Back.BLACK)
        r = r.replace('</i>', Style.RESET_ALL)
    return r
