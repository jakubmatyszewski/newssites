import os
from dotenv import load_dotenv
from datetime import datetime
from urllib.request import urlopen
from bs4 import BeautifulSoup as soup
from googleapiclient.discovery import build
from google.oauth2 import service_account

load_dotenv()

SITES = {'tvn24':
         {
             'url': 'https://tvn24.pl',
             'headline_selector': 'top-story__header'
         },
         'tvp.info':
         {
             'url': 'https://tvp.info/',
             'headline_selector': 'main-module__news-title'}
         }

# If modifying these scopes, delete the file token.pickle.
SCOPES = ['https://www.googleapis.com/auth/drive',
          'https://www.googleapis.com/auth/spreadsheets']

# The ID and range of a sample spreadsheet.
SPREADSHEET_ID = os.getenv('SPREADSHEET_ID')

WORKDIR = os.getenv('WORKDIR')


def append_spreadsheet(service, range_name, values):
    body = {'values': values}
    result = service.spreadsheets().values().append(
        spreadsheetId=SPREADSHEET_ID, range=range_name,
        valueInputOption="RAW", body=body).execute()
    print('{} cells appended.'.format(
        result.get('updates').get('updatedCells'))
    )
    return True


def scrape_headline(url, selector):
    # opening up connection, grabbing the page
    client = urlopen(url)
    page_html = client.read()
    client.close()

    # html parsing
    page_soup = soup(page_html, 'html.parser')
    headline = page_soup.find(class_=selector).text.strip()

    return headline


def login_to_google_sheets():
    creds = service_account.Credentials.from_service_account_file(
        f'{WORKDIR}creds.json', scopes=SCOPES)

    service = build('sheets', 'v4', credentials=creds)
    sheet = service.spreadsheets()
    return service, sheet


def main():
    time = datetime.now().strftime("%m/%d/%Y, %H:%M:%S")
    print(f'\n{time}')
    service, sheet = login_to_google_sheets()
    for site in SITES.keys():
        print(site)
        range_name = f'{site}!A:B'
        headline = scrape_headline(
            SITES[site]['url'],
            SITES[site]['headline_selector']
        )

        result = sheet.values().get(spreadsheetId=SPREADSHEET_ID,
                                    range=range_name).execute()
        existing_values = result.get('values', [])
        last_headline = existing_values[-1][0]
        values = [[headline, time]]
        if not existing_values:
            print('No data found.')
        elif headline == last_headline:
            print("Headline didn't change.")
            continue
        append_spreadsheet(service, range_name, values)
    return True


if __name__ == "__main__":
    main()
