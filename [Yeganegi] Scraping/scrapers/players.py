import os
import re
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


def parse_player_profile(html, url):
    soup = BeautifulSoup(html, 'html.parser')
    h1 = soup.find('h1')
    name = h1.get_text(strip=True) if h1 else ''

    meta = soup.find('div', id='meta') or (h1.find_parent('div') if h1 else soup)
    paragraphs = meta.find_all('p') if meta else []

    positions = []
    height = ''
    weight = ''
    born_date = ''
    relatives = []
    experience = ''

    for p in paragraphs:
        text = p.get_text(' ', strip=True)

        if 'Position:' in text:
            raw = text.split('Position:')[1].split('▪')[0]
            for pos in raw.replace(' and ', ', ').split(','):
                clean = pos.strip()
                if clean and clean.lower() != 'and':
                    positions.append(clean)

        if re.search(r'\d+-\d+', text) and any(u in text for u in ['lb', 'kg', 'cm']):
            cm_m = re.search(r'(\d+)\s*cm', text)
            if cm_m:
                height = cm_m.group(1)
            else:
                ft_in = re.search(r'(\d+)-(\d+)', text)
                if ft_in:
                    height = str(round((int(ft_in.group(1)) * 12 + int(ft_in.group(2))) * 2.54))

            lb_m = re.search(r'(\d+)\s*lb', text)
            if lb_m:
                weight = lb_m.group(1)

        if 'Born:' in text:
            birth_span = p.find(attrs={'data-birth': True})
            if birth_span:
                born_date = birth_span.get('data-birth')
            else:
                raw_b = text.split('Born:')[1].split('in')[0]
                born_date = re.sub(r'\s+', ' ', raw_b).strip()

        if 'Relatives:' in text:
            for a in p.find_all('a'):
                href = a.get('href', '')
                if '/players/' in href:
                    relatives.append(urllib.parse.urljoin(BASE_URL, href))

        if 'Experience:' in text:
            experience = text.split('Experience:')[1].split('▪')[0].strip()

    return {
        'player_name': name,
        'positions': '; '.join(positions),
        'height': height,
        'weight': weight,
        'born_date': born_date,
        'relatives_profile_links': '; '.join(relatives),
        'experience': experience,
        'player_url': url,
    }


def scrape_players():
    totals_csv = 'outputs/nba_totals.csv' if os.path.exists('outputs/nba_totals.csv') else 'nba_totals.csv'
    if not os.path.exists(totals_csv):
        print(f"error: totals file not found at {totals_csv}.")
        return

    df_totals = pd.read_csv(totals_csv)
    unique_players = df_totals[['player_name', 'player_url']].dropna().drop_duplicates(subset=['player_url']).reset_index(drop=True)

    players_csv = 'outputs/nba_players.csv'
    if os.path.exists(players_csv):
        existing = set(pd.read_csv(players_csv)['player_url'].dropna())
    else:
        existing = set()

    to_scrape = unique_players[~unique_players['player_url'].isin(existing)].reset_index(drop=True)

    for idx, row in to_scrape.iterrows():
        p_name = row['player_name']
        p_url = row['player_url']

        try:
            res = requests.get(p_url, headers=headers)
            if res.status_code == 200:
                data = parse_player_profile(res.text, p_url)
                temp = pd.DataFrame([data])
                temp.to_csv(
                    players_csv,
                    mode='a' if os.path.exists(players_csv) else 'w',
                    header=not os.path.exists(players_csv),
                    index=False,
                    encoding='utf-8'
                )
        except Exception as e:
            print(f"  error: {e}")

        time.sleep(3)

    if os.path.exists(players_csv):
        df_players = pd.read_csv(players_csv)
        return df_players


if __name__ == '__main__':
    scrape_players()
