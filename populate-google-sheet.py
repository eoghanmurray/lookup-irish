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
from random import randint
from colorama import Fore, Back, Style


# If modifying these scopes, delete the file token.pickle.
SCOPES = ['https://www.googleapis.com/auth/spreadsheets']

# The ID and range of a sample spreadsheet.
SPREADSHEET_ID = '1kiZlZp8weyILstvtL0PfIQkQGzuG7oZfP8n_qkMFAWo'
RANGE = '6450-most-frequent-irish-words!A1:F'

FIRST_ROW_SIG = 'AUTO GA PoS EN Gender Tags'
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
        v_ext = (v + [''] * 6)[:6]
        yield RowTup(*v_ext)


def populate_empty():
    sheet = get_sheet()
    rows = get_range(sheet)
    if rows:
        count = 0
        for n, row in enumerate(rows):
            cell_no = n + 1  # 1 for 0 index
            # TODO: also re-update existing rows where row.EN.endswith('[AUTO]')
            if row.GA and not row.EN:
                PoS, EN, Gender = get_teanglann_definition(row.GA)
                if EN:
                    values = [
                        [
                            PoS,
                            EN + '\n[AUTO]',
                            Gender,
                        ],
                    ]
                    body = {
                        'values': values,
                    }
                    result = sheet.values().update(
                        spreadsheetId=SPREADSHEET_ID,
                        range=f'{COLUMN_KEY["PoS"]}{cell_no}:{COLUMN_KEY["Gender"]}{cell_no}',
                        valueInputOption='RAW',
                        body=body).execute()
                    print('{0} cells updated.'.format(result.get('updatedCells')))
                    count += 1

            if count == 15:
                break


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
            if not row.EN:
                continue
            if n > 200:
                #orig = sys.stdout
                #sys.stdout = StringIO()
                PoS, EN, Gender = get_teanglann_definition(row.GA)
                #captured = sys.stdout
                #sys.stdout = orig
                if EN != row.EN:
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
                            body = { 'values': [[EN]], }
                        else:
                            body = { 'values': [['[NONE]']], }
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


def get_teanglann_subentries(word):
    soup = get_definition_soup(word, 'teanglann', lang='ga')

    for entry in soup.find_all(class_='entry'):

        # expand abbreviations
        for abbr in entry.find_all(title=True):
            abbr_text = abbr.text.strip()
            abbr_title = abbr['title'].strip()
            if not abbr.string:
                # <span class="fgb tip" title="Electrical Engineering"><span class="fgb tip" title="Electricity; electrical">El</span>.<span class="fgb tip" title="Engineering">E</span></span>
                abbr.string = abbr_title
            else:
                abbr.string.replace_with(abbr_title)
            if abbr.next_sibling and abbr.next_sibling.string.lstrip().startswith('.'):
                abbr.next_sibling.string.replace_with(abbr.next_sibling.string.lstrip()[1:])

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
                if suffix[0] == suffix[1]:
                    # coinnigh (vn. -nneáil)  -> coinneáil
                    vn = verb[:verb.rindex(suffix[:2])] + suffix
                else:
                    # éirigh (verbal noun -rí) -> éirí
                    vn = verb[:verb.rindex(suffix[0])] + suffix
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


def get_teanglann_definition(word):

    candidates = get_foclóir_candidates(word)
    print()
    print(f'{Back.YELLOW}{Fore.BLACK}{word}{Style.RESET_ALL} foclóir:', candidates)

    parts_of_speech = OrderedDict()
    definitions = []
    genders = []

    for subentries, subentry_labels in get_teanglann_subentries(word):
        first_line = subentries[0]
        gender = None
        types = OrderedDict()  # using as ordered set
        if first_line.find(title="feminine") and first_line.find(title="masculine"):
            # 'thar': has 'thairis (m) thairsti (f)' and is not a noun
            pass
        elif first_line.find(title="feminine") or first_line.find(title="masculine"):
            soup_fb = get_definition_soup(word, 'teanglann', lang='ga-fb')
            entry_fb = soup_fb.find(class_='entry')
            types['Noun'] = True
            if first_line.find(title="feminine"):
                gender = 'nf'
                k_lookup = 'bain'
            elif first_line.find(title="masculine"):
                gender = 'nm'
                k_lookup = 'fir'
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
                defn = '/'.join([tgw for tgw in re.split('[,;] *', trans_text) if re.sub('\s*\(.*?\)\s*', '', tgw) in candidates])
                if len(transs) > 1:
                    formatted_text = f'X{len(transs)} {formatted_text}'
                if defn:
                    if maybe_to + defn not in definitions:
                        print(f'{label}{Fore.GREEN}{maybe_to}{defn}{Style.RESET_ALL} [{formatted_text}]')
                        definitions.append(maybe_to + defn)
                else:
                    defn = '/'.join([fcw for fcw in candidates if fcw in raw_text])
                    if False and defn:
                        # this picks up 'persist' instead of 'persisting/persistent' for 'leanúnach'
                        print(f'{label}{maybe_to}{defn}[{formatted_text}]')
                        definitions.append(maybe_to + defn)
                    else:
                        print(f'{label}[{formatted_text}]')
        if gender and gender not in genders:
            genders.append(gender)
        for k, v in types.items():
            if isinstance(v, dict) and k in parts_of_speech:
                parts_of_speech[k].update(v)
            else:
                parts_of_speech[k] = v
    return print_types(parts_of_speech), '\n'.join(definitions), '\n'.join(genders)


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
        print_verbal_nouns()
    elif True:
        populate_AUTO_comparison()
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
        get_teanglann_definition('leanúnach')
    elif False:
        # some complex abbreviations here
        get_teanglann_definition('dírigh')
    elif False:
        # verb intransitive + transitive, with extra entry with intransitive verb only
        # expecting to get 'Verb - Transitive & Intransitive' back
        print(get_teanglann_definition('lonnaigh')[0])
    else:
        # not getting 'cream'
        get_teanglann_definition('uachtar')
