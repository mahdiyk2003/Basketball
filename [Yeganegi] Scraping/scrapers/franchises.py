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


def scrape_franchises():
    url = f"{BASE_URL}/teams/"
    res = requests.get(url, headers=headers)
    soup = BeautifulSoup(res.text, 'html.parser')

    table = soup.find('table', id='teams_active')
    tbody = table.find('tbody') if table else None
    rows = tbody.find_all('tr') if tbody else []

    franchises = []
    for r in rows:
        th = r.find('th', {'data-stat': 'franch_name'})
        if not th:
            continue

        f_name = th.get_text(strip=True)
        a = th.find('a')
        f_url = urllib.parse.urljoin(BASE_URL, a['href']) if a else ''

        def get_val(stat):
            c = r.find('td', {'data-stat': stat})
            return c.get_text(strip=True) if c else ''

        year_min = get_val('year_min')
        founded_year = year_min.split('-')[0] if year_min else ''

        franchises.append({
            'franchise_name': f_name,
            'founded_year': founded_year,
            'inaugural_season': year_min,
            'seasons_active': get_val('years'),
            'total_games': get_val('g'),
            'wins': get_val('wins'),
            'losses': get_val('losses'),
            'win_loss_pct': get_val('win_loss_pct'),
            'playoff_appearances': get_val('years_playoffs'),
            'championships': get_val('years_league_champion'),
            'franchise_url': f_url,
        })

    df_franchises = pd.DataFrame(franchises)
    df_franchises.to_csv('outputs/nba_franchises.csv', index=False, encoding='utf-8')

    teams_csv = 'outputs/nba_teams.csv' if os.path.exists('outputs/nba_teams.csv') else 'nba_teams.csv'
    if os.path.exists(teams_csv):
        df_teams = pd.read_csv(teams_csv)
        founded_map = dict(zip(df_franchises['franchise_name'], df_franchises['founded_year']))
        season_map = dict(zip(df_franchises['franchise_name'], df_franchises['inaugural_season']))

        if 'founded_year' not in df_teams.columns or df_teams['founded_year'].isna().any():
            df_teams['founded_year'] = df_teams['team_name'].map(founded_map)
            df_teams['inaugural_season'] = df_teams['team_name'].map(season_map)
            df_teams.to_csv(teams_csv, index=False, encoding='utf-8')

    return df_franchises


if __name__ == '__main__':
    scrape_franchises()
