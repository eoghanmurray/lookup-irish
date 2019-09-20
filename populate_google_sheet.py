#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import time
import pickle
from googleapiclient.discovery import build
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from collections import namedtuple
import os

from teanglann import get_teanglann_senses
from teanglann import assign_verbal_noun, assign_plural_genitive
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
        range=range,
        valueInputOption='RAW',
        body=body).execute()
    print('{0} cells updated.'.format(result.get('updatedCells')))
    # TODO something intelligent here to avoid hitting Google API window
    time.sleep(0.4)


def populate_empty(refresh=True, limit=15):
    sheet = get_sheet()
    rows = get_range(sheet)
    if rows:
        count = 0
        values = []
        range_start = None
        for n, row in enumerate(rows):
            cell_no = n + 2  # +1 for 0 index, +1 as we are skipping header
            insert_now = False
            if row.GA and (
                    not row.EN or
                    (refresh and row.EN.endswith('[AUTO]'))
                    ):
                senses = get_teanglann_senses(row.GA)

                parts_of_speech = {}
                for sense in senses:
                    for k, v in sense['type'].items():
                        if isinstance(v, dict) and k in parts_of_speech:
                            parts_of_speech[k].update(v)
                        else:
                            parts_of_speech[k] = v
                PoS = join_parts_of_speech(parts_of_speech)

                EN = '\n'.join([d['definitions'] for d in senses])
                if not EN:
                    # old return_raw=True
                    EN = '\n'.join([d['raw_definitions'] for d in senses])
                Gender = '\n'.join([d['genders'] for d in senses])

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


def populate_non_EN(limit=-1):
    sheet = get_sheet()
    rows = get_range(sheet)
    if rows:
        count = 0
        values = []
        range_start = range_end = None
        for n, row in enumerate(rows):
            cell_no = n + 2  # +1 for 0 index, +1 as we are skipping header
            insert_now = False
            if row.GA:
                senses = get_teanglann_senses(row.GA)

                parts_of_speech = {}
                genitive_vns = []
                genders = []
                for sense in senses:
                    use_sense = False
                    for d in sense['definitions']:
                        if not row.EN or d in row.EN:
                            use_sense = True
                    if not use_sense:
                        continue
                    for k, v in sense['types'].items():
                        if isinstance(v, dict) and k in parts_of_speech:
                            parts_of_speech[k].update(v)
                        else:
                            parts_of_speech[k] = v
                    if (sense.get('verbal-noun', None) and
                        'Verb' in row.PoS and 'ransitive' in row.PoS):
                        inf = 'ag ' + sense['verbal-noun']
                        if inf in genitive_vns:
                            import pdb; pdb.set_trace();
                        if inf not in genitive_vns:
                            genitive_vns.append(inf)
                    if sense['gender'] and \
                       'Noun' in sense['types'] and \
                       'Noun' in row.PoS:
                        genders.append(sense['gender'])
                        if sense.get('genitive-plural', None):
                            genitive_vns.append(sense['genitive-plural'])
                    if sense['gender'] and \
                       'Noun' in sense['types'] and \
                       'Noun' in row.PoS:
                        genders.append(sense['gender'])

                PoS = join_parts_of_speech(parts_of_speech)
                GenitiveVN = '\n'.join(genitive_vns)

                update = {}
                if GenitiveVN and GenitiveVN != row.GenitiveVN:
                    update['GenitiveVN'] = GenitiveVN
                if genders and \
                   (not row.Gender or row.Gender in ['nf', 'nm']):
                    update['Gender'] = '\n'.join(genders)
                if PoS and ('[AUTO]' in row.EN or not row.PoS):
                    update['PoS'] = PoS

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


def populate_AUTO_comparison(refresh=False):
    """
Populate the AUTO column to compare against existing manual entries
    """
    sheet = get_sheet()
    rows = get_range(sheet)
    if rows:
        count = 0
        for n, row in enumerate(rows):
            cell_no = n + 2  # +1 for 0 index, +1 as we are skipping header
            if row.AUTO != '' and not refresh:
                continue
            if not row.EN or row.EN.endswith('[AUTO]'):
                continue
            if n > 200:
                senses = get_teanglann_senses(row.GA)

                parts_of_speech = {}
                for sense in senses:
                    for k, v in sense['types'].items():
                        if isinstance(v, dict) and k in parts_of_speech:
                            parts_of_speech[k].update(v)
                        else:
                            parts_of_speech[k] = v
                PoS = join_parts_of_speech(parts_of_speech)

                EN = '\n'.join([d['definitions'] for d in senses])
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


if __name__ == '__main__':
    if True:
        populate_non_EN(limit=100)
    elif False:
        populate_AUTO_comparison(refresh=True)
    elif True:
        populate_empty(limit=-1)
