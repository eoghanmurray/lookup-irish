#!/usr/bin/env python3
from __future__ import print_function
import pickle
import os.path
from googleapiclient.discovery import build
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
import os
from bs4 import BeautifulSoup
import requests
import re
from collections import OrderedDict, namedtuple
import codecs
import sys
import time
from random import randint, shuffle
from colorama import Fore, Back, Style
from itertools import permutations


# If modifying these scopes, delete the file token.pickle.
SCOPES = ['https://www.googleapis.com/auth/spreadsheets']

# The ID and range of a sample spreadsheet.
SPREADSHEET_ID = '1kiZlZp8weyILstvtL0PfIQkQGzuG7oZfP8n_qkMFAWo'
RANGE = '6450-most-frequent-irish-words!A1:G'

FIRST_ROW_SIG = 'AUTO GA PoS EN Gender Tags GenitiveVN'
COLUMN_KEY = {}
alphabet = 'ABCDEFGHIJKLMNOPQRSTUVWXYZ'
for col, letter in zip(FIRST_ROW_SIG.split(' '), alphabet):
    COLUMN_KEY[col] = letter
RowTup = namedtuple('RowTup', FIRST_ROW_SIG)

cum_sleep = 0

def get_sheet():
    """Shows basic usage of the Sheets API.
    Prints values from a sample spreadsheet.
    """
    creds = None
    # The file token.pickle stores the user's access and refresh tokens, and is
    # created automatically when the authorization flow completes for the first
    # time.
    if os.path.exists('token.pickle'):
        with open('token.pickle', 'rb') as token:
            creds = pickle.load(token)
    # If there are no (valid) credentials available, let the user log in.
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file(
                'credentials.json', SCOPES)
            creds = flow.run_local_server(port=0)
        # Save the credentials for the next run
        with open('token.pickle', 'wb') as token:
            pickle.dump(creds, token)

    service = build('sheets', 'v4', credentials=creds)

    # Call the Sheets API
    sheet = service.spreadsheets()
    return sheet


def get_range(sheet):
    result = sheet.values().get(spreadsheetId=SPREADSHEET_ID,
                                range=RANGE).execute()
    values = result.get('values', [])
    if not values:
        return False
    assert ' '.join(values[0]) == FIRST_ROW_SIG
    for v in values:
        v_ext = (v + [''] * len(values[0]))[:len(values[0])]
        yield RowTup(*v_ext)


def insert_block(sheet, range, values):
    body = {
        'values': values,
    }
    result = sheet.values().update(
        spreadsheetId=SPREADSHEET_ID,
        range=range,
        valueInputOption='RAW',
        body=body).execute()
    print('{0} cells updated.'.format(result.get('updatedCells')))


def populate_empty(refresh=True, limit=15):
    sheet = get_sheet()
    rows = get_range(sheet)
    if rows:
        count = 0
        values = []
        range_start = None
        for n, row in enumerate(rows):
            cell_no = n + 1  # 1 for 0 index
            insert_now = False
            if row.GA and (
                    not row.EN or
                    (refresh and row.EN.endswith('[AUTO]'))
                    ):
                PoS, EN, Gender = get_teanglann_definition(row.GA, return_raw=True)
                if EN and EN + '\n[AUTO]' != row.EN:
                    values.append(
                        [
                            PoS,
                            EN + '\n[AUTO]',
                            Gender,
                        ],
                    )
                    if not range_start:
                        range_start = f'{COLUMN_KEY["PoS"]}{cell_no}'
                    range_end = f'{COLUMN_KEY["Gender"]}{cell_no}'
                    count += 1
                else:
                    insert_now = True
            else:
                insert_now = True
            if values and insert_now:
                insert_block(sheet, range_start + ':' + range_end, values)
                values = []
                range_start = None

            if count == limit:
                print(f'{count} rows updated')
                break
        if values:
            insert_block(sheet, range_start + ':' + range_end, values)


def populate_genitive_verbal_noun(limit=-1, refresh=True):
    sheet = get_sheet()
    rows = get_range(sheet)
    if rows:
        count = 0
        values = []
        range_start = None
        for n, row in enumerate(rows):
            cell_no = n + 1  # 1 for 0 index
            insert_now = False
            if row.GA and (
                    not row.GenitiveVN or
                    refresh
                    ):
                PoS, EN, Gender = get_teanglann_definition(row.GA)
                GenitiveVN = ''
                if 'Noun' in PoS and 'Noun' in row.PoS and ' ' not in row.GA:
                    declensions = assign_plural_genitive(row.GA, html=True)
                    if len(declensions) == 5:
                        GenitiveVN += f'<div class="{Gender[:2]} d{Gender[2:]}">'
                        GenitiveVN += declensions['nominative singular'] + '/' + declensions['nominative plural']
                        GenitiveVN += '<br>'
                        GenitiveVN += declensions['genitive singular'] + '/' + declensions['genitive plural']
                        GenitiveVN += '</div>'
                if 'Verb' in PoS and 'ransitive' in PoS and ' ' and 'Verb' in row.PoS and 'ransitive' in row.PoS and ' '  not in row.GA:
                    if GenitiveVN:
                        GenitiveVN += '\n'
                    vn = assign_verbal_noun(row.GA)
                    if not vn:
                        manual_debug()
                    else:
                        GenitiveVN += 'ag ' + vn
                if (PoS or Gender) and GenitiveVN:
                    values.append(
                        [
                            GenitiveVN
                        ],
                    )
                    if not range_start:
                        range_start = f'{COLUMN_KEY["GenitiveVN"]}{cell_no}'
                    range_end = f'{COLUMN_KEY["GenitiveVN"]}{cell_no}'
                    count += 1
                else:
                    insert_now = True
            else:
                insert_now = True
            if values and insert_now:
                insert_block(sheet, range_start + ':' + range_end, values)
                values = []
                range_start = None

            if count == limit:
                print(f'{count} rows updated')
                break
        if values:
            insert_block(sheet, range_start + ':' + range_end, values)


def populate_AUTO_comparison(refresh=False):
    """
Populate the AUTO column to compare against existing manual entries
    """
    sheet = get_sheet()
    rows = get_range(sheet)
    if rows:
        count = 0
        from io import StringIO
        for n, row in enumerate(rows):
            cell_no = n + 1  # 1 for 0 index
            if row.AUTO != '' and not refresh:
                continue
            if not row.EN or row.EN.endswith('[AUTO]'):
                continue
            if n > 200:
                #orig = sys.stdout
                #sys.stdout = StringIO()
                PoS, EN, Gender = get_teanglann_definition(row.GA)
                #captured = sys.stdout
                #sys.stdout = orig
                if False:
                    print()
                    print(f'C{cell_no}:E{cell_no}')
                    print(row.GA)
                    print(row.EN)
                    print(' vs.')
                    print(EN)
                    #print(captured.read())  # not working
                else:
                    if EN:
                        if EN == row.EN:
                            value = ''
                        else:
                            value = EN
                    else:
                        value = '[NONE]'
                    if value != row.AUTO:
                        body = { 'values': [[value]], }
                        result = sheet.values().update(
                            spreadsheetId=SPREADSHEET_ID,
                            range=f'{COLUMN_KEY["AUTO"]}{cell_no}',
                            valueInputOption='RAW',
                            body=body).execute()
                        print('{0} cells updated.'.format(result.get('updatedCells')))
                        count += 1

            if count == 100:
                break


def print_verbal_nouns(refresh=False):
    """
Maybe put these as a (smaller) second line below the GA on front of card
    """
    sheet = get_sheet()
    rows = get_range(sheet)
    if rows:
        count = 0
        from io import StringIO
        for n, row in enumerate(rows):
            cell_no = n + 1  # 1 for 0 index
            if 'Verb' in row.PoS and 'ransitive' in row.PoS and ' ' not in row.GA:
                vn = assign_verbal_noun(row.GA)
                if not vn:
                    print(f'  {row.GA} - ag {vn}')
                else:
                    print(f'{row.GA} - ag {vn}')
                count += 1
            if count == 300:
                break


def get_definition_soup(word, dictionary, lang='ga', page_no=1):
    global cum_sleep
    if cum_sleep:
        # a little bit of backoff between requests
        time.sleep(cum_sleep + randint(1, 4))
        cum_sleep += 0.25

    headers = {
        'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Ubuntu Chromium/76.0.3809.100 Chrome/76.0.3809.100 Safari/537.36'
    }
    if dictionary == 'teanglann':
        href = 'https://www.teanglann.ie'
        if lang == 'ga':
            href += '/en/fgb/' + word
        elif lang == 'ga-fb':
            # a separate dictionary rather than a separate language
            href += '/en/fb/' + word
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
        page = requests.get(href, headers=headers)
        soup = BeautifulSoup(page.text, features='html5lib')
        # writing the soup rather than raw response as it converts to utf8
        codecs.open(local_path, 'w', encoding='utf-8').write(str(soup))
    return soup


def get_foclóir_candidates(word):
    candidates = set()
    for n in range(1, 18):
        soup = get_definition_soup(word, 'foclóir', lang='ga', page_no=n)
        result_lists = soup.find_all(class_='result-list')
        if not result_lists:
            if 'No matches found.' in soup.get_text():
                return set()
        if len(result_lists) != 1:
            manual_debug()
        imprecise_match = False
        lis = result_lists[0].find_all('li')
        for result in lis:
            if result.find(class_='lang_ga').string.strip() == word:
                candidates.add(result.find(class_='lang_en').string.strip())
            elif word in result.find(class_='lang_ga').string:
                # a multi-word version
                # so for 'cead' we stop on 'cead scoir', but not on 'céad' (fada)
                imprecise_match = True
        if imprecise_match or len(lis) < 20:
            break
    return candidates


def expand_abbreviations(soup):
    for abbr in soup.find_all(title=True):
        abbr_text = abbr.text.strip()
        abbr_title = abbr['title'].strip()
        if not abbr.string:
            # <span class="fgb tip" title="Electrical Engineering"><span class="fgb tip" title="Electricity; electrical">El</span>.<span class="fgb tip" title="Engineering">E</span></span>
            abbr.string = abbr_title
        else:
            abbr.string.replace_with(abbr_title)
        if abbr.next_sibling and abbr.next_sibling.string.lstrip().startswith('.'):
            abbr.next_sibling.string.replace_with(abbr.next_sibling.string.lstrip()[1:])
    return soup


def get_teanglann_subentries(word):
    soup = get_definition_soup(word, 'teanglann', lang='ga')

    for entry in soup.find_all(class_='entry'):

        expand_abbreviations(entry)
        if not entry.text.strip().lower().startswith(word.lower()):
            # https://www.teanglann.ie/en/fgb/i%20measc gives results for 'imeasc'
            continue

        subentries = [soup.new_tag('div')]
        subentry_labels = ['']  # first line, may contain a 'main' entry
        n = 1
        nxs = 'abcdefghijklmnopqrstuvwxyz'
        nxi = 0
        for node in entry.contents[:]:
            node_text = bs4_get_text(node)
            if f'{n}.' in re.sub(f'adjective\s*{1}.', '', node_text):
                as_subnode = node.find(text=re.compile(f'\s+{n}.\s+'))
                if as_subnode:
                    rev = []
                    for r in as_subnode.previous_siblings:
                        rev.append(r)
                    for r in reversed(rev):
                        subentries[-1].append(r)
                else:
                    pre, post = node_text.rsplit(f'{n}.', 1)
                    if pre.strip():
                        subentries[-1].append(pre.strip())
                subentries.append(soup.new_tag('div'))
                subentry_labels.append(f'{n}. ')
                nxi = 0
                if as_subnode:
                    for r in as_subnode.next_siblings:
                        subentries[-1].append(r)
                else:
                    if post.strip():
                        subentries[-1].append(post.strip())
                n += 1
            elif (len(subentries) > 1  # we've actually got at least a '1.' already
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
    if entry_fb:
        for subentry in entry_fb.find_all(class_='subentry'):
            # https://www.teanglann.ie/en/fb/trumpa - ignore trumpadóir
            subentry.extract()
        noun_decs = entry_fb.find_all(
            string=re.compile(k_lookup + '[1-4]')
        )
        declensions = set()
        for noun_dec in noun_decs:
            declensions.add(noun_dec.string.strip()[-1])
        if len(declensions) > 1:
            manual_debug()
        elif declensions:
            gender += declensions.pop()
    return gender


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


def assign_plural_genitive(noun, html=True):
    """
Could scrape e.g. https://www.teanglann.ie/en/gram/teist
but don't want to
    """

    ret = {}
    mf = None
    for subentries, subentry_labels in get_teanglann_subentries(noun):
        first_line = subentries[0]
        flt = clean_text(bs4_get_text(first_line), noun)
        print(flt)
        parts = {'nominative singular': noun}
        part_names = ['nominative plural', 'genitive singular', 'genitive plural']
        for i in range(len(part_names), 0, -1):
            for cs in permutations(part_names, i):
                ct = ' & '.join(cs)
                if ct in flt:
                    rhs = flt.split(ct)[1]
                    rhs_words = re.split('[,;)(] *', rhs)
                    d_word = rhs_words[0].lstrip()
                    if d_word.startswith('-'):
                        d_word = fill_in_dash(d_word, noun)
                    for cp in cs:
                        if cp not in parts:
                            parts[cp] = d_word
        if 'nominative plural' not in parts:
            p = re.split('[,(] ?plural', flt)
            if len(p) > 1:
                rhs_words = re.split('[,;)(] *', p[1])
                d_word = rhs_words[0].lstrip()
                if d_word.startswith('-'):
                    d_word = fill_in_dash(d_word, noun)
                parts['nominative plural'] = d_word
                if 'genitive plural' not in parts:
                    parts['genitive plural'] = d_word
        gender = assign_gender_declension(noun, first_line)
        if gender:
            ret['gender'] = gender
        for k in parts:
            if k in ret and ret[k] != parts[k]:
                return {}  # different words? no agreement
                manual_debug()
        ret.update(parts)
    for k, w in ret.items():
        if k != 'gender':
            ret[k] = apply_article(w, ret['gender'], k)
    return ret


def apply_article(word, gender, part_of_speech, html=True):
    """
http://nualeargais.ie/gnag/artikel.htm
    """
    preceding_s = word[0] == 's'
    preceding_a_vowel = word[0] in 'aeiouáéíóú'
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
    elif nf and genitive:
        ret = '<i>na</i> '
    else:
        ret = 'an '
    if 'plural' in part_of_speech:
        # no html needed here as same in both genders
        if preceding_s:
            ret += word
        elif preceding_a_vowel:
            if genitive:
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
               word[1] in 'aeiouáéíóúlnr' and (
                    (nominative and nf) or
                    (genitive and nm)):
                ret += '<i>t</i>' + word
            elif preceding_a_vowel and \
                 nf and genitive:
                ret += '<i>h</i>' + word
            elif preceding_a_vowel and \
                 nm and nominative:
                ret += '<i>t</i>-' + word
            elif preceding_a_consonant and (
                    (nm and genitive) or
                    (nf and nominative)):
                ret += lenite(word, html=True)
            else:
                ret += word
    if not html:
        return ret.replace('<i>', '').replace('</i>', '')
    return ret


def assign_verbal_noun(verb):
    for subentries, subentry_labels in get_teanglann_subentries(verb):
        first_line = subentries[0]
        if first_line.find(title="transitive verb") or \
           first_line.find(title="intransitive verb") or \
           first_line.find(title="and intransitive"):
            flt = bs4_get_text(first_line)
            flt = re.sub('\s\s+', ' ', flt)  # dóigh: newlines
            vn = None
            if 'verbal noun ~' in flt:
                vn = flt.split('verbal noun ~', 1)[1]
                vn = vn.replace('feminine', '')  # pleanáil poor spacing
                vn = vn.replace('masculine', '')  # ditto
                vn = verb + vn
            elif 'verbal noun -' in flt:
                suffix = flt.split('verbal noun -', 1)[1]
                suffix = re.split('[\s,);]', suffix.lstrip())[0]
                vn = fill_in_dash('-' + suffix, verb)
                if get_verb_from_verbal_noun(vn) != verb:
                    vn_entries = [e for e in get_teanglann_subentries(vn)]
                    if len(vn_entries) == 1 and \
                       len(vn_entries[0][0]) == 1 and \
                       bs4_get_text(vn_entries[0][0][0]).rstrip('123456789. ').replace(' ', '') == f'{vn}:{verb}':
                        # these ones ok and just link back directly
                        pass
                    else:
                        manual_debug()
                    # we haven't done it right?
                    pass
            else:
                for good_split in [
                        '(verbal noun ',
                        ', verbal noun ',
                        '; verbal noun ',
                        ]:
                    if good_split in flt:
                        vn = flt.split(good_split, 1)[1]
            if vn:
                vn = re.split('[\s,);]', vn.lstrip())[0]
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
            if get_verb_from_verbal_noun(verb) == verb:
                # self verbal noun, e.g. bruith
                return verb

    soup = get_definition_soup(verb, 'teanglann', lang='ga')  # same page
    rm = soup.find(text=re.compile("\s*RELATED\s+MATCHES\s*"))
    if rm:
        for link in rm.parent.parent.find_all('a'):
            #related_word = link['href'].rsplit('/', 1)[1]
            related_word = bs4_get_text(link).strip(' »')
            if get_verb_from_verbal_noun(related_word) == verb:
                return related_word
    if verb.endswith('aigh') and get_verb_from_verbal_noun(verb[:-4] + 'ú') == verb:
        # aontaigh / aontú
        return verb[:-4] + 'ú'
    if verb.endswith('igh') and get_verb_from_verbal_noun(verb[:-2] + 'ú') == verb:
        # oibrigh / oibriú
        return verb[:-2] + 'ú'
    if get_verb_from_verbal_noun(verb + 'adh') == verb:
        # gets 'cor'
        return verb + 'adh'
    if get_verb_from_verbal_noun(verb + 'eadh') == verb:
        # gets 'croith'
        return verb + 'eadh'
    if verb != 'tosnaigh':
        manual_debug()
    pass


def get_verb_from_verbal_noun(word):
    for subentries, subentry_labels in get_teanglann_subentries(word):
        first_line = subentries[0]
        if first_line.find(title="masculine") or \
           first_line.find(title="feminine"):
            # 'coradh' has it in first line (missing '1.') so can't do subentries[1:]
            # although afraid that it shouldn't be in a heading
            for line in subentries:
                vn = line.find(title='verbal noun')
                if vn and bs4_get_text(vn.next_sibling).strip() == 'of':
                    line_text = bs4_get_text(line)
                    line_text = line_text.split('of', 1)[-1].strip()
                    line_text = line_text.split(' ')[0].rstrip(' .123456789')
                    return line_text.strip()


def get_teanglann_definition(word, return_raw=False, sort_by_foclóir=False):

    candidates = get_foclóir_candidates(word)
    print()
    print(f'{Back.YELLOW}{Fore.BLACK}{word}{Style.RESET_ALL} foclóir:', candidates)

    parts_of_speech = OrderedDict()
    definitions = []
    raw_definitions = []
    genders = []

    for subentries, subentry_labels in get_teanglann_subentries(word):
        first_line = subentries[0]
        gender = None
        types = OrderedDict()  # using as ordered set
        if first_line.find(title="feminine") and first_line.find(title="masculine"):
            # 'thar': has 'thairis (m) thairsti (f)' and is not a noun
            pass
        elif first_line.find(title="feminine") or first_line.find(title="masculine"):
            types['Noun'] = True
            gender = assign_gender_declension(word, first_line)
        if first_line.find(title="adverb"):
            types['Adverb'] = True
        if first_line.find(title="preposition"):
            types['Preposition'] = True
        if first_line.find(title="adjective"):
            types['Adjective'] = True
            gender = 'a'
            dec = first_line.find(title="adjective").next_sibling
            # to check: think it only goes up to a3
            if dec and dec.strip().strip('.') in ['1', '2', '3', '4']:
                gender += dec.strip().strip('.')
            else:
                soup_fb = get_definition_soup(word, 'teanglann', lang='ga-fb')
                entry_fb = soup_fb.find(class_='entry')
                if soup_fb.find(text='aid3'):
                    gender += '3'
                elif soup_fb.find(text='aid2'):
                    gender += '2'
                elif soup_fb.find(text='aid1'):
                    gender += '1'  # think there'
                elif not  soup_fb.find(text='aid'):
                    # 'thar' spurious adj. in following:
                    # 'references of <span title="adjective">a</span> general nature'
                    del types['Adjective']
                    gender = None
        if first_line.find(title="transitive verb"):
            if 'Verb' not in types:
                types['Verb'] = OrderedDict()
            types['Verb']['Transitive'] = True
        if first_line.find(title="intransitive verb") or first_line.find(title="and intransitive"):
            if 'Verb' not in types:
                types['Verb'] = OrderedDict()
            types['Verb']['Intransitive'] = True
        if first_line.find(title="conjunction"):
            types['Conjugation'] = True
        if first_line.find(title="prefix"):
            types['Prefix'] = True

        for subentry in subentries:
            raw_text = clean_text(' '.join(subentry.stripped_strings), word)
            if  raw_text.startswith('verbal noun') and ' of ' in raw_text:
                verb_name = raw_text.split(' of ', 1)[1].strip().rstrip(' 123456789')
                if verb_name == word:
                    types['Verbal Noun'] = True
                else:
                    types['Verbal Noun'] = ' of ' + verb_name

        print()
        print(f'{Back.RED}{word}{Style.RESET_ALL}', print_types(types), gender)
        for label, subentry in zip(subentry_labels, subentries):
            transs = subentry.find_all(class_='trans')
            if len(transs) > 1 and (
                    (bs4_get_text(transs[0]).lstrip().startswith('(') and
                     bs4_get_text(transs[0]).rstrip().endswith(')'))
                    or
                    (bs4_get_text(transs[0].previous_sibling).rstrip().endswith('(') and
                     bs4_get_text(transs[0].next_sibling).lstrip().startswith(')'))
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
            formatted_text = clean_text(' '.join(subentry.stripped_strings), word)
            for example in subentry.find_all(class_='example'):
                example_text = clean_text(example.get_text(), word)
                formatted_text = formatted_text.replace(example_text, f'\n    {example_text}')
            if not transs:
                print(f'{label}[{formatted_text}]')
            else:
                trans_text = clean_text(transs[0].get_text(), word)
                maybe_to = ''
                if 'Verb' in types:
                    maybe_to = 'to '
                trans_words = re.split('[,;] *', trans_text)
                #trans_words = [tgw for tgw in trans_words if tgw not in definitions]
                defn_words = [tgw for tgw in trans_words if re.sub('\s*\(.*?\)\s*', '', tgw) in candidates]
                if sort_by_foclóir and defn_words:
                    foclóir_scores = []
                    for defn_word in defn_words:
                        foclóir_scores.append((foclóir_score_definition(defn_word, word), defn_word))
                    foclóir_scores.sort()
                    foclóir_min_score = min(foclóir_scores)[0]
                    if False:
                        # debug
                        defn = '/'.join([fs[1] + f' ({fs[0]})' for fs in foclóir_scores])
                    else:
                        defn = '/'.join([fs[1] for fs in foclóir_scores])
                else:
                    defn = '/'.join(defn_words)
                if len(transs) > 1:
                    formatted_text = f'X{len(transs)} {formatted_text}'
                raw_definitions.append(f'[{trans_text}]')
                definition = None
                if defn:
                    definition = maybe_to + defn + first_trans_extra
                    print(f'{label}{Fore.GREEN}{definition}{Style.RESET_ALL} [{formatted_text}]')
                else:
                    for fcw in candidates:
                        if all(tgw.startswith(fcw + ' ') for tgw in trans_words):
                            rest = ' (' + ', '.join(tgw[len(fcw) + 1:] for tgw in trans_words) + ')'
                            print(f'{label}{Fore.GREEN}{maybe_to}{fcw}{Fore.MAGENTA}{rest}{Style.RESET_ALL} [{formatted_text}]')
                            definition = maybe_to + fcw + rest
                            break
                        elif all(tgw.endswith(' ' + fcw) for tgw in trans_words):
                            rest = '(' + ', '.join(tgw[:-len(fcw) - 1] for tgw in trans_words) + ') '
                            print(f'{label}{Fore.GREEN}{maybe_to}{Fore.MAGENTA}{rest}{Fore.GREEN}{fcw}{Style.RESET_ALL} [{formatted_text}]')
                            definition = maybe_to + rest + fcw
                            break
                    else:
                        print(f'{label}[{formatted_text}]')
                if definition and definition not in definitions:
                    # could filter/rearrange existing definitions here
                    if 'Prefix' in types:
                        definition = definition + ' (as prefix)'
                    if sort_by_foclóir:
                        if 'Verb' in types:
                            # put all verbs at the end (could do better)
                            definitions.append((foclóir_min_score + 10, definition))
                        else:
                            definitions.append((foclóir_min_score, definition))
                    else:
                        definitions.append(definition)

        if gender and gender not in genders:
            genders.append(gender)
        for k, v in types.items():
            if isinstance(v, dict) and k in parts_of_speech:
                parts_of_speech[k].update(v)
            else:
                parts_of_speech[k] = v
    if return_raw == 'force' or \
       (not definitions and return_raw):
        return print_types(parts_of_speech), '\n'.join(raw_definitions), '\n'.join(genders)
    elif sort_by_foclóir:
        definitions.sort()
        mdefinitions = '\n'.join([d[1] for d in definitions])
        return print_types(parts_of_speech), mdefinitions, '\n'.join(genders)
    else:
        return print_types(parts_of_speech), '\n'.join(definitions), '\n'.join(genders)


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
        lang_gas = sense.find_all(attrs={'xml:lang': 'ga', 'class': 'cit_translation'})
        for lang_ga in lang_gas:
            lang_gas_count += 1
            if lang_ga.find(class_='quote', text=ga) or \
               ga in bs4_get_text(lang_ga.find(class_='quote')):
                found_count += 1
                break
    return 1 - (found_count / lang_gas_count)


def bs4_get_text(node_or_string):
    if node_or_string is None:
        return ''
    elif hasattr(node_or_string, 'get_text'):
        return node_or_string.get_text()
    else:
        return node_or_string.string


def clean_text(text, word):
    text = text.replace('\n', '')
    text = text.replace('~', word)
    text = re.sub('[ ]{2,}', ' ', text).strip()  # repeated spaces
    text = text.rstrip('.')  # trailing dots
    return text.lower().lstrip(')').rstrip('(')


def fill_in_dash(suffix, word):
    suffix = suffix.lstrip('-')
    if suffix[0] == suffix[1]:
        # coinnigh (vn. -nneáil)  -> coinneáil
        modified_word = word[:word.rindex(suffix[:2])] + suffix
    else:
        # éirigh (verbal noun -rí) -> éirí
        modified_word = word[:word.rindex(suffix[0])] + suffix
    return modified_word


def print_types(type_dict):
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


def manual_debug():
    import pdb
    p = pdb.Pdb()
    p.set_trace(sys._getframe().f_back)


if __name__ == '__main__':
    if len(sys.argv) > 1:
        GA = sys.argv[-1]
        PoS, EN, Gender = get_teanglann_definition(GA)
        print()
        print(PoS, Gender)
        if 'Verb' in PoS and 'ransitive' in PoS and ' ' not in GA:
            print('ag ' + assign_verbal_noun(GA))
        print(EN)
    elif True:
        populate_genitive_verbal_noun(limit=500)
    elif False:
        find_teanglann_periphrases()
    elif False:
        populate_AUTO_comparison(refresh=True)
    elif True:
        populate_empty(limit=-1)
    elif False:
        print_verbal_nouns()
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
        # ensure don't get 'persist' ('persistent' is in teanglann, 'persisting' is in focloir)
        get_teanglann_definition('leanúnach')
        # get '(proper) condition'
        get_teanglann_definition('bail')
        # get 'exact (measure, position)' instead of 'exact (measure; exact position)'
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
        # verb intransitive + transitive, with extra entry with intransitive verb only
        # expecting to get 'Verb - Transitive & Intransitive' back
        print(get_teanglann_definition('lonnaigh')[0])
    else:
        # not getting 'cream'
        get_teanglann_definition('uachtar')
