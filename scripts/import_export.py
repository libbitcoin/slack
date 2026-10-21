"""Merge a Slack workspace export (ZIP) into the archive.

usage: python scripts/import_export.py <export.zip> [channel]

The export is authoritative for its time span: stored messages inside that
span are replaced by the export's. Attachments are downloaded through the
export's tokenized links, so run this before the export is deleted in Slack.
"""

import json
import os
import sys
import zipfile

import store


def main(path, channel_name='general'):
    with zipfile.ZipFile(path) as z:
        channels = json.loads(z.read('channels.json'))
        channel = next(c for c in channels if c['name'] == channel_name)
        raw_users = json.loads(z.read('users.json'))
        prefix = channel_name + '/'
        raw = []
        for name in sorted(z.namelist()):
            if name.startswith(prefix) and name.endswith('.json'):
                raw.extend(json.loads(z.read(name)))

    store.write_json(os.path.join(store.DATA, 'channel.json'), {
        'id': channel['id'], 'name': channel['name'],
        'created': channel['created'],
        'topic': channel.get('topic', {}).get('value', ''),
        'purpose': channel.get('purpose', {}).get('value', '')})

    users = store.load_users()
    for u in raw_users:
        users[u['id']] = store.sanitize_user(u)
    store.save_users(users)
    avatars = store.fetch_avatars(raw_users)

    first = min(float(m['ts']) for m in raw)
    last = max(float(m['ts']) for m in raw)
    messages = {ts: m for ts, m in store.load_messages().items()
                if not first <= float(ts) <= last}
    for m in raw:
        messages[m['ts']] = store.sanitize_message(m)
    store.save_messages(messages)

    count, failed = store.fetch_files(raw)
    print('messages %d, users %d, avatars +%d, files +%d'
          % (len(raw), len(raw_users), avatars, count))
    for f in failed:
        print('failed', f)


if __name__ == '__main__':
    main(*sys.argv[1:])
