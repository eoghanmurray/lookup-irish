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
from collections import OrderedDict

# If modifying these scopes, delete the file token.pickle.
SCOPES = ['https://www.googleapis.com/auth/spreadsheets']

# The ID and range of a sample spreadsheet.
SAMPLE_SPREADSHEET_ID = '1kiZlZp8weyILstvtL0PfIQkQGzuG7oZfP8n_qkMFAWo'
SAMPLE_RANGE_NAME = '6450-most-frequent-irish-words!B2:E'


def main():
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
    result = sheet.values().get(spreadsheetId=SAMPLE_SPREADSHEET_ID,
                                range=SAMPLE_RANGE_NAME).execute()
    values = result.get('values', [])

    if not values:
        print('No data found.')
    else:
        print('GA, EN:')
        count = 0
        for n, row in enumerate(values):
            cell_no = n + 2  # 1 for 0 index, 1 for range offset
            if len(row) == 1:  # only GA column is defined
                PoS, EN, Gender = get_teanglann_definition(row[0])
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
                        spreadsheetId=SAMPLE_SPREADSHEET_ID,
                        range=f'C{cell_no}:E{cell_no}',
                        valueInputOption='RAW',
                        body=body).execute()
                    print('{0} cells updated.'.format(result.get('updatedCells')))
                    count += 1

            if count == 5:
                break


def get_definition_soup(word, dictionary, lang='ga', page_no=1):
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
        local_path = os.path.join(local_dir, f'{word}-{page_no}.html')
    else:
        local_path = os.path.join(local_dir, word + '.html')
    if not os.path.exists(local_dir):
        os.makedirs(local_dir)
    if os.path.exists(local_path):
        contents = open(local_path, 'r').read()
        soup = BeautifulSoup(contents, features='html5lib')
    else:
        page = requests.get(href, headers=headers)
        soup = BeautifulSoup(page.text, features='html5lib')
        # writing the soup rather than raw response as it converts to utf8
        open(local_path, 'w', encoding='utf-8').write(soup.prettify())
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
            else:
                imprecise_match = True
        if imprecise_match or len(lis) < 20:
            break
    return candidates


def get_teanglann_definition(word):

    candidates = get_foclóir_candidates(word)
    print(word, 'folóir:', candidates)

    soup = get_definition_soup(word, 'teanglann', lang='ga')
    parts_of_speech = []
    definitions = []
    genders = []
    for entry in soup.find_all(class_='entry'):

        # expand abbreviations
        for abbr in entry.find_all(title=True):
            abbr_text = abbr.text.strip()
            abbr_title = abbr['title'].strip()
            if (len(abbr_text) > 4 and not abbr_title.startswith(abbr_text)) or \
                len(abbr_text) > len(abbr_title):
                manual_debug()
            abbr.string.replace_with(abbr_title)
            if abbr.next_sibling and abbr.next_sibling.string.lstrip().startswith('.'):
                abbr.next_sibling.string.replace_with(abbr.next_sibling.string.lstrip()[1:])

        if not entry.text.strip().lower().startswith(word.lower()):
            manual_debug()

        subentries = [soup.new_tag('div')]
        subentry_labels = ['head']
        n = 1
        nxs = 'abcdefghijklmnopqrstuvwxyz'
        nxi = 0
        for node in entry.contents[:]:
            if hasattr(node, 'get_text'):
                node_text = node.get_text()
            else:
                node_text = node.string
            if f'{n}.' in node_text:
                pre, post = node_text.split(f'{n}.', 1)
                if pre.strip():
                    subentries[-1].append(pre.strip())
                subentries.append(soup.new_tag('div'))
                subentry_labels.append(f'{n}.')
                nxi = 0
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
                    subentry_labels.append(f'{n-1}.({nxs[nxi]})')
                else:
                    subentry_labels[-1] = f'{n-1}.({nxs[nxi]})'
                if post.strip().lstrip(')'):
                    subentries[-1].append(post.strip())
                nxi += 1
            else:
                subentries[-1].append(node)

        first_line = subentries[0]
        gender = None
        types = OrderedDict()  # using as ordered set
        if first_line.find(title="feminine") or first_line.find(title="masculine"):
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
            if dec.strip().strip('.') in ['1', '2', '3', '4']:
                gender += dec.strip().strip('.')
            elif dec.strip():
                manual_debug()
        if (first_line.find(title="transitive verb") and
              first_line.find(title="and intransitive")):
            types['Verb - Transitive & Intransitive'] = True
        elif first_line.find(title="transitive verb"):
            types['Verb - Transitive'] = True
        elif first_line.find(title="conjunction"):
            types['Conjugation'] = True

        for subentry in subentries:
            raw_text = clean_text(' '.join(subentry.stripped_strings), word)
            if  raw_text.startswith('verbal noun') and ' of ' in raw_text:
                types['Verbal Noun'] = ' of ' + raw_text.split(' of ', 1)[1].strip()

        print()
        print(word, ' & '.join(types.keys()), gender)
        for label, subentry in zip(subentry_labels, subentries):
            transs = subentry.find_all(class_='trans')
            raw_text = clean_text(' '.join(subentry.stripped_strings), word)
            if len(transs) > 1:
                print(f'{label} [x{len(transs)}', raw_text + ']')
            elif len(transs) < 1:
                print(f'{label} [' + raw_text + ']')
            else:
                trans_text = clean_text(transs[0].get_text(), word)
                maybe_to = ''
                if types and ' & '.join(types.keys()).startswith('Verb'):
                    maybe_to = 'to '
                defn = '/'.join([tgw for tgw in re.split('[,;] *', trans_text) if tgw in candidates])
                if defn:
                    print(f'{label}', maybe_to + defn, '[' + raw_text + ']')
                    definitions.append(maybe_to + defn)
                else:
                    print(f'{label}', '[' + raw_text + ']')
        for type_ in types:
            if type_ not in parts_of_speech:
                if types[type_] is True:
                    parts_of_speech.append(type_)
                else:
                    parts_of_speech.append(type_ + types[type_])
        if gender and gender not in genders:
            genders.append(gender)
    return ' & '.join(parts_of_speech), '\n'.join(definitions), '\n'.join(genders)

def clean_text(text, word):
    text = text.replace('\n', '')
    text = text.replace('~', word)
    text = re.sub('[ ]{2,}', ' ', text).strip()  # repeated spaces
    text = text.rstrip('.')  # trailing dots
    return text.lower().lstrip(')').rstrip('(')


def manual_debug():
    import sys
    import pdb
    p = pdb.Pdb()
    p.set_trace(sys._getframe().f_back)


if __name__ == '__main__':
    if True:
        main()
    elif False:
        # adverb/preposition/adverb in a single entry
        get_teanglann_definition('anall')
    elif False:
        # testing male/female:
        get_teanglann_definition('dóid')
        get_teanglann_definition('dogma')
    elif False:
        # has entry pointing to DUGA
        get_teanglann_definition('doic')
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
    else:
        # get a verbal noun
        # also an example with 5.(a), 5.(b) etc.
        get_teanglann_definition('imeacht')
