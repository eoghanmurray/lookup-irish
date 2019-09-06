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

# If modifying these scopes, delete the file token.pickle.
SCOPES = ['https://www.googleapis.com/auth/spreadsheets']

# The ID and range of a sample spreadsheet.
SAMPLE_SPREADSHEET_ID = '1kiZlZp8weyILstvtL0PfIQkQGzuG7oZfP8n_qkMFAWo'
SAMPLE_RANGE_NAME = '6450-most-frequent-irish-words!B2:D'


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
            if False and len(row) == 1:
                # only EN column is defined
                print(f'Looking up B{n}: {row[0]}')
                pass
            elif row[0] == 'N':  # testing
                values = [
                    [
                        'TEST AUTO'
                    ],
                ]
                body = {
                    'values': values
                }
                result = sheet.values().update(
                    spreadsheetId=SAMPLE_SPREADSHEET_ID, range=f'D{cell_no}',
                    valueInputOption='RAW', body=body).execute()
                print('{0} cells updated.'.format(result.get('updatedCells')))
                break
                count += 1

            if count == 20:
                break


def get_definition_soup(word, dictionary, lang='ga'):
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
            href += '/en/search/ei/adv?inlanguage=ga&q=' + word
    local_dir = os.path.join(
        os.path.dirname(__file__),
        '.webcache',
        dictionary + '-' + lang
    )
    local_path = os.path.join(local_dir, word + '.html')
    if not os.path.exists(local_dir):
        os.makedirs(local_dir)
    if os.path.exists(local_path):
        contents = open(local_path, 'r').read()
        soup = BeautifulSoup(contents, features='html5lib')
    else:
        page = requests.get(href)
        soup = BeautifulSoup(page.text, features='html5lib')
        # writing the soup rather than raw response as it converts to utf8
        open(local_path, 'w').write(soup.prettify())
    return soup


def get_teanglann_definition(word):
    soup = get_definition_soup(word, 'teanglann', lang='ga')
    for entry in soup.find_all(class_='entry'):

        # expand abbreviations
        for abbr in entry.find_all(title=True):
            abbr_text = abbr.text.strip()
            abbr_title = abbr['title'].strip()
            if len(abbr_text) > 4 or len(abbr_text) > len(abbr_title):
                manual_debug()
            abbr.string.replace_with(abbr_title)
            if abbr.next_sibling and abbr.next_sibling.string.lstrip().startswith('.'):
                abbr.next_sibling.string.replace_with(abbr.next_sibling.string.lstrip()[1:])

        if not entry.text.strip().startswith(word):
            manual_debug()

        split_point = None
        type_ = gender = None
        if entry.find(title="feminine") or entry.find(title="masculine"):
            soup_fb = get_definition_soup(word, 'teanglann', lang='ga-fb')
            entry_fb = soup_fb.find(class_='entry')
            type_ = 'Noun'
            if entry.find(title="feminine"):
                gender = 'nf'
                k_lookup = 'bain'
                split_point = entry.find(title="feminine")
            elif entry.find(title="masculine"):
                gender = 'nm'
                k_lookup = 'fir'
                split_point = entry.find(title="masculine")
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
        elif entry.find(title="adjective"):
            type_ = 'Adjective'
            gender = 'a'
            dec = entry.find(title="adjective").next_sibling
            # to check: think it only goes up to a3
            if dec.strip().strip('.') in ['1', '2', '3', '4']:
                gender += dec.strip().strip('.')
            else:
                manual_debug()
            split_point = entry.find(title="adjective")
        elif (entry.find(title="transitive verb") and
              entry.find(title="and intransitive")):
            type_ = 'Verb - Transitive & Intransitive'
        elif entry.find(title="transitive verb"):
            type_ = 'Verb - Transitive'
        elif entry.find(title="conjunction"):
            type_ = 'Conjugation'

        heading = ''
        if split_point:
            split_point_top = split_point
            while split_point_top.parent != entry:
                split_point_top = split_point_top.parent
            prev_sibs = [ps for ps in
                         split_point_top.previous_siblings]  # copy
            for preamble in reversed(prev_sibs):
                heading += preamble.extract().string.strip()
            split_point.extract()

        entry_text = entry.text.replace('\n', '')
        entry_text = re.sub('[ ]{2,}', ' ', entry_text).strip()
        entry_text = entry_text.replace('~', word)

        mainentry = None
        subentries = []
        for n in range(1, 1000):
            if f'{n}.' in entry_text:
                pre, entry_text = entry_text.split(f'{n}.', 1)
                pre = pre.strip()
                entry_text = entry_text.strip()
                if n == 1:
                    mainentry = pre
                else:
                    subentries.append(pre)
            else:
                if n == 1:
                    mainentry = entry_text
                else:
                    subentries.append(entry_text)
                break

        print()
        print(word, type_, gender)
        if heading:
            print('::Heading:', heading)
        if mainentry:
            print('::Main:', mainentry)
        if entry.find(class_='trans'):
            for trans in entry.find_all(class_='trans'):
                if trans and trans.text.strip():
                    print(trans.text.strip())
        else:
            for i, subentry in enumerate(subentries):
                print(f'{i+1}.', subentry)


def manual_debug():
    import sys
    import pdb
    p = pdb.Pdb()
    p.set_trace(sys._getframe().f_back)


if __name__ == '__main__':
    if False:
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
    elif True:
        # something easy?
        get_teanglann_definition('bothán')
    else:
        main()
