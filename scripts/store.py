"""Archive store: sanitized messages, users and attachments under the repo."""

import datetime
import json
import os
import re
import urllib.request

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA = os.path.join(ROOT, 'data')
MESSAGES = os.path.join(DATA, 'messages')
FILES = os.path.join(ROOT, 'files')
AVATARS = os.path.join(FILES, 'avatars')

MESSAGE_KEYS = {
    'type', 'subtype', 'ts', 'user', 'text', 'blocks', 'thread_ts',
    'reply_count', 'latest_reply', 'edited', 'reactions', 'files',
    'attachments', 'root', 'room', 'topic', 'purpose', 'bot_id',
    'username', 'hidden', 'parent_user_id', 'item_type', 'inviter'}
PROFILE_KEYS = {'real_name', 'display_name', 'name'}
FILE_KEYS = {
    'id', 'name', 'title', 'filetype', 'mimetype', 'pretty_type', 'size',
    'original_w', 'original_h', 'mode', 'created', 'user', 'duration_ms'}
ATTACHMENT_KEYS = {
    'fallback', 'title', 'title_link', 'text', 'pretext', 'from_url',
    'original_url', 'service_name', 'author_name', 'author_link',
    'author_subname', 'footer', 'image_url', 'image_width', 'image_height',
    'thumb_url', 'thumb_width', 'thumb_height', 'is_msg_unfurl', 'ts',
    'channel_name'}
USER_KEYS = {'id', 'name', 'deleted', 'is_bot', 'is_admin', 'is_owner'}
USER_PROFILE_KEYS = {'real_name', 'display_name', 'title', 'avatar_hash'}
ROOM_KEYS = {'date_start', 'date_end', 'created_by', 'participant_history'}

MAX_FILE = 95 * 1024 * 1024
SECRET = re.compile(r'xox[a-z]-|[?&](t|token)=')


def read_json(path, default=None):
    if not os.path.exists(path):
        return default
    with open(path, encoding='utf8') as f:
        return json.load(f)


def write_json(path, value):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, 'w', encoding='utf8', newline='\n') as f:
        json.dump(value, f, ensure_ascii=False, indent=1, sort_keys=True)
        f.write('\n')


def write_lines(path, items):
    """One JSON object per line keeps diffs readable."""
    os.makedirs(os.path.dirname(path), exist_ok=True)
    body = ',\n'.join(json.dumps(i, ensure_ascii=False, sort_keys=True)
                      for i in items)
    with open(path, 'w', encoding='utf8', newline='\n') as f:
        f.write('[\n' + body + '\n]\n')


def no_secrets(value):
    """Drop any string that carries a Slack token."""
    if isinstance(value, dict):
        return {k: no_secrets(v) for k, v in value.items()
                if not (isinstance(v, str) and SECRET.search(v))}
    if isinstance(value, list):
        return [no_secrets(v) for v in value
                if not (isinstance(v, str) and SECRET.search(v))]
    return value


def ts_date(ts):
    utc = datetime.timezone.utc
    return datetime.datetime.fromtimestamp(float(ts), utc).replace(
        tzinfo=None)


def month_of(ts):
    return ts_date(ts).strftime('%Y-%m')


def file_path(f):
    """Local path of an attachment, relative to the repo."""
    ext = os.path.splitext(f.get('name') or '')[1].lower()
    if not re.fullmatch(r'\.[a-z0-9]{1,8}', ext):
        ext = ''
    return 'files/' + f['id'] + ext


def mirrored(f):
    """True if the attachment is stored, false if metadata only."""
    return (f.get('mode') not in ('tombstone', 'hidden_by_limit', 'external')
            and f.get('size', 0) <= MAX_FILE)


def sanitize_file(f):
    out = {k: v for k, v in f.items() if k in FILE_KEYS}
    if mirrored(f):
        out['path'] = file_path(f)
    return out


def sanitize_message(m):
    out = {k: v for k, v in m.items() if k in MESSAGE_KEYS}
    if 'user_profile' in m:
        out['user_profile'] = {k: v for k, v in m['user_profile'].items()
                               if k in PROFILE_KEYS}
    if 'bot_profile' in m:
        out['bot_profile'] = {'name': m['bot_profile'].get('name')}
    if 'files' in m:
        out['files'] = [sanitize_file(f) for f in m['files']]
    if 'attachments' in m:
        out['attachments'] = [{k: v for k, v in a.items()
                               if k in ATTACHMENT_KEYS}
                              for a in m['attachments']]
    if 'root' in m:
        out['root'] = sanitize_message(m['root'])
    if 'room' in m:
        out['room'] = {k: v for k, v in m['room'].items() if k in ROOM_KEYS}
    if 'reactions' in m:
        out['reactions'] = [{'name': r['name'], 'count': r['count'],
                             'users': r.get('users', [])}
                            for r in m['reactions']]
    return no_secrets(out)


def sanitize_user(u):
    out = {k: v for k, v in u.items() if k in USER_KEYS}
    profile = u.get('profile', {})
    out['profile'] = {k: v for k, v in profile.items()
                      if k in USER_PROFILE_KEYS}
    return no_secrets(out)


def avatar_url(u):
    profile = u.get('profile', {})
    return profile.get('image_72') or profile.get('image_48')


def avatar_path(u):
    h = re.sub(r'[^0-9a-z]', '', u.get('profile', {}).get('avatar_hash', '')
               or 'none')
    return 'files/avatars/%s-%s.jpg' % (u['id'], h)


def load_messages():
    """All stored messages keyed by ts."""
    out = {}
    if os.path.isdir(MESSAGES):
        for name in sorted(os.listdir(MESSAGES)):
            if name.endswith('.json'):
                for m in read_json(os.path.join(MESSAGES, name)):
                    out[m['ts']] = m
    return out


def save_messages(messages):
    by_month = {}
    for m in messages.values():
        by_month.setdefault(month_of(m['ts']), []).append(m)
    os.makedirs(MESSAGES, exist_ok=True)
    for name in os.listdir(MESSAGES):
        if name.endswith('.json') and name[:-5] not in by_month:
            os.remove(os.path.join(MESSAGES, name))
    for month, items in by_month.items():
        items.sort(key=lambda m: float(m['ts']))
        write_lines(os.path.join(MESSAGES, month + '.json'), items)


def load_users():
    return {u['id']: u for u in read_json(os.path.join(DATA, 'users.json'),
                                          [])}


def save_users(users):
    write_lines(os.path.join(DATA, 'users.json'),
                sorted(users.values(), key=lambda u: u['id']))


def download(url, path, headers=None):
    """Fetch url to a repo-relative path unless already present."""
    target = os.path.join(ROOT, path)
    if os.path.exists(target) and os.path.getsize(target) > 0:
        return False
    request = urllib.request.Request(url, headers=headers or {})
    with urllib.request.urlopen(request, timeout=300) as response:
        kind = response.headers.get('Content-Type', '')
        body = response.read()
    if kind.startswith('text/html') and not path.endswith(('.htm', '.html')):
        raise IOError('login page returned for ' + path)
    os.makedirs(os.path.dirname(target), exist_ok=True)
    with open(target, 'wb') as f:
        f.write(body)
    return True


def fetch_files(raw_messages, headers=None):
    """Download every attachment of the raw (unsanitized) messages."""
    count, failed = 0, []
    for m in raw_messages:
        for f in m.get('files', []) + m.get('root', {}).get('files', []):
            url = f.get('url_private_download') or f.get('url_private')
            if not url or not mirrored(f):
                continue
            try:
                count += download(url, file_path(f), headers)
            except Exception as e:
                failed.append('%s: %s' % (f['id'], e))
    return count, failed


def fetch_avatars(raw_users):
    count = 0
    for u in raw_users:
        url = avatar_url(u)
        if url:
            try:
                count += download(url, avatar_path(u))
            except Exception:
                pass
    return count
