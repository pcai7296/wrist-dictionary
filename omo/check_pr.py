"""Check PR #398 commits."""
import requests

url = 'https://api.github.com/repos/AstralSightStudios/AstroBox-Repo/pulls/398'
r = requests.get(url)
pr = r.json()
print('Title:', pr.get('title'))
head = pr.get('head', {})
print('Branch:', head.get('ref'))
print('Fork repo:', head.get('repo', {}).get('full_name'))
print('Clone URL:', head.get('repo', {}).get('clone_url'))
print('Owner:', head.get('repo', {}).get('owner', {}).get('login'))

c = requests.get(pr.get('commits_url'))
commits = c.json()
print(f'\nCommits ({len(commits)}):')
for i, cm in enumerate(commits):
    msg = cm['commit']['message'].split('\n')[0]
    print(f'  {i+1}. [{cm["sha"][:8]}] {msg}')
