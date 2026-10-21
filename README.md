# libbitcoin Slack archive

Public mirror of the libbitcoin Slack `#general` channel, served at
https://libbitcoin.info/slack/.

* `data/` sanitized messages (one file per month), users and channel.
* `files/` attachments and avatars.
* `scripts/import_export.py` merges a Slack workspace export ZIP.
* `scripts/sync.py` updates from the Slack Web API (daily, by workflow).
* `scripts/build.py` generates the static site into `_site/`.

## Setup

1. Create a Slack app from `slack-app.yml` (api.slack.com/apps, *Create New
   App*, *From a manifest*), install it to the workspace and copy its *Bot
   User OAuth Token* (`xoxb-...`).
2. In Slack, `/invite @archive` in `#general`.
3. Add the token to this repository as the Actions secret `SLACK_TOKEN`.
4. Set *Settings › Pages › Source* to *GitHub Actions*.

## Local

```
pip install -r requirements.txt
python scripts/import_export.py "<export>.zip"
SLACK_TOKEN=xoxb-... python scripts/sync.py
python scripts/build.py
python -m http.server -d _site
```
