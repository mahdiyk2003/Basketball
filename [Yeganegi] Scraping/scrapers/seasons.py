import os
import urllib.parse
import pandas as pd
import requests
from bs4 import BeautifulSoup

os.makedirs('outputs', exist_ok=True)

BASE_URL = 'https://www.basketball-reference.com'
headers = {
    'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36',
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
    'Accept-Language': 'en-US,en;q=0.9',
}


def scrape_seasons():
    url = f"{BASE_URL}/leagues/"
    res = requests.get(url, headers=headers)
    if res.status_code != 200:
        print(f"status {res.status_code}, could not fetch {url}")
        return

    soup = BeautifulSoup(res.text, 'html.parser')

    table = soup.find('table', id='stats')
    tbody = table.find('tbody') if table else None
    rows = tbody.find_all('tr') if tbody else []

    seasons = []
    for row in rows:
        if 'thead' in (row.get('class') or []) or 'over_header' in (row.get('class') or []):
            continue

        th = row.find('th', {'data-stat': 'season'})
        if not th:
            continue

        season_name = th.get_text(strip=True)
        link = th.find('a')
        season_url = urllib.parse.urljoin(BASE_URL, link['href']) if link else ''

        if not ('2020-21' <= season_name <= '2026-27'):
            continue

        def get_val(stat):
            c = row.find('td', {'data-stat': stat})
            return c.get_text(strip=True) if c else ''

        seasons.append({
            'season': season_name,
            'league': get_val('lg_id'),
            'champion': get_val('champion'),
            'mvp': get_val('mvp'),
            'rookie_of_the_year': get_val('roy'),
            'points_leader': get_val('pts_leader_name_display'),
            'rebounds_leader': get_val('trb_leader_name_display'),
            'assists_leader': get_val('ast_leader_name_display'),
            'win_shares_leader': get_val('ws_leader_name_display'),
            'season_url': season_url,
        })

    df = pd.DataFrame(seasons)
    df.to_csv('outputs/nba_seasons.csv', index=False, encoding='utf-8')
    return df


if __name__ == '__main__':
    scrape_seasons()
