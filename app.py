import os
import boto3
import psycopg2
from dotenv import load_dotenv
from datetime import datetime
from urllib.request import urlopen
from bs4 import BeautifulSoup as soup
from googleapiclient.discovery import build
from google.oauth2 import service_account

load_dotenv()

# Define news sites and headline class.
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

# Define Google Spreadsheets const.
SPREADSHEET_ID = os.getenv('SPREADSHEET_ID')
SCOPES = ['https://www.googleapis.com/auth/drive',
          'https://www.googleapis.com/auth/spreadsheets']

# Define AWS const.
ENDPOINT = os.getenv('AWS_ENDPOINT')
USR = os.getenv('AWS_USER')
REGION = os.getenv('AWS_REGION')
PORT = "5432"
DBNAME = "newssites"

# gets the credentials from .aws/credentials
session = boto3.Session(profile_name='default')
client = boto3.client('rds')


# Generates AWS RDS token.
def get_db_token():
    t = client.generate_db_auth_token(
        DBHostname=ENDPOINT,
        Port=PORT,
        DBUsername=USR,
        Region=REGION)
    return t


def append_db(site, headline, timestamp):
    try:
        conn = psycopg2.connect(
            host=ENDPOINT,
            port=PORT,
            database=DBNAME,
            user=USR,
            password=get_db_token())
        cursor = conn.cursor()
        cursor.execute(f"""
            INSERT INTO {site} (headline, time_stamp)
            VALUES ('{headline}', '{timestamp}');""")
        conn.commit()
        cursor.close()
        conn.close()
    except Exception as e:
        print("Can't connect. Invalid dbname, user or password?")
        print(e)


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
        f'{os.getcwd()}/creds.json', scopes=SCOPES)

    service = build('sheets', 'v4', credentials=creds)
    sheet = service.spreadsheets()
    return service, sheet


def main():
    time_format = "%m/%d/%Y, %H:%M:%S"
    time = datetime.now().strftime(time_format)
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
        # Adjust formatting for DB:
        site = site.replace('.', '')  # db names have no special signs
        db_time = datetime.strptime(time, time_format)
        append_db(site, headline, db_time)
    return True


if __name__ == "__main__":
    main()
