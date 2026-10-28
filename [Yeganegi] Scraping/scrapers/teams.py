import os
import re
import time
import pandas as pd
import requests
from bs4 import BeautifulSoup

os.makedirs('outputs', exist_ok=True)

headers = {
    'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36',
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
    'Accept-Language': 'en-US,en;q=0.9',
}


def parse_team_info(html, url=""):
    soup = BeautifulSoup(html, 'html.parser')
    h1 = soup.find('h1')

    team_name = ''
    if h1:
        spans = h1.find_all('span')
        for s in spans:
            t = s.get_text(strip=True)
            if not re.search(r'^\d{4}-\d{2}$', t):
                team_name = t
                break
        if not team_name:
            t = h1.get_text(strip=True)
            team_name = re.sub(r'^\d{4}-\d{2}\s*', '', t).split('Roster')[0].strip()

    meta = soup.find('div', id='meta') or (h1.find_parent('div') if h1 else soup)
    paragraphs = meta.find_all('p') if meta else []

    coach = ''
    coach_details = ''
    arena = ''
    attendance = ''
    record = ''
    executive = ''

    for p in paragraphs:
        text = p.get_text(' ', strip=True)

        if 'Coach:' in text or 'Coaches:' in text:
            links = p.find_all('a')
            if links:
                coach = ', '.join([a.get_text(strip=True) for a in links])
            else:
                coach = re.split(r'Coach(?:es)?:\s*', text, maxsplit=1)[-1].strip()
            coach_details = re.split(r'Coach(?:es)?:\s*', text, maxsplit=1)[-1].strip()

        if 'Arena:' in text:
            part = text.split('Arena:')[1]
            if 'Attendance:' in part:
                arena = part.split('Attendance:')[0].strip()
                attendance = part.split('Attendance:')[1].strip()
            else:
                arena = part.strip()
        elif 'Attendance:' in text and not attendance:
            attendance = text.split('Attendance:')[1].strip()

        if 'Record:' in text and not record:
            record = text.split('Record:')[1].strip()

        if 'Executive:' in text and not executive:
            executive = text.split('Executive:')[1].strip()

    return {
        'team_name': team_name,
        'coach': coach,
        'coach_details': coach_details,
        'arena': arena,
        'record': record,
        'executive': executive,
        'attendance': attendance,
        'team_url': url,
    }


def scrape_teams():
    totals_csv = 'outputs/nba_totals.csv' if os.path.exists('outputs/nba_totals.csv') else 'nba_totals.csv'
    if not os.path.exists(totals_csv):
        print(f"error: totals file not found at {totals_csv}.")
        return

    df_totals = pd.read_csv(totals_csv)
    unique_teams = df_totals[['season', 'team_abbr', 'team_url']].dropna().drop_duplicates(subset=['team_url']).reset_index(drop=True)

    teams_csv = 'outputs/nba_teams.csv'
    if os.path.exists(teams_csv):
        existing_teams = set(pd.read_csv(teams_csv)['team_url'].dropna())
    else:
        existing_teams = set()

    teams_to_scrape = unique_teams[~unique_teams['team_url'].isin(existing_teams)].reset_index(drop=True)

    for idx, row in teams_to_scrape.iterrows():
        s = row['season']
        abbr = row['team_abbr']
        t_url = row['team_url']

        try:
            res = requests.get(t_url, headers=headers)
            if res.status_code == 200:
                data = parse_team_info(res.text, t_url)
                data['season'] = s
                data['team_abbr'] = abbr
                temp = pd.DataFrame([data])
                temp.to_csv(
                    teams_csv,
                    mode='a' if os.path.exists(teams_csv) else 'w',
                    header=not os.path.exists(teams_csv),
                    index=False,
                    encoding='utf-8'
                )
        except Exception as e:
            print(f"  error: {e}")

        time.sleep(3)

    if os.path.exists(teams_csv):
        df_teams = pd.read_csv(teams_csv)
        return df_teams


if __name__ == '__main__':
    scrape_teams()
