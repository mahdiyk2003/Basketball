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


def parse_mvp_table(html, season=""):
    soup = BeautifulSoup(html, 'html.parser')
    table = soup.find('table', id='mvp')
    if not table:
        return []

    tbody = table.find('tbody')
    rows = tbody.find_all('tr') if tbody else table.find_all('tr')

    candidates = []
    rename_map = {
        'rank': 'rank',
        'player': 'player_name',
        'age': 'age',
        'team_id': 'team_abbr',
        'votes_first': 'first_place_votes',
        'points_won': 'points_won',
        'points_max': 'points_max',
        'award_share': 'award_share',
        'g': 'games',
        'mp_per_g': 'mp_per_g',
        'pts_per_g': 'pts_per_g',
        'trb_per_g': 'trb_per_g',
        'ast_per_g': 'ast_per_g',
        'stl_per_g': 'stl_per_g',
        'blk_per_g': 'blk_per_g',
        'fg_pct': 'fg_pct',
        'fg3_pct': 'fg3_pct',
        'ft_pct': 'ft_pct',
        'ws': 'ws',
        'ws_per_48': 'ws_per_48',
    }

    for r in rows:
        if 'thead' in (r.get('class') or []) or 'over_header' in (r.get('class') or []):
            continue

        row_data = {'season': season} if season else {}
        for cell in r.find_all(['th', 'td']):
            stat = cell.get('data-stat')
            if stat in rename_map:
                row_data[rename_map[stat]] = cell.get_text(strip=True)

            if stat == 'player':
                a = cell.find('a')
                if a and 'href' in a.attrs:
                    row_data['player_url'] = urllib.parse.urljoin(BASE_URL, a['href'])

        if 'player_name' in row_data and row_data['player_name']:
            candidates.append(row_data)

    return candidates


def scrape_mvp():
    seasons_csv = 'outputs/nba_seasons.csv' if os.path.exists('outputs/nba_seasons.csv') else 'nba_seasons.csv'
    if not os.path.exists(seasons_csv):
        print(f"error: seasons file not found at {seasons_csv}.")
        return

    df_seasons = pd.read_csv(seasons_csv)
    mvp_candidates = []

    for idx, row in df_seasons.iterrows():
        season = row['season']
        s_url = str(row['season_url'])

        year = s_url.split('NBA_')[-1].replace('.html', '') if 'NBA_' in s_url else season.split('-')[0][:2] + season.split('-')[1]
        awards_url = f"{BASE_URL}/awards/awards_{year}.html"

        res = requests.get(awards_url, headers=headers)
        if res.status_code != 200:
            time.sleep(3)
            continue

        candidates = parse_mvp_table(res.text, season=season)
        mvp_candidates.extend(candidates)
        time.sleep(3)

    df_mvp = pd.DataFrame(mvp_candidates)
    df_mvp.to_csv('outputs/nba_mvp_candidates.csv', index=False, encoding='utf-8')
    return df_mvp


if __name__ == '__main__':
    scrape_mvp()
