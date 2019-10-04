#!/usr/bin/env python3
# -*- coding: utf-8 -*-
from download import get_definition_soup, bs4_get_text
from random import shuffle
import re
import sys
from colorama import Fore, Back, Style
from collections import OrderedDict
from itertools import permutations
from copy import copy

from irish_lang import apply_gender_hints, apply_article
from irish_lang import format_declensions
from irish_lang import lenite, eclipse
from focloir import get_foclóir_candidates, foclóir_score_definition

HAIR_SLASH = ' / '  # unicode, equivalent to '&hairsp;/&hairsp;'


def get_teanglann_senses(
        word, return_raw=False, sort_by_foclóir=False, verbose=False,
        return_counts=False,
        format='html'):

    candidates = get_foclóir_candidates(word)
    candidates = [c.lower() for c in candidates]
    foclóir_candidates = candidates[:]
    candidates = [re.sub(r'ise$', r'ize', c) for c in candidates]
    if verbose:
        print()
        print(f'{Back.YELLOW}{Fore.BLACK}{word}'
              f'{Style.RESET_ALL} foclóir:', candidates)

    senses = [{
        'definitions': [],
        'raw_definitions': [],
    }]

    for subentries, subentry_labels in get_teanglann_subentries(word):
        first_line = subentries[0]
        gender = None
        genitive_vn = None
        types = OrderedDict()  # using as ordered set
        if first_line.find(title="feminine") and \
           first_line.find(title="masculine"):
            # 'cara' has '(Var:feminine)' at the end
            for g in [r'masculine', r'feminine']:
                r = re.compile(r'var(?:iant)*:\s*' + g, re.I)
                if g not in re.sub(r, '', bs4_get_text(first_line)):
                    first_line.find(title=g).extract()

        # TODO: should look at first_line only up to opening parenthesis

        if first_line.find(title="pronoun"):
            # sé/sí are not nouns
            types['Pronoun'] = True
        elif first_line.find(title="feminine") and \
           first_line.find(title="masculine") and \
           word != 'talamh':
            # 'thar': has 'thairis (m) thairsti (f)' and is not a noun
            pass
        elif (first_line.find(title="feminine") or
              first_line.find(title="masculine")):
            types['Noun'] = True
            gender = assign_gender_declension(word, first_line)
            plural_genitive = sense_assign_plural_genitive(
                        word, first_line, gender
                    )
        if first_line.find(title="adverb"):
            types['Adverb'] = True
        if first_line.find(title="preposition"):
            types['Preposition'] = True
        if first_line.find(title="adjective"):
            types['Adjective'] = True
            gender_a = 'a'
            dec = first_line.find(title="adjective").next_sibling
            # to check: think it only goes up to a3
            if dec and dec.strip().strip('.') in ['1', '2', '3', '4']:
                gender_a += dec.strip().strip('.')
            else:
                soup_fb = get_definition_soup(word, 'teanglann', lang='ga-fb')
                entry_fb = soup_fb.find(class_='entry')
                if soup_fb.find(text='aid3'):
                    gender_a += '3'
                elif soup_fb.find(text='aid2'):
                    gender_a += '2'
                elif soup_fb.find(text='aid1'):
                    gender_a += '1'
                elif not soup_fb.find(text='aid'):
                    # 'thar' spurious adj. in following:
                    # ' of <span title="adjective">a</span> general nature'
                    del types['Adjective']
                    gender_a = None
            if gender_a:
                if not gender:
                    gender = gender_a
                else:
                    gender += '\n' + gender_a
        if first_line.find(title="transitive verb"):
            if 'Verb' not in types:
                types['Verb'] = OrderedDict()
            types['Verb']['Transitive'] = True
        if first_line.find(title="intransitive verb") or \
           first_line.find(title="and intransitive"):
            if 'Verb' not in types:
                types['Verb'] = OrderedDict()
            types['Verb']['Intransitive'] = True
        if first_line.find(title="conjunction"):
            types['Conjugation'] = True
        if first_line.find(title="prefix"):
            types['Prefix'] = True
        if 'Verb' in types and 'Noun' in types:
            del types['Noun']
            gender = None

        type_sig = ' & '.join(types.keys())
        sense = senses[-1]
        if ('gender' in sense and
            sense['gender'] != gender) or \
            ('type-sig' in sense and
             sense['type-sig'] != type_sig):
            senses.append({
                'definitions': [],
                'raw_definitions': [],
            })
            sense = senses[-1]
        sense['gender'] = gender
        sense['type-sig'] = type_sig
        sense['types'] = types
        pos = join_parts_of_speech(types)
        sense['pos'] = pos

        for subentry in subentries:
            raw_text = clean_text(' '.join(subentry.stripped_strings), word)
            if raw_text.startswith('verbal noun') and ' of ' in raw_text:
                verb_name = raw_text.split(' of ', 1)[1]
                verb_name = verb_name.strip().rstrip(' 123456789')
                if verb_name == word:
                    types['Verbal Noun'] = True
                else:
                    types['Verbal Noun'] = ' of ' + verb_name

        if verbose:
            print()
            print(f'{Back.RED}{word}'
                  f'{Style.RESET_ALL}', join_parts_of_speech(types), gender)
        for label, subentry in zip(subentry_labels, subentries):
            transs = subentry.find_all(class_='trans')
            if len(transs) > 1 and (
                    (bs4_get_text(transs[0]).lstrip().startswith('(') and
                     bs4_get_text(transs[0]).rstrip().endswith(')'))
                    or
                    (
                        bs4_get_text(
                            transs[0].previous_sibling
                        ).rstrip().endswith('(')
                        and bs4_get_text(
                            transs[0].next_sibling
                        ).lstrip().startswith(')')
                    )
            ):
                transs = transs[1:]
            raw_text = clean_text(' '.join(subentry.stripped_strings), word)
            first_trans_extra = ''
            if transs and transs[0].previous_sibling and \
               transs[0].previous_sibling.string and \
               transs[0].previous_sibling.string.strip() == ':' and \
               transs[0].previous_sibling.previous_sibling and \
               transs[0].previous_sibling.previous_sibling.find(title=True):
                # important qualifiers like military: textile: etc.
                first_trans_extra = ' (' + transs[0].previous_sibling.\
                    previous_sibling.find(title=True)['title'].lower() + ')'
            for trans in transs:
                trans.insert_before(Fore.YELLOW)
                trans.insert_after(Style.RESET_ALL)
            formatted_text = ' '.join(subentry.stripped_strings)
            formatted_text = clean_text(formatted_text, word)
            for example in subentry.find_all(class_='example'):
                example_text = clean_text(example.get_text(), word)
                formatted_text = formatted_text.replace(
                    example_text,
                    f'\n    {example_text}'
                )
            if not transs:
                if verbose:
                    print(f'{label}[{formatted_text}]')
            else:
                trans_text = clean_text(transs[0].get_text(), word)
                maybe_to = ''
                if 'Verb' in types:
                    maybe_to = 'to '
                trans_words = re.split('[,;] *', trans_text)
                defn_words = [
                    tgw for tgw in trans_words
                    if re.sub(r'ise$', r'ize',
                              re.sub(r'\s*\(.*?\)\s*', '', tgw))
                    in candidates
                ]
                if sort_by_foclóir and defn_words:
                    foclóir_scores = []
                    for defn_word in defn_words:
                        fsd = foclóir_score_definition(defn_word, word)
                        foclóir_scores.append((fsd, defn_word))
                    foclóir_scores.sort()
                    foclóir_min_score = min(foclóir_scores)[0]
                    if False:
                        # debug
                        defn = HAIR_SLASH.join([
                            fs[1] + f' ({fs[0]})'
                            for fs in foclóir_scores
                        ])
                    else:
                        defn = HAIR_SLASH.join([fs[1] for fs in foclóir_scores])
                else:
                    defn = HAIR_SLASH.join(defn_words)
                if len(transs) > 1:
                    formatted_text = f'X{len(transs)} {formatted_text}'
                sense['raw_definitions'].append(f'[{trans_text}]')
                definition = None
                if defn:
                    definition = maybe_to + defn + first_trans_extra
                    if verbose:
                        print(f'{label}{Fore.GREEN}{definition}'
                              f'{Style.RESET_ALL} [{formatted_text}]')
                else:
                    for fcw in candidates:
                        if all(tgw.startswith(fcw + ' ')
                               for tgw in trans_words):
                            rest = ' (' + ', '.join(
                                tgw[len(fcw) + 1:] for tgw in trans_words
                            ) + ')'
                            if verbose:
                                print(f'{label}{Fore.GREEN}{maybe_to}{fcw}'
                                      f'{Fore.MAGENTA}{rest}'
                                      f'{Style.RESET_ALL} [{formatted_text}]')
                            definition = maybe_to + fcw + rest
                            break
                        elif all(tgw.endswith(' ' + fcw)
                                 for tgw in trans_words):
                            rest = '(' + ', '.join(
                                tgw[:-len(fcw) - 1] for tgw in trans_words
                            ) + ') '
                            if verbose:
                                print(f'{label}{Fore.GREEN}{maybe_to}'
                                      f'{Fore.MAGENTA}{rest}{Fore.GREEN}{fcw}'
                                      f'{Style.RESET_ALL} [{formatted_text}]')
                            definition = maybe_to + rest + fcw
                            break
                    else:  # no break - for
                        if verbose:
                            print(f'{label}[{formatted_text}]')

                if definition and definition not in sense['definitions']:
                    # could filter/rearrange existing definitions here
                    if 'Prefix' in types:
                        definition = definition + ' (as prefix)'
                    if sort_by_foclóir:
                        if 'Verb' in types:
                            # put all verbs at the end (could do better)
                            sense['definitions'].append((
                                foclóir_min_score + 10,
                                definition
                            ))
                        else:
                            sense['definitions'].append(
                                (foclóir_min_score, definition)
                            )
                    else:
                        sense['definitions'].append(definition)


            if 'Verb' in types:
                vn = assign_verbal_noun(word)
                if sense.get('verbal-noun', vn) != vn:
                    manual_debug()
                if vn:
                    # http://nualeargais.ie/gnag/verbnom1.htm
                    vnvts = [
                        'ag ' + vn,
                        'a ' + lenite(vn),
                        'le ' + vn,
                        'do mo ' + lenite(vn),
                        'do do ' + lenite(vn),
                        'á ' + vn,
                        'á ' + lenite(vn),
                        'dár ' + eclipse(vn),
                        'do bhur ' + eclipse(vn),
                        'á ' + eclipse(vn),
                    ]
                    vn_examples = []
                    for vt in vnvts:
                        if vt in raw_text:
                            vn_examples.append((raw_text.count(vt), vt))
                    if vn_examples:
                        vn_examples.sort(reverse=True)
                        sense['verbal-noun-examples'] = [vte[1] for vte in vn_examples]
                    else:
                        sense['verbal-noun-examples'] = ['ag ' + vn]
                sense['verbal-noun'] = vn

            if 'Noun' in types:
                gp = format_declensions(word, plural_genitive, gender, format)
                if sense.get('genitive-plural', gp) != gp:
                    senses.append({
                        'definitions': [],
                        'raw_definitions': [],
                        'gender': gender,
                        'type-sig': type_sig,
                        'types': types.copy(),
                        'pos': pos,
                    })
                    sense = senses[-1]
                sense['genitive-plural'] = gp
                sense['genitive-plural-raw'] = plural_genitive


    if sort_by_foclóir:
        for sense in senses:
            sense['definitions'].sort()
            if sense['definitions']:
                sense['score'] = min([d[0] for d in sense['definitions']])
                sense['definitions'] = [d[1] for d in sense['definitions']]
            else:
                sense['score'] = 1.1
        senses.sort(key=lambda x: x['score'])

    if not senses[-1]['raw_definitions']:
        senses = senses[:-1]

    if return_counts:
        return (senses, sum(len(s['raw_definitions']) for s in senses),
                len(candidates), foclóir_candidates)
    else:
        return senses


def get_teanglann_subentries(word):
    soup = get_definition_soup(word, 'teanglann', lang='ga')

    for entry in soup.find_all(class_='entry'):

        expand_abbreviations(entry)
        if not entry.text.strip().lower().startswith(word.lower()):
            # https://www.teanglann.ie/en/fgb/i%20measc
            # gives results for 'imeasc' not 'i measc'
            continue

        subentries = [soup.new_tag('div')]
        subentry_labels = ['']  # first line, may contain a 'main' entry
        n = 1
        nxs = 'abcdefghijklmnopqrstuvwxyz'
        nxi = 0
        for node in entry.contents[:]:
            node_text = bs4_get_text(node)
            if f'{n}.' in re.sub(rf'adjective\s*{1}.', '', node_text):
                as_subnode = node.find(text=re.compile(rf'\s+{n}.\s+'))
                if as_subnode:
                    rev = []
                    for r in as_subnode.previous_siblings:
                        rev.append(r)
                    for r in reversed(rev):
                        subentries[-1].append(r)
                pre, post = node_text.rsplit(f'{n}.', 1)
                if pre.strip():
                    subentries[-1].append(pre.strip())
                subentries.append(soup.new_tag('div'))
                subentry_labels.append(f'{n}. ')
                nxi = 0
                if post.strip():
                    subentries[-1].append(post.strip())
                if as_subnode:
                    for r in as_subnode.next_siblings:
                        subentries[-1].append(r)
                n += 1
            elif (len(subentries) > 1  # we've got at least a '1.' already
                  and (
                      f'({nxs[nxi]})' in node_text
                      or (
                          f'{nxs[nxi]}' == node_text.strip() and
                          node.next_sibling.string.strip() == ')' and
                          subentries[-1].get_text().strip().endswith('(')
                      ))):
                pre, post = node_text.split(f'{nxs[nxi]}', 1)
                if pre.strip().rstrip('('):
                    subentries[-1].append(pre.strip())
                if subentries[-1].get_text().strip().rstrip('('):
                    subentries.append(soup.new_tag('div'))
                    subentry_labels.append(f'{n-1}.({nxs[nxi]}) ')
                else:
                    subentry_labels[-1] = f'{n-1}.({nxs[nxi]}) '
                if post.strip().lstrip(')'):
                    subentries[-1].append(post.strip())
                nxi += 1
            else:
                subentries[-1].append(node)
        yield subentries, subentry_labels


def assign_gender_declension(noun, first_line):
    soup_fb = get_definition_soup(noun, 'teanglann', lang='ga-fb')
    entry_fb = soup_fb.find(class_='entry')
    if first_line.find(title="feminine"):
        gender = 'nf'
        k_lookup = 'bain'
    elif first_line.find(title="masculine"):
        gender = 'nm'
        k_lookup = 'fir'
    else:
        return None
    search_entry = entry_fb
    if entry_fb:
        for subentry in entry_fb.find_all(class_='subentry'):
            if bs4_get_text(subentry.find(class_='headword')) == noun:
                # https://www.teanglann.ie/en/fb/cainteoir
                # main entry is 'caint'
                search_entry = subentry
                break
            else:
                # https://www.teanglann.ie/en/fb/trumpa - ignore trumpadóir
                subentry.extract()
    if search_entry:
        noun_decs = search_entry.find_all(
            string=re.compile(k_lookup + '[1-4]')
        )
        declensions = set()
        for noun_dec in noun_decs:
            declensions.add(noun_dec.string.strip()[-1])
        if len(declensions) > 1:
            manual_debug()
        elif declensions:
            gender += declensions.pop()
    if len(gender) == 2:
        soup_gram = get_definition_soup(noun, 'teanglann', lang='ga-gram')
        grams = soup_gram.find_all(class_='gram')
        for gram in grams:
            gender_prop = False
            if gram.find(text='NOUN'):
                if gender == 'nf':
                    gender_prop = gram.find(text='FEMININE')
                elif gender == 'nm':
                    gender_prop = gram.find(text='MASCULINE')
            if gender_prop:
                dec_prop = gender_prop.\
                    find_parent(class_='property').\
                    find_next_sibling(class_='property')
                if dec_prop:
                    dec_text = bs4_get_text(dec_prop.find(class_='value'))
                    dec_text = dec_text.strip()
                    if dec_text.endswith('DECLENSION'):
                        gender += dec_text[0]
                        break
    return gender


def assign_plural_genitive(noun, html=True):

    ret = {}
    for subentries, subentry_labels in get_teanglann_subentries(noun):
        first_line = subentries[0]
        if first_line.find(title="transitive verb") or \
           first_line.find(title="intransitive verb") or \
           first_line.find(title="and intransitive"):
            # don't get confused by 'leibhéal' as a transitive verb
            # (dunno what it means to that there's a 'genitive singular'
            # leibhéalta)
            continue
        gender = assign_gender_declension(noun, first_line)
        if not gender:
            continue
        ret['gender'] = gender
        parts = sense_assign_plural_genitive(noun, first_line, gender, html)
        for k in parts:
            if k in ret and ret[k] != parts[k]:
                print(f'ERROR: multiple cases for {k}; '
                      f'{ret[k]} vs. {parts[k]}')
                return {}  # different words? no agreement
        ret.update(parts)
        if gender:
            if 'gender' in ret:
                if ret['gender'][:2] != gender[:2]:
                    print(f'ERROR: multiple genders for {k}')
                elif len(ret['gender']) < len(gender):
                    ret['gender'] = gender
            else:
                ret['gender'] = gender
    if 'gender' not in ret:
        return {}  # not a noun
    return ret


def sense_assign_plural_genitive(noun, first_line, gender, html=True):
    """
Could scrape e.g. https://www.teanglann.ie/en/gram/teist
but don't want the extra request
and this method can identify strong/weak plurals
    """
    first_line_mark_split = copy(first_line)
    trans = first_line_mark_split.find(class_='trans')
    if trans:
        trans.replace_with('__xxx_start_trans__')
    flt = clean_text(bs4_get_text(first_line_mark_split), noun)
    flt = flt.split('__xxx_start_trans__')[0]

    parts = {'nominative singular': noun}
    if noun == 'talamh':
        # an exception http://nualeargais.ie/gnag/0dekl.htm
        parts['nominative plural'] = 'tailte'
        parts['genitive plural'] = 'tailte'
        parts['plural strength'] = 'strong'
        parts['gender'] = 'nf'
        parts['genitive singular'] = 'talún (also m. variant: talaimh)'
        return parts
    part_names = [
        'nominative plural',
        'genitive singular',
        'genitive plural',
        'plural',
    ]
    strong_plural_endings = [
        'í',
        'acha',
        'anna',
        'ánna',  # íomhánna
        'lta',  # síolta
        'onna',  # suíonna
        'tha',
        'ocha',  # claí -> claíocha
        'thra', # briathar -> briathra
        'nta', # braon -> braonta, tonn -> tonnta, srian -> srianta, pian -> pianta
        # TODO: incomplete
    ]
    for i in range(len(part_names), 0, -1):
        for cs in permutations(part_names, i):
            ct = ' & '.join(cs)
            if ct in flt and ct == 'plural' and \
               ct not in flt.\
               replace('nominative plural', '').\
               replace('genitive plural', '').\
               split(')')[0]:  # trealamh
                continue
            rhss = []
            if ct in flt:
                rhss = flt.split(ct)[1:]
            for rhs in rhss:
                rhs_words = re.split('[,;)(] *', rhs)
                d_word = rhs_words[0].lstrip()
                if not d_word:
                    continue
                if d_word.startswith('as substantive'):
                    # e.g. smaoineamh
                    # 'smaoinimh' is what we want (don't understand
                    # 'smaointe' as 'genitive singular as verbal noun')
                    d_word = d_word[14:].lstrip()
                if d_word.endswith('in certain phrases') or \
                   d_word.endswith('used in phrases'):
                    # e.g. cara or rí
                    # 'genitive plural': 'carad in certain phrases'
                    # ignore
                    continue
                if d_word.startswith('-'):
                    d_word = fill_in_dash(d_word, noun)
                if 'plural' in cs:
                    cs = list(cs)
                    cs.remove('plural')
                    cs.append('nominative plural')
                    cs.append('genitive plural')
                    # strong plurals have to maintain
                    # their endings across all cases
                    # https://en.wikipedia.org/wiki/Irish_declension
                    parts['plural strength'] = 'strong'
                    if gender in ['nm1', 'nf2']:
                        # these are supposed to have weak plurals http://nualeargais.ie/gnag/subst2.htm#plural
                        print('CHECK PLURAL 4 :', gender, noun, d_word)
                    if d_word.endswith('a') and not any(d_word.endswith(e) for e in strong_plural_endings):
                        pass  # lots of them
                        #print('CHECK PLURAL 2 nf2:', gender, noun, d_word)
                    if d_word[-2:] == noun[-2:]:
                        # weak?
                        print('CHECK PLURAL 3:', gender, noun, d_word)
                for cp in cs:
                    if cp not in parts:
                        parts[cp] = d_word
    if 'nominative plural' not in parts:
        p = re.split(r'[,(;] ?(?:plural|pl\.)', flt)
        if len(p) > 1:
            rhs_words = re.split('[,;)(] *', p[1])
            d_word = rhs_words[0].lstrip()
            if d_word.startswith('-'):
                d_word = fill_in_dash(d_word, noun)
            parts['nominative plural'] = d_word
            if 'genitive plural' not in parts:
                parts['genitive plural'] = d_word
    if 'dative singular' in flt:
        p = re.split(r'[,(;] ?(?:dative singular)', flt)
        if len(p) > 1:
            rhs_words = re.split('[,;)(] *', p[1])
            d_word = rhs_words[0].lstrip()
            d_word = d_word.split('used in certain phrases')[0].rstrip()
            if d_word.startswith('-'):
                d_word = fill_in_dash(d_word, noun)
            parts['dative singular'] = d_word
    has_strong_ending = False
    if 'nominative plural' in parts:
        for ending in strong_plural_endings:
            if parts['nominative plural'].endswith(ending):
                if 'genitive plural' in parts and parts['genitive plural'] != parts['nominative plural']:
                    print('CHECK PLURAL 5:', gender, parts['nominative plural'], parts['genitive plural'])
                has_strong_ending = True
                break
    if 'plural strength' not in parts:
        parts['plural strength'] = 'unknown'
    if parts.get('genitive plural', None) == parts['nominative singular']:
        if has_strong_ending:
            print('CHECK PLURAL 1:', gender, parts['nominative plural'], parts['genitive plural'])
        parts['plural strength'] = 'weak'
    apply_gender_hints(noun, gender, parts)
    for k, w in parts.items():
        parts[k] = apply_article(w, gender, k)
    return parts


def assign_verbal_noun(verb):
    for subentries, subentry_labels in get_teanglann_subentries(verb):
        first_line = subentries[0]
        if first_line.find(title="transitive verb") or \
           first_line.find(title="intransitive verb") or \
           first_line.find(title="and intransitive"):
            flt = bs4_get_text(first_line)
            flt = re.sub(r'\s\s+', ' ', flt)  # dóigh: newlines
            vn = None
            if 'verbal noun ~' in flt:
                vn = flt.split('verbal noun ~', 1)[1]
                vn = vn.replace('feminine', '')  # pleanáil poor spacing
                vn = vn.replace('masculine', '')  # ditto
                vn = verb + vn
            elif 'verbal noun -' in flt:
                suffix = flt.split('verbal noun -', 1)[1]
                suffix = re.split(r'[\s,);]', suffix.lstrip())[0]
                vn = fill_in_dash('-' + suffix, verb)
            else:
                for good_split in [
                        '(verbal noun ',
                        ', verbal noun ',
                        '; verbal noun ',
                        ]:
                    if good_split in flt:
                        vn = flt.split(good_split, 1)[1]
            if vn:
                vn = re.split(r'[\s,);]', vn.lstrip())[0]
                return vn
            vni = first_line.find(title='verbal noun')
            if vni:
                vn = bs4_get_text(vni.next_sibling)
                vn = vn.strip()
                if ' ' in vn:
                    manual_debug()
                if 'of' in vn:
                    manual_debug()
                if '~' not in vn:
                    manual_debug()
                else:
                    return vn.replace('~', verb)
            pass
        else:
            if verb_from_vn(verb) == verb:
                # self verbal noun, e.g. bruith
                return verb

    soup = get_definition_soup(verb, 'teanglann', lang='ga')  # same page
    rm = soup.find(text=re.compile(r"\s*RELATED\s+MATCHES\s*"))
    if rm:
        for link in rm.parent.parent.find_all('a'):
            related_word = bs4_get_text(link).strip(' »')
            if verb_from_vn(related_word) == verb:
                return related_word
    if verb.endswith('aigh') and verb_from_vn(verb[:-4] + 'ú') == verb:
        # aontaigh / aontú
        return verb[:-4] + 'ú'
    if verb.endswith('igh') and verb_from_vn(verb[:-2] + 'ú') == verb:
        # oibrigh / oibriú
        return verb[:-2] + 'ú'
    if verb_from_vn(verb + 'adh') == verb:
        # gets 'cor'
        return verb + 'adh'
    if verb_from_vn(verb + 'eadh') == verb:
        # gets 'croith'
        return verb + 'eadh'

    if verb == 'tosnaigh':
        # https://www.gaois.ie/crp/ga/?txt=tosn%C3%BA&lang=ga&SearchMode=narrow
        return 'tosnú'  # rather than 'tosú'
    if verb not in [
            'réigh',  # is it réiteach also?
            'áil',  # literary use as a verb
            'cis',
            'gad',
            'fainic',  # used imperatively only
            'batráil',
    ]:
        print(f'Warning: No verbal noun found for {verb}')
    pass


def verb_from_vn(word):
    for subentries, subentry_labels in get_teanglann_subentries(word):
        first_line = subentries[0]
        if first_line.find(title="masculine") or \
           first_line.find(title="feminine"):
            # 'coradh' has it in first line (missing '1.') so can't do
            # subentries[1:]
            # although afraid that it shouldn't be in a heading
            for line in subentries:
                vn = line.find(title='verbal noun')
                if vn and bs4_get_text(vn.next_sibling).strip() == 'of':
                    line_text = bs4_get_text(line)
                    line_text = line_text.split('of', 1)[-1].strip()
                    line_text = line_text.split(' ')[0].rstrip(' .123456789')
                    return line_text.strip()


def find_teanglann_periphrases():
    """
total words: 53,677
323 multi-word entries:
...
téigh trí
thar ceann
thar n-ais
tit amach
tit ar
tit chuig
tit do
tit faoi
...
    """
    alphabet = list('abcdefghijklmnopqrstuvwxyz')
    word_count = 0
    shuffle(alphabet)
    for letter in alphabet:
        soup = get_definition_soup('_' + letter, 'teanglann')
        abc = soup.find(class_='abcListings')
        for word_item in abc.find_all(class_="abcItem"):
            potential_periphrase = bs4_get_text(word_item.find('a'))
            if ' ' in potential_periphrase:
                print(potential_periphrase)
            else:
                word_count += 1
    print('total words:', word_count)


def expand_abbreviations(soup):
    for abbr in soup.find_all(title=True):
        abbr_title = abbr['title'].strip()
        if not abbr.string:
            # <span class="fgb tip" title="Electrical Engineering"><span
            # class="fgb tip" title="Electricity; electrical">El</span>.<span
            # class="fgb tip" title="Engineering">E</span></span>
            abbr.string = abbr_title
        else:
            abbr.string.replace_with(abbr_title)
        next_sib = abbr.next_sibling
        if next_sib and next_sib.string.lstrip().startswith('.'):
            abbr.next_sibling.string.\
                replace_with(abbr.next_sibling.string.lstrip()[1:])
    return soup


def join_parts_of_speech(type_dict):
    bits = []
    for type_, val in type_dict.items():
        if val is True:
            bit = type_
        elif isinstance(val, dict):
            if not val:
                continue  # wouldn't be necessary with an OrderedDefaultDict
            bit = type_ + ' - ' + ' & '.join(val.keys())
        else:
            bit = type_ + val
        bits.append(bit)
    return ', '.join(bits[:-2] + [' & '.join(bits[-2:])])


def clean_text(text, word):
    text = text.replace('\n', '')
    text = re.sub('[ ]{2,}', ' ', text).strip()  # repeated spaces
    text = text.rstrip('.')  # trailing dots
    text = text.lower().lstrip(')').rstrip('(')
    # only replace now as don't want to change case of e.g. Eorpach
    return text.replace('~', word)


def fill_in_dash(dash_suffix, word):
    suffix = dash_suffix.lstrip('-')
    if suffix[0] not in word:
        if word + suffix != 'cosantóirí':
            raise Exception(
                'Bad suffix in teanglann?'
                f'{word} {dash_suffix}'
            )
        modified_word = word + suffix
    elif suffix[0] == suffix[1]:
        # coinnigh (vn. -nneáil)  -> coinneáil
        modified_word = word[:word.rindex(suffix[:2])] + suffix
    else:
        # éirigh (verbal noun -rí) -> éirí
        modified_word = word[:word.rindex(suffix[0])] + suffix
    return modified_word


def manual_debug():
    import pdb
    p = pdb.Pdb()
    p.set_trace(sys._getframe().f_back)


if __name__ == '__main__':
    find_teanglann_periphrases()
