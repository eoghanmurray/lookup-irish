#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import time
import pickle
from googleapiclient.discovery import build
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from collections import namedtuple
import os
import argparse
from bs4 import BeautifulSoup
import re

from teanglann import get_teanglann_senses
from teanglann import assign_adjectival_variants
from teanglann import join_parts_of_speech
from irish_lang import format_declensions

# If modifying these scopes, delete the file token.pickle.
SCOPES = ['https://www.googleapis.com/auth/spreadsheets']

# The ID and range of a sample spreadsheet.
SPREADSHEET_ID = '1kiZlZp8weyILstvtL0PfIQkQGzuG7oZfP8n_qkMFAWo'
RANGE = '6450-most-frequent-irish-words!A1:I'

ALPHABET = 'ABCDEFGHIJKLMNOPQRSTUVWXYZ'
COLUMN_KEY = {}
COL_HEAD = {}
HAIR_SLASH = ' / '  # unicode, equivalent to '&hairsp;/&hairsp;'

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


def get_range(
        sheet,
        spreadsheet_id=SPREADSHEET_ID,
        spreadsheet_range=RANGE
):
    result = sheet.values().get(spreadsheetId=spreadsheet_id,
                                range=spreadsheet_range).execute()
    values = result.get('values', [])
    if not values:
        return False
    FIRST_ROW_SIG = ' '.join([v.replace(' ', '_') for v in values[0]])
    for col, letter in zip(values[0], ALPHABET):
        COLUMN_KEY[col] = letter
        COL_HEAD[letter] = col
    RowTup = namedtuple('RowTup', FIRST_ROW_SIG)
    for v in values[1:]:
        v_ext = (v + [''] * len(values[0]))[:len(values[0])]
        yield RowTup(*v_ext)


def insert_block(sheet, range, values):
    body = {
        'values': values,
    }
    result = sheet.values().update(
        spreadsheetId=SPREADSHEET_ID,
        range=RANGE.split('!')[0] + '!' + range,
        valueInputOption='RAW',
        body=body).execute()
    print('{0} cells updated.'.format(result.get('updatedCells')))
    # TODO something intelligent here to avoid hitting Google API window
    # <HttpError 429 when requesting .. returned
    # "Quota exceeded for quota group 'WriteGroup' and
    # limit 'USER-100s' of service 'sheets.googleapis.com' for consumer
    time.sleep(0.8)


def filter_some_usages(EN):
    """
Some subjective removal of usage types
for the purposes of the 6500 word list
    """
    bad_markers = [
        # 'ecclesiastical', actually not a good idea:
        # reachtaire
        # - rector (ecclesiastical)
        # - master of ceremonies
    ]
    ret = '\n'.join([line for line in EN.split('\n') if
                      (not line.endswith(')')
                       or
                       line.rsplit('(', 1)[1].rstrip(')')
                       not in bad_markers)])
    if ret:
        return ret
    return EN


def populate_empty(refresh=True, limit=15, start_row=2, single_GA=None):
    if single_GA:
        limit = 1
    sheet = get_sheet()
    rows = get_range(sheet)
    if rows:
        count = 0
        values = []
        range_start = None
        for n, row in enumerate(rows):
            cell_no = n + 2  # +1 for 0 index, +1 as we are skipping header
            if cell_no < start_row:
                continue
            insert_now = False
            if single_GA and row.GA != single_GA:
                pass
            elif row.GA and (
                    not row.EN or
                    (refresh and row.EN.endswith('[AUTO]'))
                    ):
                senses, _, _, foclóir_candidates = get_teanglann_senses(
                    row.GA, return_counts=True)

                parts_of_speech = {}
                for sense in senses:
                    for k, v in sense['types'].items():
                        if isinstance(v, dict) and k in parts_of_speech:
                            parts_of_speech[k].update(v)
                        else:
                            parts_of_speech[k] = v
                PoS = join_parts_of_speech(parts_of_speech)

                EN = '\n'.join([
                    '\n'.join(sense['definitions'])
                    for sense in senses if
                    sense['definitions']
                ])
                if not EN:
                    # old return_raw=True
                    EN = '\n'.join([
                        '\n'.join(sense['raw_definitions'])
                        for sense in senses
                    ])
                    if not EN and len(foclóir_candidates) == 1:
                        # choose a definite single one
                        EN = foclóir_candidates[0]
                    elif foclóir_candidates:
                        EN += '<br>[' + ' / '.join(foclóir_candidates) + ']'
                else:
                    EN = filter_some_usages(EN)
                EN = EN.replace('\n', '\n<li>')
                Gender = '\n'.join([d['gender'] for d in senses if d['gender']])

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


def populate_meta(limit=-1, start_row=2, single_GA=None):
    if single_GA:
        limit = 1
    sheet = get_sheet()
    rows = get_range(sheet)
    if rows:
        verb_definitions = {}
        count = 0
        values = []
        range_start = range_end = None
        for n, row in enumerate(rows):
            cell_no = n + 2  # +1 for 0 index, +1 as we are skipping header
            if cell_no < start_row:
                continue
            insert_now = False
            if single_GA and row.GA != single_GA:
                pass
            elif row.GA:
                senses, teanglann_count, foclóir_count, foclóir_candidates = \
                                      get_teanglann_senses(row.GA,
                                                           return_counts=True)

                parts_of_speech = {}
                genitive_plural_raw = {}
                # html.parser doesn't add <html><body>
                genitive_vn_soup = BeautifulSoup(row.GenitiveVN, 'html.parser')
                for existing in genitive_vn_soup.find_all('div'):
                    if {'vn', 'nf', 'nm', 'adj'}.intersection(existing['class']):
                        existing.extract()
                if genitive_vn_soup.string:
                    genitive_vn_soup.string.insert_after('\n')
                genders = []
                for sense in senses:
                    use_sense = False
                    for d in sense['definitions']:
                        for sd in re.sub(r'^to ', '', d).split(HAIR_SLASH):  # saol life/world vs. life/time/world
                            if not row.EN or sd in row.EN:
                                use_sense = True
                    if not use_sense:
                        if (len(senses) == 1 and
                            (not row.PoS or (
                                'types' in sense and (
                                    sense['types'].keys() == {row.PoS} or
                                    row.PoS == join_parts_of_speech(
                                        sense['types']
                                    )
                                ))
                            ) and (
                                not row.Gender or
                                sense['gender'] == row.Gender
                            )):
                            use_sense = True
                    if not use_sense:
                        continue
                    for k, v in sense['types'].items():
                        if isinstance(v, dict) and k in parts_of_speech:
                            parts_of_speech[k].update(v)
                        else:
                            parts_of_speech[k] = v
                    if (sense.get('verbal-noun', None) and
                        (row.PoS.strip() == 'Verb' or
                         ('Verb' in row.PoS and 'ransitive' in row.PoS))):
                        for vt in sense['verbal-noun-examples'][:3]:
                            if vt not in str(genitive_vn_soup):
                                inf = '<div class="vn">' + vt + '</div>'
                                inf = BeautifulSoup(inf, 'html.parser')
                                if str(genitive_vn_soup):
                                    genitive_vn_soup.append('\n')
                                genitive_vn_soup.append(inf)
                        if row.GA not in verb_definitions:
                            verb_definitions[row.GA] = '\n'.join(sense['definitions'])
                    if sense['gender'] and \
                       'Noun' in sense['types'] and \
                       ('Noun' in row.PoS or not row.PoS):
                        if sense['gender'] not in genders:
                            genders.append(sense['gender'])
                        if sense.get('genitive-plural', None):
                            if 'nominative plural' in sense['genitive-plural-raw'] and \
                               sense['genitive-plural-raw']['plural strength'] == 'unknown':
                                print('CHECK no strong/weak detected:', row.GA, row.Gender)
                            if not genitive_plural_raw:
                                if str(genitive_vn_soup):
                                    genitive_vn_soup.append('\n')
                                genitive_vn_soup.append(
                                    BeautifulSoup(
                                        sense['genitive-plural'],
                                        'html.parser'
                                    )
                                )
                                genitive_plural_raw.update(
                                    sense['genitive-plural-raw']
                                )
                            else:
                                for k, v in sense['genitive-plural-raw'].items():
                                    if not {'nominative', 'genitive', 'singular', 'plural'}.issuperset(k.split()):
                                        # don't compare 'plural strength' etc.
                                        continue
                                    if genitive_plural_raw.get(k, None) != v:
                                        if str(genitive_vn_soup):
                                            genitive_vn_soup.append('\n')
                                        genitive_vn_soup.append(
                                            BeautifulSoup(
                                                sense['genitive-plural'],
                                                'html.parser'
                                            )
                                        )
                                        sgp = sense['genitive-plural-raw']
                                        genitive_plural_raw = sgp
                                        break
                    if sense['gender'] and \
                       'Adjective' in sense['types'] and \
                       'Adjective' in row.PoS.replace('Possessive Adj', ''):
                        if sense['gender'] not in genders:
                            genders.append(sense['gender'])
                        adj = assign_adjectival_variants(row.GA, format='html')
                        adj = BeautifulSoup(adj, 'html.parser')
                        if str(adj) not in str(genitive_vn_soup):
                            if str(genitive_vn_soup):
                                genitive_vn_soup.append('\n')
                            genitive_vn_soup.append(adj)

                PoS = join_parts_of_speech(parts_of_speech)
                GenitiveVN = str(genitive_vn_soup).strip()
                GenitiveVN = re.sub('\n+', '\n', GenitiveVN)

                update = {}
                if GenitiveVN != row.GenitiveVN:
                    update['GenitiveVN'] = GenitiveVN
                if teanglann_count and row.NTeanglann != str(teanglann_count):
                    update['NTeanglann'] = teanglann_count
                if foclóir_count and row.NFocloir != str(foclóir_count):
                    update['NFocloir'] = foclóir_count
                if genders and \
                   (not row.Gender or row.Gender in ['nf', 'nm']):
                    ng = '\n'.join(genders)
                    if row.Gender and len(genders) != len(row.Gender.split('\n')):
                        print(f'CHECK 1: {row.GA} not updating {row.Gender} to {ng}')
                    elif 'nf' in row.Gender and 'nf' not in ng:
                        print(f'CHECK 2: {row.GA} not updating {row.Gender} to {ng}')
                    elif 'nm' in row.Gender and 'nm' not in ng:
                        print(f'CHECK 3: {row.GA} not updating {row.Gender} to {ng}')
                    else:
                        update['Gender'] = ng

                if 'Verbal Noun' in parts_of_speech and \
                   parts_of_speech['Verbal Noun'] != True and \
                   '<aside class="verbal-noun-info">' not in row.EN:
                    vb = parts_of_speech['Verbal Noun'].split('of ', 1)[-1]
                    if vb not in verb_definitions:
                        # e.g. cónaí vs. cónaigh
                        # actually cónaí (the 'verbal noun') is more important
                        print('WARNING: missing higher definition of '
                              f"{vb} for it's verbal noun {row.GA}")
                    elif vb not in ['gáir', 'oibrigh', 'dearc']:
                        # cheating as with --meta we're not supposed
                        # to update definition
                        vdef = verb_definitions[vb].split('\n')[0]
                        update['EN'] = row.EN + '\n' + \
                            '<aside class="verbal-noun-info">' + \
                            f'verbal noun of {vb} (' + vdef + \
                            ')</aside>'

                if PoS and (
                        not row.PoS or
                        ('[AUTO]' in row.EN and row.PoS != PoS)):
                    update['PoS'] = PoS
                elif 'Verbal Noun of' in PoS and \
                     'Verbal Noun of' not in row.PoS:
                    del parts_of_speech['Verbal Noun']
                    if row.PoS == join_parts_of_speech(parts_of_speech):
                        update['PoS'] = PoS
                        print(row.GA, 'adding verbal noun:', PoS)
                    else:
                        print(row.GA, 'NOT adding verbal noun:', row.PoS, PoS)

                if update:
                    column_start = False
                    column_end = False
                    value = []
                    vfill = []
                    for L in ALPHABET:
                        if L not in COL_HEAD:
                            break
                        C = COL_HEAD[L]
                        if C in update:
                            if column_start is False:
                                column_start = C
                            column_end = C
                            if vfill:
                                value.extend(vfill)
                                vfill = []
                            value.append(update[C])
                        elif column_start is not False:
                            # keep current value
                            vfill.append(getattr(row, C))

                    COL_START = COLUMN_KEY[column_start]
                    COL_END = COLUMN_KEY[column_end]
                    if values and \
                       ((range_start and not range_start.startswith(COL_START))
                        or (range_end and not range_end.startswith(COL_END))):
                        # change of column width
                        insert_block(sheet, range_start + ':' + range_end, values)
                        values = []
                        range_start = None

                    values.append(value)
                    if not range_start:
                        range_start = COL_START + str(cell_no)
                    range_end = COL_END + str(cell_no)
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


def populate_AUTO_comparison(refresh=False, single_GA=None, start_row=2):
    """
Populate the AUTO column to compare against existing manual entries
    """
    if single_GA:
        limit = 1
    sheet = get_sheet()
    rows = get_range(sheet)
    if rows:
        count = 0
        for n, row in enumerate(rows):
            cell_no = n + 2  # +1 for 0 index, +1 as we are skipping header
            if cell_no < start_row:
                continue
            if single_GA and row.GA != single_GA:
                pass
            elif row.AUTO != '' and not refresh:
                pass
            elif not row.EN or row.EN.endswith('[AUTO]'):
                pass
            elif n > 200:
                senses = get_teanglann_senses(row.GA)

                parts_of_speech = {}
                for sense in senses:
                    for k, v in sense['types'].items():
                        if isinstance(v, dict) and k in parts_of_speech:
                            parts_of_speech[k].update(v)
                        else:
                            parts_of_speech[k] = v
                PoS = join_parts_of_speech(parts_of_speech)

                EN = '\n'.join([
                    '\n'.join(sense['definitions'])
                    for sense in senses if
                    sense['definitions']
                ])
                EN = filter_some_usages(EN)
                EN = EN.replace('\n', '<li>\n')

                Gender = '\n'.join([d['genders'] for d in senses])

                if False:
                    print()
                    print(f'C{cell_no}:E{cell_no}')
                    print(row.GA)
                    print(row.EN)
                    print(' vs.')
                    print(EN)
                else:
                    if EN:
                        if EN == row.EN:
                            value = ''
                        else:
                            value = EN
                    else:
                        value = '[NONE]'
                    if value != row.AUTO:
                        body = {
                            'values': [[value]],
                        }
                        result = sheet.values().update(
                            spreadsheetId=SPREADSHEET_ID,
                            range=f'{COLUMN_KEY["AUTO"]}{cell_no}',
                            valueInputOption='RAW',
                            body=body).execute()
                        print('{0} cells updated.'.format(
                            result.get('updatedCells'))
                        )
                        count += 1

            if count == 100:
                break


def test_ending(ending):
    """
Look at a particular ending to see whether it should be
highlighted as a typical masculine or feminine ending
    """
    sheet = get_sheet()
    rows = get_range(sheet)
    feminine = []
    masculine = []
    unknown = []
    total_count = 0

    if not rows:
        return 'No rows'
    for n, row in enumerate(rows):
        if row.GA.endswith(ending) and \
           'Noun' in row.PoS:
            total_count += 1
            if 'nf' in row.Gender:
                feminine.append(row.GA)
            if 'nm' in row.Gender:
                masculine.append(row.GA)
            elif 'nf' not in row.Gender:
                unknown.append(row.GA)
    print(f'Sample: {total_count}')
    if not total_count:
        return
    print('Fem: %.2f (%d)' % (len(feminine)/total_count, len(feminine)))
    if len(feminine) < 13:
        print(feminine)
    print('Mas: %.2f (%d)' % (len(masculine)/total_count, len(masculine)))
    if len(masculine) < 13:
        print(masculine)
    if unknown:
        print('Unk: %.2f - %r' % (len(unknown)/total_count, unknown))


def declensions_with_strong_plural():
    """
Break down strong/weak plurals by declensions
    """
    sheet = get_sheet()
    rows = get_range(sheet)
    if not rows:
        return 'No rows'
    from collections import defaultdict
    counts = defaultdict(int)
    strongs = defaultdict(int)
    gender = ['nf', 'nm']
    decl = ['1', '2', '3', '4', '5']
    for n, row in enumerate(rows):
        for g in gender:
            for d in decl:
                c = g + d
                if c in row.Gender:
                    counts[c] += 1
                    if 'strong plural' in row.GenitiveVN:
                        strongs[c] += 1
                    break
            else:
                if g in row.Gender:
                    counts[g] += 1
                    if 'strong plural' in row.GenitiveVN:
                        strongs[g] += 1
    for d in counts:
        print('Strong in %s: %.2f (%d)' % (d, strongs[d] / counts[d], counts[d]))


parser = argparse.ArgumentParser(
    description='''Populate source spreadsheet for Anki deck
requires access to shared spreadsheet or you could
create your own wordlist in Google Sheets by adding
heading row:
GA|PoS|EN|Gender|Tags|GenitiveVN|NTeanglann|NFocloir|AUTO
and filling in the GA column with words you wish to be translated
''')

arg = parser.add_argument

arg(
    '--translate',
    help='''Fills in translation for empty English cells and updates
existing cells ending with the text '[AUTO]'
''',
    action='store_true')

arg(
    '--meta',
    help='''Update the Gender/GenitiveVN/NTeanglann/NFocloir
columns based on the PoS column. Always refreshes.''',
    action='store_true')

arg(
    '--compare',
    help='Fills in an additional AUTO column with English '
    'translation for comparison',
    action='store_true')

arg(
    '--GA', '--irish-word',
    help='Selectively update a single word')

arg(
    '-l', '--limit',
    type=int,
    help='''How many spreadsheet rows to update
set to -1 to update all
''',
    default=-1
)

arg(
    '--start-row',
    type=int,
    help='''Don't restart from the top, but upon this row
''',
    default=2
)

arg(
    '--no-refresh',
    help="Don't update existing results",
    action='store_true',
    default=False
)

arg(
    '--force-noun',
    type=int,
    help='''Populate GenitiveVN column even if we don't find a matching sense''',
    default=2
)

arg(
    '--test-ending',
    help='See what the likelyhood that the top Nouns with this ending have a particular gender')


if __name__ == '__main__':
    args = vars(parser.parse_args())
    refresh = not args['no_refresh']
    kwargs = {
        'limit': args['limit'],
        'refresh': refresh,
        'start_row': args['start_row'],
    }
    if 'GA' in args:
        kwargs['single_GA'] = args['GA']
    if args['meta']:
        if not refresh:
            print('Error, can\'t turn off refresh for populate_meta')
        else:
            kwargs.pop('refresh')
            populate_meta(**kwargs)
    elif args['translate']:
        populate_empty(**kwargs)
    elif args['compare']:
        populate_AUTO_comparison(**kwargs)
    elif args['test_ending']:
        test_ending(args['test_ending'])
    else:
        #declensions_with_strong_plural()
        print('Please choose --translate, --meta or --compare')
