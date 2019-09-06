from __future__ import print_function
import pickle
import os.path
from googleapiclient.discovery import build
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request

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
            #if len(row) == 1:  # only EN is defined
            if row[0] == 'N':
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
                #print(f'B{n}: {row[0]}')
                count += 1

            if count == 20:
                break


if __name__ == '__main__':
    main()
