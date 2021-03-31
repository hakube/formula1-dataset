import requests
from bs4 import BeautifulSoup
import pandas as pd
import csv

csv_fields = ['position', 'number', 'driver', 'car', 'laps', 'time', 'points', 'grand_prix', 'year', 'fastest_lap']

with open('formula1_data_races.csv', 'w', encoding='utf-8') as csv_file:
    csv_writer = csv.DictWriter(csv_file, fieldnames=csv_fields, delimiter=',', lineterminator='\n')
    csv_writer.writeheader()

BASE_URL = 'https://www.formula1.com/en/results.html'
SOURCE = 'https://www.formula1.com'

SCORING_SYSTEM = {
    1: 25,
    2: 18,
    3: 15,
    4: 12,
    5: 10,
    6: 8,
    7: 6,
    8: 4,
    9: 2,
    10: 1

}

def get_fastest_lap(race_url):
    fastest_lap_url = str(race_url).replace('race-result.html', 'fastest-laps.html')
    response = requests.get(fastest_lap_url)
    data = response.text
    df = pd.read_html(data, index_col=0)

    df = df[0]
    df.dropna(how='all', axis='columns')
    df = df.loc[:, ~df.columns.str.contains('^Unnamed')]
    return df.iloc[0].to_dict()


archive_links = []
race_history = []

response = requests.get(BASE_URL)
data = response.text
soup  = BeautifulSoup(data, 'html.parser')

# Yearly Archives

archive_hrefs = soup.find_all('a', {'data-name': 'year'})

for link in archive_hrefs:
    if f'{SOURCE}{link.get("href")}' not in archive_links: 
        archive_links.append(f'{SOURCE}{link.get("href")}')
        print('Yearly Archive: ',f'{SOURCE}{link.get("href")}')


# Races

for year in archive_links:

    response = requests.get(year)
    data = response.text
    soup  = BeautifulSoup(data, 'html.parser')
    archive_hrefs = soup.find_all('a', {'data-name': 'meetingKey'})

    for link in archive_hrefs:
        if f'{SOURCE}{link.get("href")}' not in race_history and 'race-result.html' in f'{SOURCE}{link.get("href")}' :
            race_history.append({'url': f'{SOURCE}{link.get("href")}', 'gp': link.get_text(' ', strip=True) })
            print('Race Result: ', f'{SOURCE}{link.get("href")}')




for race in race_history:

    response = requests.get(race['url'])
    
    data = response.text
    if 'No results are currently available' not in data:
        fastest_lap = get_fastest_lap(race['url'])
        soup  = BeautifulSoup(data, 'html.parser')

        result_tbl = soup.find('table', {'class': 'resultsarchive-table'}).get_text(' ', strip=True)

        race_date = soup.find('span', {'class': 'full-date'}).get_text().replace(' ', '-')
        gp = race['gp'].upper()

        result_table = pd.read_html(data, index_col=0)
        result_table[0].dropna(how='all', axis='columns')
        result_table[0] = result_table[0].loc[:, ~result_table[0].columns.str.contains('^Unnamed')]
        result_table[0] = result_table[0].rename(columns={'Pos': 'position', 'No': 'number', 'Driver': 'driver', 'Car': 'car', 'Laps': 'laps', 'Time/Retired': 'time', 'PTS': 'points'})
        
        data_dict = result_table[0].to_dict('records')

        
        for dx in data_dict:
            dx['year'] = race_date.split('-')[-1]
            dx['grand_prix'] = gp
            dx['fastest_lap'] = 'no'
            try:
                if dx['driver'] == fastest_lap['Driver']:
                    dx['points'] = int(SCORING_SYSTEM[int(dx['position'])]) + 1
                    dx['fastest_lap'] = 'yes'
                    
                else:
                    dx['points'] = int(SCORING_SYSTEM[int(dx['position'])])
                    dx['fastest_lap'] = 'no'

            except: pass

            with open('formula1_data_races.csv', 'a', encoding='utf-8') as csv_file:
                csv_writer = csv.DictWriter(csv_file, fieldnames=csv_fields, delimiter=',', lineterminator='\n')
                csv_writer.writerow(dx)

