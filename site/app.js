(function () {
  'use strict';

  function reveal() {
    var id = location.hash.slice(1);
    if (!id) return;
    var el = document.getElementById(id);
    if (!el) return;
    for (var p = el.parentElement; p; p = p.parentElement) {
      if (p.tagName === 'DETAILS') p.open = true;
    }
    el.scrollIntoView({ block: 'center' });
  }
  window.addEventListener('hashchange', reveal);
  reveal();

  var input = document.getElementById('q');
  if (!input) return;
  var out = document.getElementById('results');
  var data = null, loading = null, timer = 0;
  var LIMIT = 200;

  function load() {
    if (!loading) {
      loading = fetch('search.json').then(function (r) { return r.json(); })
        .then(function (d) {
          d.lower = d.rows.map(function (r) { return r[3].toLowerCase(); });
          data = d;
        });
    }
    return loading;
  }

  function esc(s) {
    return s.replace(/[&<>"]/g, function (c) {
      return { '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;' }[c];
    });
  }

  function snippet(text, terms) {
    var lower = text.toLowerCase(), at = lower.indexOf(terms[0]);
    var start = Math.max(0, at - 80), end = Math.min(text.length, start + 280);
    var s = (start ? '…' : '') + text.slice(start, end) +
      (end < text.length ? '…' : '');
    s = esc(s);
    terms.forEach(function (t) {
      var re = new RegExp(esc(t).replace(/[.*+?^${}()|[\]\\]/g, '\\$&'), 'gi');
      s = s.replace(re, function (m) { return '<mark>' + m + '</mark>'; });
    });
    return s;
  }

  function when(sec) {
    var d = new Date(sec * 1000);
    return d.toISOString().slice(0, 16).replace('T', ' ');
  }

  function run() {
    var q = input.value.trim();
    try {
      history.replaceState(null, '', q ? '?q=' + encodeURIComponent(q) +
        '#search' : location.pathname);
    } catch (_) {}
    if (q.length < 2) { out.innerHTML = ''; return; }
    load().then(function () {
      if (input.value.trim() !== q) return;
      var terms = q.toLowerCase().split(/\s+/).filter(Boolean);
      var hits = [], total = 0;
      for (var i = data.rows.length - 1; i >= 0; i--) {
        var l = data.lower[i], ok = true;
        for (var j = 0; j < terms.length && ok; j++) {
          ok = l.indexOf(terms[j]) !== -1 ||
            data.names[data.rows[i][1]].toLowerCase() === terms[j];
        }
        if (ok) { total++; if (hits.length < LIMIT) hits.push(data.rows[i]); }
      }
      var html = '<div class="rn">' + total.toLocaleString() + ' result' +
        (total === 1 ? '' : 's') + (total > LIMIT ? ', newest ' + LIMIT +
        ' shown' : '') + '</div>';
      html += hits.map(function (r) {
        return '<a class="res" href="' + r[2] + '"><div class="rh"><b>' +
          esc(data.names[r[1]]) + '</b>' + when(r[0]) + ' UTC</div>' +
          snippet(r[3], terms) + '</a>';
      }).join('');
      out.innerHTML = html;
    });
  }

  input.addEventListener('input', function () {
    clearTimeout(timer);
    timer = setTimeout(run, 150);
  });
  input.addEventListener('focus', load);
  var initial = new URLSearchParams(location.search).get('q');
  if (initial) { input.value = initial; run(); }
  if (location.hash === '#search') input.focus();
})();
