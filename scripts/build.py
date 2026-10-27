"""Generate the static archive site into _site/.

usage: python scripts/build.py
"""

import calendar
import html
import json
import os
import re
import shutil

from PIL import Image

import store

SITE = 'https://libbitcoin.info/slack/'
CANONICAL = 'libbitcoin.info'
OUT = os.path.join(store.ROOT, '_site')
CACHE = os.path.join(store.ROOT, '.cache')
THUMB_WIDTH = 960
SNIPPET_LINES = 40
SNIPPET_BYTES = 64 * 1024
GROUP_SECONDS = 300
CODE_TYPES = {'text', 'cpp', 'c', 'python', 'shell', 'diff', 'javascript',
              'objc', 'json', 'markdown', 'csv', 'xml', 'yaml', 'go',
              'rust', 'java', 'sql', 'html', 'css', 'make', 'cmake'}

SITE_MENU = [
    ('index.html', 'Home'),
    ('Getting Started', [
        ('download/index.html', 'Download BS'),
        ('start/index.html', 'Quick Start'),
        ('configuration/index.html', 'Configuration'),
        ('building/index.html', 'Building'),
    ]),
    ('Server', [
        ('interfaces.html', 'BS Interfaces'),
        ('interfaces/admin.html', 'Admin Console'),
        ('interfaces/native.html', 'Native REST'),
        ('interfaces/electrum.html', 'Electrum'),
        ('interfaces/sparrow.html', 'Sparrow'),
        ('interfaces/p2p.html', 'Bitcoin P2P'),
        ('interfaces/bitcoind-rpc.html', 'Bitcoind JSON-RPC'),
        ('interfaces/bitcoind-rest.html', 'Bitcoind REST'),
        ('interfaces/zeromq.html', 'Bitcoind ZMQ'),
        ('interfaces/btcd.html', 'BTCD'),
        ('interfaces/esplora.html', 'Esplora'),
        ('interfaces/stratum-v1.html', 'Stratum v1'),
        ('interfaces/stratum-v2.html', 'Stratum v2'),
    ]),
    ('Performance', [
        ('sync.html', 'Sync BS'),
        ('footprint.html', 'Footprint'),
        ('computation.html', 'Computation'),
        ('interface-performance.html', 'Interfaces'),
    ]),
    ('Architecture', [
        ('architecture/index.html', 'Node'),
        ('database/index.html', 'Database'),
    ]),
    ('Client', [
        ('client/commands.html', 'BX Commands'),
    ]),
    ('developers/index.html', 'Developers'),
    ('team.html', 'Team'),
]

esc = html.escape


class Archive:
    def __init__(self):
        self.users = store.load_users()
        self.channel = store.read_json(os.path.join(store.DATA,
                                                    'channel.json'))
        self.emoji = store.read_json(os.path.join(store.DATA, 'emoji.json'))
        self.messages = store.load_messages()
        self.top = []
        self.threads = {}
        for m in sorted(self.messages.values(), key=lambda m: float(m['ts'])):
            parent = m.get('thread_ts', m['ts'])
            if parent != m['ts']:
                self.threads.setdefault(parent, []).append(m)
            if parent == m['ts'] or m.get('subtype') == 'thread_broadcast':
                self.top.append(m)
        self.home = {}
        for m in self.top:
            month = store.month_of(m['ts'])
            self.home.setdefault(m['ts'], month)
            for r in self.threads.get(m['ts'], []):
                self.home.setdefault(r['ts'], month)

    # names

    def name(self, m_or_id, m=None):
        uid = m_or_id if isinstance(m_or_id, str) else m_or_id.get('user')
        m = m if m is not None else (m_or_id if isinstance(m_or_id, dict)
                                     else {})
        if m.get('bot_profile') or m.get('username'):
            return (m.get('bot_profile') or {}).get('name') or m['username']
        u = self.users.get(uid)
        if u:
            p = u.get('profile', {})
            return p.get('display_name') or p.get('real_name') or u['name']
        p = m.get('user_profile', {})
        return p.get('display_name') or p.get('real_name') or uid or '?'

    def avatar(self, uid, prefix):
        u = self.users.get(uid)
        if u:
            path = store.avatar_path(u)
            if os.path.exists(os.path.join(store.ROOT, path)):
                return '<img class="av" src="%s%s" alt="" loading="lazy">' % (
                    prefix, path)
        initial = self.name(uid)[:1].upper() or '?'
        hue = sum(map(ord, uid or '')) * 47 % 360
        return ('<span class="av" style="background:hsl(%d 35%% 32%%)">%s'
                '</span>' % (hue, esc(initial)))

    def emoji_char(self, name, code=None):
        code = code or self.emoji.get(name)
        if not code:
            return esc(':%s:' % name)
        return ''.join(chr(int(c, 16)) for c in code.split('-'))

    def link(self, ts):
        month = self.home.get(ts)
        if not month:
            return None
        return '%s/%s/#p%s' % (month[:4], month[5:], ts.replace('.', ''))

    # rich text

    def inline(self, e):
        t = e.get('type')
        if t == 'text':
            s = esc(e.get('text', ''))
            style = e.get('style') or {}
            if style.get('code'):
                s = '<code>%s</code>' % s
            if style.get('bold'):
                s = '<b>%s</b>' % s
            if style.get('italic'):
                s = '<i>%s</i>' % s
            if style.get('strike'):
                s = '<s>%s</s>' % s
            return s
        if t == 'link':
            text = e.get('text') or e.get('url', '')
            s = esc(text)
            if (e.get('style') or {}).get('code'):
                s = '<code>%s</code>' % s
            return '<a href="%s" rel="nofollow ugc">%s</a>' % (
                esc(e.get('url', ''), True), s)
        if t == 'user':
            return '<span class="at">@%s</span>' % esc(self.name(e['user_id']))
        if t == 'channel':
            return '<span class="at">#%s</span>' % esc(
                self.channel['name'] if e.get('channel_id') ==
                self.channel['id'] else 'channel')
        if t == 'usergroup':
            return '<span class="at">@group</span>'
        if t == 'broadcast':
            return '<span class="at">@%s</span>' % esc(e.get('range', ''))
        if t == 'emoji':
            return self.emoji_char(e.get('name', ''), e.get('unicode'))
        if t == 'date':
            return esc(e.get('fallback', ''))
        if t == 'color':
            return esc(e.get('value', ''))
        return esc(e.get('text', ''))

    def section(self, el):
        return ''.join(self.inline(e) for e in el.get('elements', []))

    def rich(self, el):
        t = el.get('type')
        if t == 'rich_text':
            return ''.join(self.rich(e) for e in el.get('elements', []))
        if t == 'rich_text_section':
            return '<div class="p">%s</div>' % self.section(el)
        if t == 'rich_text_preformatted':
            return '<pre>%s</pre>' % self.section(el)
        if t == 'rich_text_quote':
            return '<blockquote>%s</blockquote>' % self.section(el)
        if t == 'rich_text_list':
            tag = 'ol' if el.get('style') == 'ordered' else 'ul'
            items = ''.join('<li>%s</li>' % self.section(i)
                            for i in el.get('elements', []))
            return '<%s class="l%d">%s</%s>' % (tag, el.get('indent', 0),
                                                items, tag)
        return ''

    # mrkdwn fallback

    def mrkdwn(self, text):
        out, pos = [], 0
        for match in re.finditer(r'```(.*?)```', text, re.S):
            out.append(self.mrkdwn_inline(text[pos:match.start()]))
            out.append('<pre>%s</pre>' % esc(html.unescape(
                match.group(1).strip('\n'))))
            pos = match.end()
        out.append(self.mrkdwn_inline(text[pos:]))
        return '<div class="p">%s</div>' % ''.join(out)

    def token(self, body):
        target, _, label = body.partition('|')
        label = html.unescape(label)
        if target.startswith('@'):
            return '<span class="at">@%s</span>' % esc(
                label or self.name(target[1:]))
        if target.startswith('#'):
            return '<span class="at">#%s</span>' % esc(label or 'channel')
        if target.startswith('!'):
            return '<span class="at">@%s</span>' % esc(
                label or target[1:].split('^')[0])
        url = html.unescape(target)
        return '<a href="%s" rel="nofollow ugc">%s</a>' % (
            esc(url, True), esc(label or url))

    def mrkdwn_inline(self, text):
        out = []
        for part in re.split(r'(`[^`\n]+`|<[^<>\n]+>)', text):
            if len(part) > 1 and part[0] == '`' and part[-1] == '`':
                out.append('<code>%s</code>' % esc(html.unescape(part[1:-1])))
                continue
            if len(part) > 1 and part[0] == '<' and part[-1] == '>':
                out.append(self.token(part[1:-1]))
                continue
            part = esc(html.unescape(part), False)
            part = re.sub(r'(?<![\w*])\*([^*\n]+)\*(?![\w*])', r'<b>\1</b>',
                          part)
            part = re.sub(r'(?<![\w_])_([^_\n]+)_(?![\w_])', r'<i>\1</i>',
                          part)
            part = re.sub(r'(?<![\w~])~([^~\n]+)~(?![\w~])', r'<s>\1</s>',
                          part)
            part = re.sub(r':([a-z0-9_+\-]+(?:::skin-tone-\d)?):',
                          lambda m: self.emoji_char(m.group(1))
                          if m.group(1) in self.emoji else m.group(0), part)
            out.append(part)
        return ''.join(out)

    def body(self, m):
        blocks = [b for b in m.get('blocks', []) if b.get('type') ==
                  'rich_text']
        if blocks:
            return ''.join(self.rich(b) for b in blocks)
        if m.get('text'):
            return self.mrkdwn(m['text'])
        return ''

    def plain(self, m):
        text = m.get('text', '')
        text = re.sub(r'<@(\w+)(\|[^>]*)?>',
                      lambda g: '@' + self.name(g.group(1)), text)
        text = re.sub(r'<[^<>|]+\|([^<>]+)>', r'\1', text)
        text = re.sub(r'<([^<>]+)>', r'\1', text)
        return ' '.join(html.unescape(text).split())

    # attachments

    def thumb(self, f):
        src = os.path.join(store.ROOT, f['path'])
        width = f.get('original_w') or 0
        if f.get('filetype') == 'gif' or f.get('mimetype') == 'image/svg+xml':
            return f['path']
        if width <= THUMB_WIDTH and f.get('size', 0) < 400 * 1024:
            return f['path']
        target = os.path.join(CACHE, 't', f['id'] + '.webp')
        if not os.path.exists(target):
            os.makedirs(os.path.dirname(target), exist_ok=True)
            try:
                with Image.open(src) as image:
                    image.thumbnail((THUMB_WIDTH, THUMB_WIDTH * 4))
                    image.save(target, 'WEBP', quality=86, method=6)
            except Exception:
                return f['path']
        return 't/%s.webp' % f['id']

    def snippet(self, path):
        with open(os.path.join(store.ROOT, path), 'rb') as f:
            data = f.read(SNIPPET_BYTES)
        lines = data.decode('utf8', 'replace').splitlines()
        more = len(lines) > SNIPPET_LINES or len(data) == SNIPPET_BYTES
        return '\n'.join(lines[:SNIPPET_LINES]), more

    def file(self, f, prefix):
        if f.get('mode') == 'tombstone':
            return '<div class="file gone">File deleted</div>'
        if 'path' not in f:
            return ('<div class="file"><span class="ico">%s</span><span>'
                    '<span class="fn">%s</span><span class="meta">%s · too '
                    'large to mirror</span></span></div>' % (
                        esc((f.get('filetype') or 'file').upper()[:4]),
                        esc(f.get('title') or f.get('name') or f['id']),
                        esc(size(f.get('size', 0)))))
        if not os.path.exists(os.path.join(store.ROOT, f['path'])):
            return '<div class="file gone">%s (missing)</div>' % esc(
                f.get('name', ''))
        href = prefix + f['path']
        name = f.get('title') or f.get('name') or f['id']
        meta = '%s · %s' % (f.get('pretty_type') or f.get('filetype', ''),
                            size(f.get('size', 0)))
        mime = f.get('mimetype', '')
        if mime.startswith('image/'):
            dims = ''
            if f.get('original_w') and f.get('original_h'):
                dims = ' width="%d" height="%d"' % (f['original_w'],
                                                    f['original_h'])
            return ('<a class="img" href="%s"><img src="%s%s" alt="%s"%s '
                    'loading="lazy"></a>' % (href, prefix, self.thumb(f),
                                             esc(name, True), dims))
        if mime.startswith('video/') or f.get('filetype') in (
                'mp4', 'mov', 'webm', 'mkv'):
            return ('<div class="vid"><video controls preload="metadata" '
                    'src="%s"></video><a href="%s" download>%s</a> '
                    '<span class="meta">%s</span></div>' % (
                        href, href, esc(name), esc(meta)))
        if (f.get('mode') == 'snippet' or mime.startswith('text/') or
                f.get('filetype') in CODE_TYPES):
            text, more = self.snippet(f['path'])
            tail = ('<a href="%s">full file</a>' % href) if more else ''
            return ('<details class="snip" open><summary>%s <span class="meta">'
                    '%s</span></summary><pre>%s</pre>%s</details>' % (
                        esc(name), esc(meta), esc(text), tail))
        icon = 'PDF' if f.get('filetype') == 'pdf' else (
            f.get('filetype') or 'file').upper()[:4]
        return ('<a class="file" href="%s"><span class="ico">%s</span>'
                '<span><span class="fn">%s</span><span class="meta">%s</span>'
                '</span></a>' % (href, esc(icon), esc(name), esc(meta)))

    def unfurl(self, a):
        title = a.get('title') or ''
        link = a.get('title_link') or a.get('from_url') or a.get(
            'original_url')
        if not (title or a.get('text')):
            return ''
        head = esc(a.get('service_name') or a.get('author_name') or '')
        title_html = ('<a href="%s" rel="nofollow ugc">%s</a>' % (
            esc(link, True), esc(title)) if link and title else esc(title))
        text = a.get('text', '')
        if len(text) > 600:
            text = text[:600] + '…'
        return ('<div class="unf">%s%s%s</div>' % (
            '<div class="svc">%s</div>' % head if head else '',
            '<div class="t">%s</div>' % title_html if title else '',
            '<div class="x">%s</div>' % self.mrkdwn_inline(text)
            if text else ''))

    def reactions(self, m):
        if not m.get('reactions'):
            return ''
        chips = []
        for r in m['reactions']:
            who = ', '.join(self.name(u) for u in r.get('users', []))
            chips.append('<span class="rx" title="%s">%s <b>%d</b></span>' % (
                esc(who, True), self.emoji_char(r['name']), r['count']))
        return '<div class="rxs">%s</div>' % ''.join(chips)

    # messages

    def message(self, m, prefix, compact=False, anchor=True, broadcast=True):
        ts = m['ts']
        when = store.ts_date(ts)
        pid = 'p' + ts.replace('.', '')
        sub = m.get('subtype', '')
        attrs = ' id="%s"' % pid if anchor else ''
        stamp = '<a class="tm" href="%s%s" title="%s UTC">%s</a>' % (
            prefix, share_path(ts), when.strftime('%Y-%m-%d %H:%M:%S'),
            when.strftime('%H:%M'))

        if sub in ('channel_join', 'channel_leave', 'channel_topic',
                   'channel_purpose', 'pinned_item', 'tombstone',
                   'huddle_thread'):
            if sub == 'huddle_thread':
                room = m.get('room', {})
                who = room.get('participant_history', [])
                mins = max(0, (room.get('date_end', 0) -
                               room.get('date_start', 0)) // 60)
                text = 'Huddle with %s · %d min' % (
                    ', '.join(self.name(u) for u in who) or 'nobody',
                    mins)
            elif sub == 'tombstone':
                text = 'This message was deleted.'
            elif sub == 'channel_topic':
                text = '%s set the topic: %s' % (self.name(m),
                                                 self.plain(m).split(
                                                     'topic: ', 1)[-1])
            else:
                text = self.plain(m)
            return ('<div class="msg ev"%s><span class="evt">%s</span>%s</div>'
                    % (attrs, esc(text), stamp))

        parts = []
        if sub == 'thread_broadcast' and broadcast:
            parent = m.get('thread_ts')
            href = self.link(parent)
            parts.append('<div class="bc">replied to a thread%s</div>' % (
                ': <a href="%s%s">view</a>' % (prefix, href) if href else ''))
        body = self.body(m)
        if sub == 'me_message':
            body = '<i>%s</i>' % body
        parts.append('<div class="tx">%s%s</div>' % (
            body, ' <span class="ed">(edited)</span>' if m.get('edited')
            else ''))
        for f in m.get('files', []):
            parts.append(self.file(f, prefix))
        for a in m.get('attachments', []):
            parts.append(self.unfurl(a))
        parts.append(self.reactions(m))

        if compact:
            head = '<div class="gut">%s</div>' % stamp
        else:
            head = ('<div class="gut">%s</div><div class="hd"><span class="nm">'
                    '%s</span>%s</div>' % (self.avatar(m.get('user'), prefix),
                                           esc(self.name(m)), stamp))
        return '<div class="msg%s"%s>%s<div class="bd">%s</div></div>' % (
            ' c' if compact else '', attrs, head, ''.join(parts))

    def stream(self, items, prefix, threads=True):
        out, last = [], None
        for m in items:
            normal = m.get('subtype', '') in ('', 'me_message', 'bot_message',
                                               'file_share')
            compact = (normal and last is not None and
                       last.get('user') == m.get('user') and
                       float(m['ts']) - float(last['ts']) < GROUP_SECONDS and
                       store.ts_date(m['ts']).date() ==
                       store.ts_date(last['ts']).date())
            out.append(self.message(m, prefix, compact))
            replies = self.threads.get(m['ts']) if threads else None
            if replies and m.get('subtype') != 'thread_broadcast':
                people = []
                for r in replies:
                    n = self.name(r)
                    if n not in people:
                        people.append(n)
                inner = ''.join(self.message(r, prefix, broadcast=False)
                                for r in replies)
                out.append(
                    '<details class="th"><summary><b>%d %s</b> · %s · last '
                    '%s</summary>%s</details>' % (
                        len(replies), 'reply' if len(replies) == 1 else
                        'replies', esc(', '.join(people[:4]) +
                                       (' +%d' % (len(people) - 4)
                                        if len(people) > 4 else '')),
                        store.ts_date(replies[-1]['ts']).strftime('%b %d, %Y'),
                        inner))
                last = None
            else:
                last = m if normal else None
        return ''.join(out)


def size(n):
    for unit in ('B', 'KB', 'MB', 'GB'):
        if n < 1024 or unit == 'GB':
            return ('%d %s' if unit == 'B' else '%.1f %s') % (n, unit)
        n /= 1024.0


def guard(path):
    """Redirect squatter mirrors and framing to the canonical host."""
    return '''<script>
(function () {
  var C = '%s', h = location.hostname.toLowerCase();
  var local = location.protocol === 'file:' || h === 'localhost' ||
    h === '127.0.0.1';
  var ok = local || h === C || h === 'libbitcoin.github.io';
  var framed = false;
  try { framed = window.top !== window.self; } catch (_) { framed = true; }
  if (ok && !(framed && !local)) return;
  var url = 'https://' + C + '/slack/%s' + location.hash;
  try { window.top.location.replace(url); } catch (_) {}
  try { location.replace(url); } catch (_) {}
})();
</script>''' % (CANONICAL, path)


def share_path(ts):
    return 'p/%s/' % ts.replace('.', '')


def page(title, path, prefix, body, description, image=None, robots=''):
    """Image is (url, width, height) or None for the site card."""
    url, width, height = image or ('https://%s/card3.png' % CANONICAL,
                                   2400, 1260)
    title, description = esc(title, True), esc(description, True)
    meta = [('property', 'og:type', 'website'),
            ('property', 'og:site_name', 'libbitcoin'),
            ('property', 'og:url', SITE + path),
            ('property', 'og:title', title),
            ('property', 'og:description', description),
            ('property', 'og:image', esc(url, True)),
            ('property', 'og:image:width', width),
            ('property', 'og:image:height', height),
            ('name', 'twitter:card', 'summary_large_image'),
            ('name', 'twitter:title', title),
            ('name', 'twitter:description', description),
            ('name', 'twitter:image', esc(url, True))]
    if robots:
        meta.append(('name', 'robots', robots))
    tags = '\n'.join('<meta %s="%s" content="%s">' % m for m in meta)
    return '''<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>%s</title>
<meta name="description" content="%s">
<link rel="canonical" href="%s%s">
<link rel="icon" type="image/svg+xml" href="%sfavicon.svg">
<link rel="stylesheet" href="%sstyle.css">
%s
%s
</head>
<body>
%s
<script src="%sapp.js"></script>
</body>
</html>
''' % (title, description, SITE, path, prefix, prefix, tags, guard(path),
       body, prefix)


def mast(prefix, title, lede, extra=''):
    root = prefix + '../'
    items = ''
    for label, target in SITE_MENU:
        if isinstance(target, list):
            links = ''.join('<a href="%s%s">%s</a>' % (root, href, name)
                for href, name in target)
            items += ('<details class="drop" name="site"><summary>%s</summary>'
                '<div>%s</div></details>' % (label, links))
        else:
            here = ' class="here"' if label == 'team.html' else ''
            items += '<a href="%s%s"%s>%s</a>' % (root, label, here, target)
    return '''<header class="mast">
<a href="%s" aria-label="libbitcoin.info"><img class="logo" src="%slogo.svg" alt="libbitcoin"></a>
<div class="eyebrow">Bitcoin full node and query server</div>
<h1>%s</h1>
<nav class="menu site">%s</nav>
<p class="lede">%s</p>
%s
</header>''' % (root, prefix, esc(title), items, lede, extra)


def month_name(month):
    return '%s %s' % (calendar.month_name[int(month[5:])], month[:4])


def build_month(a, month, months):
    prefix = '../../'
    items = [m for m in a.top if store.month_of(m['ts']) == month]
    index = months.index(month)
    prev = months[index - 1] if index else None
    nxt = months[index + 1] if index + 1 < len(months) else None

    def nav_link(target, label):
        if not target:
            return '<span></span>'
        return '<a href="../../%s/%s/">%s</a>' % (target[:4], target[5:],
                                                  label)

    nav = '<nav class="pn">%s%s</nav>' % (
        nav_link(prev, '← ' + month_name(prev) if prev else ''),
        nav_link(nxt, month_name(nxt) + ' →' if nxt else ''))
    days = []
    by_day = {}
    for m in items:
        by_day.setdefault(store.ts_date(m['ts']).date(), []).append(m)
    for day in sorted(by_day):
        days.append('<section class="day"><h2>%s</h2>%s</section>' % (
            day.strftime('%A, %B ') + str(day.day) + day.strftime(', %Y'),
            a.stream(by_day[day], prefix)))
    body = '''<div class="wrap">
%s
<nav class="menu"><a href="../../">All months</a><a href="../../#search">Search</a></nav>
%s
%s
%s
</div>''' % (mast(prefix, month_name(month),
                  'Archive of the libbitcoin Slack <strong>#%s</strong> channel.'
                  % esc(a.channel['name'])), nav, ''.join(days), nav)
    path = '%s/%s/' % (month[:4], month[5:])
    html_text = page('#%s · %s · libbitcoin Slack' % (a.channel['name'],
                                                     month_name(month)),
                     path, prefix, body,
                     'libbitcoin Slack #%s archive, %s.' % (
                         a.channel['name'], month_name(month)))
    write(os.path.join(OUT, month[:4], month[5:], 'index.html'), html_text)


def build_index(a, months):
    counts = {}
    for m in a.messages.values():
        if m.get('subtype') in ('channel_join', 'channel_leave'):
            continue
        month = a.home.get(m['ts'])
        if month:
            counts[month] = counts.get(month, 0) + 1
    peak = max(counts.values())
    people = {m.get('user') for m in a.messages.values()
              if not m.get('subtype') or m.get('subtype') == 'thread_broadcast'}
    years = sorted({m[:4] for m in months}, reverse=True)
    rows = []
    for year in years:
        cells = []
        for i in range(1, 13):
            month = '%s-%02d' % (year, i)
            n = counts.get(month, 0)
            if month in months:
                cells.append('<td><a class="mo" style="--h:%.2f" href="%s/%02d/">'
                             '<span>%s</span><b>%d</b></a></td>' % (
                                 (n / peak) ** 0.5, year, i,
                                 calendar.month_abbr[i], n))
            else:
                cells.append('<td><span class="mo none"><span>%s</span></span>'
                             '</td>' % calendar.month_abbr[i])
        total = sum(counts.get('%s-%02d' % (year, i), 0) for i in range(1, 13))
        rows.append('<tr><th>%s<small>%d</small></th>%s</tr>' % (
            year, total, ''.join(cells)))
    first, last = months[0], months[-1]
    lede = ('Mirror of the libbitcoin Slack <strong>#%s</strong> channel.'
            % esc(a.channel['name']))
    stats = ('<p class="stats"><b>%s</b> messages · <b>%d</b> people · '
             '%s – %s</p>' % ('{:,}'.format(sum(counts.values())),
                              len(people), month_name(first),
                              month_name(last)))
    body = '''<div class="wrap">
%s
<section id="search" class="search">
<input id="q" type="search" placeholder="Search messages" autocomplete="off" aria-label="Search messages">
<div id="results"></div>
</section>
<section class="cal">
<h2>Browse by month</h2>
<div class="scroller"><table>%s</table></div>
</section>
<p class="foot">Mirrored daily from the libbitcoin Slack workspace. Times are UTC.</p>
</div>''' % (mast('', 'Slack', lede, stats), ''.join(rows))
    write(os.path.join(OUT, 'index.html'),
          page('#%s · libbitcoin Slack archive' % a.channel['name'], '', '',
               body, 'Searchable archive of the libbitcoin Slack #%s '
               'channel, %s to %s.' % (a.channel['name'], month_name(first),
                                       month_name(last))))


def preview_image(m):
    """The message's first image as a link preview, if usable."""
    for f in m.get('files', []):
        if ('path' in f and f.get('size', 0) <= 5 * 1024 * 1024 and
                f.get('mimetype') in ('image/png', 'image/jpeg', 'image/gif')
                and f.get('original_w') and f.get('original_h')):
            return SITE + f['path'], f['original_w'], f['original_h']
    return None


def build_share(a):
    prefix = '../../'
    for m in a.messages.values():
        month = a.home.get(m['ts'])
        if not month:
            continue
        when = store.ts_date(m['ts'])
        day = '%s %d, %d' % (calendar.month_abbr[when.month], when.day,
                             when.year)
        parent = m.get('thread_ts', m['ts'])
        if parent != m['ts'] and m.get('subtype') != 'thread_broadcast':
            root = a.messages.get(parent)
            content = (a.message(root, prefix, anchor=False) if root else '')
            content += '<div class="th">%s</div>' % a.message(m, prefix)
        else:
            content = a.stream([m], prefix).replace('<details class="th">',
                                                    '<details class="th" '
                                                    'open>', 1)
        context = '%s%s/%s/#p%s' % (prefix, month[:4], month[5:],
                                    m['ts'].replace('.', ''))
        lede = ('<a href="%s">View in context</a> in the libbitcoin Slack '
                '<strong>#%s</strong> mirror.' % (context,
                                                  esc(a.channel['name'])))
        body = '<div class="wrap">\n%s\n<div class="share">%s</div>\n</div>' % (
            mast(prefix, day, lede), content)
        text = a.plain(m) or ' '.join(f.get('title') or f.get('name') or ''
                                      for f in m.get('files', []))
        if len(text) > 280:
            text = text[:279].rstrip() + '…'
        name = a.name(m)
        path = share_path(m['ts'])
        write(os.path.join(OUT, path, 'index.html'),
              page('%s · #%s · %s' % (name, a.channel['name'], day), path,
                   prefix, body, text or 'libbitcoin Slack #%s' %
                   a.channel['name'], preview_image(m)))


def build_search(a):
    names, index = [], {}
    rows = []
    for m in sorted(a.messages.values(), key=lambda m: float(m['ts'])):
        if m.get('subtype') in ('channel_join', 'channel_leave', 'tombstone',
                                'huddle_thread'):
            continue
        link = a.link(m['ts'])
        text = a.plain(m)
        files = ' '.join(f.get('title') or f.get('name') or ''
                         for f in m.get('files', []))
        if not link or not (text or files):
            continue
        name = a.name(m)
        if name not in index:
            index[name] = len(names)
            names.append(name)
        rows.append([int(float(m['ts'])), index[name], link,
                     (text + ' ' + files).strip()])
    with open(os.path.join(OUT, 'search.json'), 'w', encoding='utf8') as f:
        json.dump({'names': names, 'rows': rows}, f, ensure_ascii=False,
                  separators=(',', ':'))


def write(path, text):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, 'w', encoding='utf8', newline='\n') as f:
        f.write(text)


def mirror(src, dst):
    """Hard-link a directory tree into the site, copying across volumes."""
    for root, _, names in os.walk(src):
        target = os.path.join(dst, os.path.relpath(root, src))
        os.makedirs(target, exist_ok=True)
        for name in names:
            a, b = os.path.join(root, name), os.path.join(target, name)
            if os.path.exists(b):
                continue
            try:
                os.link(a, b)
            except OSError:
                shutil.copy2(a, b)


def main():
    a = Archive()
    os.makedirs(OUT, exist_ok=True)
    for name in os.listdir(OUT):
        path = os.path.join(OUT, name)
        if os.path.isdir(path):
            shutil.rmtree(path)
        else:
            os.remove(path)
    months = sorted({store.month_of(m['ts']) for m in a.top})
    for month in months:
        build_month(a, month, months)
    build_index(a, months)
    build_share(a)
    build_search(a)
    for name in os.listdir(os.path.join(store.ROOT, 'site')):
        shutil.copy2(os.path.join(store.ROOT, 'site', name), OUT)
    mirror(store.FILES, os.path.join(OUT, 'files'))
    if os.path.isdir(os.path.join(CACHE, 't')):
        mirror(os.path.join(CACHE, 't'), os.path.join(OUT, 't'))
    open(os.path.join(OUT, '.nojekyll'), 'w').close()
    print('months %d, messages %d' % (len(months), len(a.messages)))


if __name__ == '__main__':
    main()
