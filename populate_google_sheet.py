#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import pickle
from googleapiclient.discovery import build
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from collections import namedtuple
import os

from teanglann import get_teanglann_definition, assign_plural_genitive
from teanglann import assign_verbal_noun
from irish_lang import format_declensions

# If modifying these scopes, delete the file token.pickle.
SCOPES = ['https://www.googleapis.com/auth/spreadsheets']

# The ID and range of a sample spreadsheet.
SPREADSHEET_ID = '1kiZlZp8weyILstvtL0PfIQkQGzuG7oZfP8n_qkMFAWo'
RANGE = '6450-most-frequent-irish-words!A1:G'

FIRST_ROW_SIG = 'AUTO GA PoS EN Gender GenitiveVN Tags'
COLUMN_KEY = {}
alphabet = 'ABCDEFGHIJKLMNOPQRSTUVWXYZ'
for col, letter in zip(FIRST_ROW_SIG.split(' '), alphabet):
    COLUMN_KEY[col] = letter
RowTup = namedtuple('RowTup', FIRST_ROW_SIG)


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
                PoS, EN, Gender = get_teanglann_definition(
                    row.GA,
                    return_raw=True
                )
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


def populate_pos_gender(limit=-1):
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
                    not row.Pos
                    ):
                PoS, EN, Gender = get_teanglann_definition(row.GA)
                if PoS or Gender:
                    values.append(
                        [
                            PoS,
                            row.EN,  # keep current value
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
            cell_no = n + 2  # +1 for 0 index, +1 as we are skipping header
            insert_now = cell_no % 600 == 0
            if row.GA and (
                    not row.GenitiveVN or
                    refresh
                    ):
                GenitiveVN = ''
                if 'Noun' in row.PoS and ' ' not in row.GA:
                    declensions = assign_plural_genitive(row.GA, html=True)
                    GenitiveVN += format_declensions(declensions)
                if 'Verb' in row.PoS and 'ransitive' in row.PoS and \
                   ' ' not in row.GA:
                    if GenitiveVN:
                        GenitiveVN += '\n'
                    vn = assign_verbal_noun(row.GA)
                    if vn:
                        GenitiveVN += 'ag ' + vn
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
                PoS, EN, Gender = get_teanglann_definition(row.GA)
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
        populate_genitive_verbal_noun(limit=-1)
    elif False:
        populate_AUTO_comparison(refresh=True)
    elif True:
        populate_empty(limit=-1)
