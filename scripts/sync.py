"""Bring the archive up to date from the Slack Web API.

usage: SLACK_TOKEN=xoxb-... python scripts/sync.py

The token belongs to a Slack app installed in the workspace with scopes
channels:history, channels:read, files:read and users:read, and the app
must be a member of the channel.

Top-level messages are refetched over a trailing window, so edits and
deletions inside it are mirrored. Threads are refetched while their latest
reply is recent.
"""

import json
import os
import sys
import time
import urllib.error
import urllib.parse
import urllib.request

import store

WINDOW = 30 * 86400
THREAD_WINDOW = 90 * 86400
API = 'https://slack.com/api/'


def call(token, method, **params):
    url = API + method + '?' + urllib.parse.urlencode(params)
    while True:
        request = urllib.request.Request(
            url, headers={'Authorization': 'Bearer ' + token})
        try:
            with urllib.request.urlopen(request, timeout=60) as response:
                body = json.loads(response.read())
        except urllib.error.HTTPError as e:
            if e.code == 429:
                time.sleep(int(e.headers.get('Retry-After', '5')) + 1)
                continue
            raise
        if not body.get('ok'):
            raise RuntimeError('%s: %s' % (method, body.get('error')))
        return body


def paged(token, method, key, **params):
    cursor = None
    while True:
        if cursor:
            params['cursor'] = cursor
        body = call(token, method, limit=200, **params)
        yield from body.get(key, [])
        cursor = body.get('response_metadata', {}).get('next_cursor')
        if not cursor:
            return


def in_channel(m):
    """True for messages listed by conversations.history."""
    return (m.get('thread_ts', m['ts']) == m['ts'] or
            m.get('subtype') == 'thread_broadcast')


def main():
    token = os.environ.get('SLACK_TOKEN')
    if not token:
        sys.exit('SLACK_TOKEN is not set')
    channel = store.read_json(os.path.join(store.DATA, 'channel.json'))
    cid = channel['id']

    raw_users = list(paged(token, 'users.list', 'members'))
    users = store.load_users()
    for u in raw_users:
        users[u['id']] = store.sanitize_user(u)
    store.save_users(users)
    store.fetch_avatars(raw_users)

    messages = store.load_messages()
    now = time.time()
    latest = max((float(ts) for ts in messages), default=0.0)
    oldest = max(latest - WINDOW, 0.0)

    top = list(paged(token, 'conversations.history', 'messages',
                     channel=cid, oldest='%.6f' % oldest, inclusive='true'))
    for ts in [ts for ts, m in messages.items()
               if float(ts) >= oldest and in_channel(m)]:
        del messages[ts]
    raw = list(top)
    for m in top:
        messages[m['ts']] = store.sanitize_message(m)

    threads = {m['ts'] for m in top if m.get('reply_count')}
    threads |= {ts for ts, m in messages.items() if m.get('reply_count')
                and float(m.get('latest_reply', 0)) >= now - THREAD_WINDOW}
    for parent in sorted(threads):
        replies = [m for m in paged(token, 'conversations.replies',
                                    'messages', channel=cid, ts=parent)
                   if m['ts'] != parent]
        for ts in [ts for ts, m in messages.items()
                   if m.get('thread_ts') == parent and not in_channel(m)]:
            del messages[ts]
        for m in replies:
            if not in_channel(m):
                messages[m['ts']] = store.sanitize_message(m)
        raw.extend(replies)

    store.save_messages(messages)
    count, failed = store.fetch_files(
        raw, {'Authorization': 'Bearer ' + token})
    print('messages %d, threads %d, files +%d'
          % (len(top), len(threads), count))
    for f in failed:
        print('failed', f)


if __name__ == '__main__':
    main()
