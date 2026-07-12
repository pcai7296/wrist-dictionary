"""Check commit dates on PR branch."""
import requests, sys

TOKEN = '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'
HEADERS = {'Authorization': f'Bearer {TOKEN}'}
URL = 'https://api.github.com/repos/pcai7296/AstroBox-Repo/commits'

params = {'sha': 'astrobooox-submit-1783843203906', 'per_page': 5}
r = requests.get(URL, headers=HEADERS, params=params)
for c in r.json():
    sha = c['sha'][:8]
    date = c['commit']['committer']['date'][:10]
    msg = c['commit']['message'].split('\n')[0]
    print(f'{sha}  {date}  {msg}')
