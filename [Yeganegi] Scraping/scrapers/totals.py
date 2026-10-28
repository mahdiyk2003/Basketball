import os
import time
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


def scrape_totals():
    seasons_csv = 'outputs/nba_seasons.csv' if os.path.exists('outputs/nba_seasons.csv') else 'nba_seasons.csv'
    if not os.path.exists(seasons_csv):
        print(f"error: seasons file not found at {seasons_csv}.")
        return

    df_seasons = pd.read_csv(seasons_csv)
    all_totals = []

    for idx, row in df_seasons.iterrows():
        season = row['season']
        totals_url = str(row['season_url']).replace('.html', '_totals.html')

        res = requests.get(totals_url, headers=headers)
        if res.status_code != 200:
            time.sleep(3)
            continue

        soup = BeautifulSoup(res.text, 'html.parser')
        table = soup.find('table', id='totals_stats')
        tbody = table.find('tbody') if table else None
        rows = tbody.find_all('tr') if tbody else []

        count = 0
        for r in rows:
            if 'thead' in (r.get('class') or []):
                continue

            p_cell = r.find(['th', 'td'], {'data-stat': 'name_display'}) or r.find(['th', 'td'], {'data-stat': 'player'})
            if not p_cell:
                continue

            p_name = p_cell.get_text(strip=True)
            p_link = p_cell.find('a')
            p_url = urllib.parse.urljoin(BASE_URL, p_link['href']) if p_link and 'href' in p_link.attrs else ''

            t_cell = r.find(['th', 'td'], {'data-stat': 'team_name_abbr'}) or r.find(['th', 'td'], {'data-stat': 'team_id'})
            t_name = t_cell.get_text(strip=True) if t_cell else ''
            t_link = t_cell.find('a') if t_cell else None
            t_url = urllib.parse.urljoin(BASE_URL, t_link['href']) if t_link and 'href' in t_link.attrs else ''

            rec = {
                'season': season,
                'player_name': p_name,
                'player_url': p_url,
                'team_abbr': t_name,
                'team_url': t_url,
            }

            for cell in r.find_all(['th', 'td']):
                stat = cell.get('data-stat')
                if stat and stat not in ['name_display', 'player', 'team_name_abbr', 'team_id', 'ranker']:
                    rec[stat] = cell.get_text(strip=True)

            all_totals.append(rec)
            count += 1

        time.sleep(3)

    df_totals = pd.DataFrame(all_totals)
    df_totals.to_csv('outputs/nba_totals.csv', index=False, encoding='utf-8')
    return df_totals


if __name__ == '__main__':
    scrape_totals()
