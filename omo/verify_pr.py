"""Verify PR #398 after squash."""
import requests

TOKEN = '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'
H = {'Authorization': f'Bearer {TOKEN}'}

# PR commits
r = requests.get(
    'https://api.github.com/repos/AstralSightStudios/AstroBox-Repo/pulls/398/commits',
    headers=H
)
commits = r.json()
print(f'PR #398 now has {len(commits)} commit(s):')
for c in commits:
    sha = c['sha'][:8]
    msg = c['commit']['message'].split('\n')[0]
    print(f'  [{sha}] {msg}')

# PR state
r2 = requests.get(
    'https://api.github.com/repos/AstralSightStudios/AstroBox-Repo/pulls/398',
    headers=H
)
pr = r2.json()
print(f'\nPR state: {pr.get("state")} - "{pr.get("title")}"')
