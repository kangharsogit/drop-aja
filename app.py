from flask import Flask, request, send_from_directory, redirect, abort, url_for, make_response
import os, secrets, string, time, json, threading, requests

app = Flask(__name__)
DATA_DIR = '/data'
os.makedirs(DATA_DIR, exist_ok=True)
PUBLIC_URL = os.environ.get('PUBLIC_URL', '').rstrip('/')
MAX_BYTES = 5 * 1024 * 1024  # 5 MB

# Cloudflare Turnstile (anti-bot)
TURNSTILE_SITE_KEY = os.environ.get('TURNSTILE_SITE_KEY', '')
TURNSTILE_SECRET_KEY = os.environ.get('TURNSTILE_SECRET_KEY', '')
TURNSTILE_VERIFY_URL = 'https://challenges.cloudflare.com/turnstile/v0/siteverify'


def verify_turnstile(token, remote_ip=None):
    """Verifikasi token Turnstile ke Cloudflare. True kalau valid atau Turnstile non-aktif."""
    if not TURNSTILE_SECRET_KEY:
        return True  # Turnstile tidak dikonfigurasi -> skip (backward compatible)
    if not token:
        return False
    try:
        data = {'secret': TURNSTILE_SECRET_KEY, 'response': token}
        if remote_ip:
            data['remoteip'] = remote_ip
        r = requests.post(TURNSTILE_VERIFY_URL, data=data, timeout=5)
        return r.json().get('success', False)
    except Exception:
        return False


INDEX = '''<!DOCTYPE html>
<html lang="id"><head><meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>Suntuk? Drop Aja — Instant HTML Hosting</title>
<meta name="robots" content="noindex,nofollow">
<meta name="description" content="Paste HTML, dapat URL live. No signup, langsung jadi.">
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;800;900&family=JetBrains+Mono:wght@400;500&display=swap" rel="stylesheet">
{{TURNSTILE_SCRIPT}}
<style>
*{box-sizing:border-box;margin:0;padding:0}
:root{
  --bg:#0a0a0b;--bg-soft:#131316;--bg-card:#16161a;
  --border:#26262d;--border-soft:#1d1d22;
  --text:#f0f0f2;--text-dim:#8a8a93;--text-faint:#555560;
  --accent:#a78bfa;--accent-2:#22d3ee;--accent-3:#f472b6;
  --success:#34d399;
}
html,body{height:100%}
body{
  font-family:'Inter',-apple-system,BlinkMacSystemFont,'Segoe UI',sans-serif;
  background:var(--bg);color:var(--text);min-height:100vh;
  background-image:
    radial-gradient(at 20% 0%, rgba(167,139,250,.15) 0, transparent 50%),
    radial-gradient(at 85% 30%, rgba(34,211,238,.08) 0, transparent 55%),
    radial-gradient(at 50% 100%, rgba(244,114,182,.07) 0, transparent 50%);
  background-attachment:fixed;
  display:flex;flex-direction:column;align-items:center;
  padding:2.5rem 1.25rem 4rem;line-height:1.5;
}
.container{width:100%;max-width:920px}
header{text-align:center;margin-bottom:2.25rem}
.logo{
  display:inline-flex;align-items:center;gap:.5rem;
  font-size:.78rem;font-weight:600;letter-spacing:.12em;text-transform:uppercase;
  color:var(--text-dim);background:var(--bg-soft);
  padding:.4rem .9rem;border-radius:99px;border:1px solid var(--border-soft);
  margin-bottom:1.25rem;
}
.logo .dot{width:6px;height:6px;border-radius:50%;background:var(--success);
  box-shadow:0 0 8px var(--success);animation:pulse 2s infinite}
@keyframes pulse{0%,100%{opacity:1}50%{opacity:.4}}
h1{
  font-size:clamp(2.5rem,7vw,4.25rem);font-weight:900;letter-spacing:-.04em;
  line-height:1.05;margin-bottom:.85rem;
  background:linear-gradient(135deg,var(--accent) 0%,var(--accent-2) 50%,var(--accent-3) 100%);
  -webkit-background-clip:text;background-clip:text;color:transparent;
}
h1 .q{display:inline-block;transform:rotate(-4deg);transform-origin:center}
.tag{
  font-size:1.05rem;color:var(--text-dim);max-width:520px;margin:0 auto;
}
.tag b{color:var(--text);font-weight:600}
.card{
  background:var(--bg-card);border:1px solid var(--border);
  border-radius:16px;padding:1.25rem;
  box-shadow:0 1px 0 rgba(255,255,255,.03) inset, 0 24px 48px -24px rgba(0,0,0,.6);
}
.editor{
  position:relative;background:#0d0d10;border:1px solid var(--border-soft);
  border-radius:10px;overflow:hidden;
}
.editor-bar{
  display:flex;align-items:center;gap:.5rem;
  padding:.7rem .9rem;border-bottom:1px solid var(--border-soft);
  background:rgba(255,255,255,.015);
}
.editor-bar .dots{display:flex;gap:.35rem}
.editor-bar .dots span{width:11px;height:11px;border-radius:50%;background:#2a2a30}
.editor-bar .dots span:nth-child(1){background:#ff5f57}
.editor-bar .dots span:nth-child(2){background:#febc2e}
.editor-bar .dots span:nth-child(3){background:#28c840}
.editor-bar .file{
  font-family:'JetBrains Mono',monospace;font-size:.78rem;
  color:var(--text-faint);margin-left:.4rem;
}
textarea{
  width:100%;min-height:52vh;resize:vertical;
  background:transparent;color:#e6e6ea;border:0;
  padding:1.1rem 1.2rem;
  font-family:'JetBrains Mono',monospace;font-size:13px;line-height:1.65;
}
textarea:focus{outline:none}
textarea::placeholder{color:#3a3a44}
.toolbar{
  display:flex;justify-content:space-between;align-items:center;
  gap:1rem;flex-wrap:wrap;margin-top:1.1rem;
}
.toolbar-left{display:flex;align-items:center;gap:.65rem;flex-wrap:wrap}
label{color:var(--text-dim);font-size:.875rem;font-weight:500}
select{
  background:var(--bg-soft);color:var(--text);
  border:1px solid var(--border);border-radius:8px;
  padding:.55rem .85rem;font-size:.875rem;font-family:inherit;
  cursor:pointer;transition:border-color .15s;
}
select:hover{border-color:#3a3a44}
select:focus{outline:none;border-color:var(--accent)}
button[type=submit]{
  background:linear-gradient(135deg,var(--accent) 0%,var(--accent-3) 100%);
  color:#0a0a0b;font-weight:700;font-size:.9rem;font-family:inherit;
  border:0;padding:.7rem 1.5rem;border-radius:8px;cursor:pointer;
  display:inline-flex;align-items:center;gap:.4rem;
  transition:transform .12s,box-shadow .12s;
  box-shadow:0 8px 24px -8px rgba(167,139,250,.5);
}
button[type=submit]:hover{transform:translateY(-1px);
  box-shadow:0 12px 28px -8px rgba(167,139,250,.7)}
button[type=submit]:active{transform:translateY(0)}
.turnstile-wrap{
  margin-top:1rem;display:flex;justify-content:center;
}
.features{
  display:grid;grid-template-columns:repeat(auto-fit,minmax(180px,1fr));
  gap:.75rem;margin-top:2rem;
}
.feat{
  background:var(--bg-soft);border:1px solid var(--border-soft);
  border-radius:10px;padding:.85rem 1rem;
}
.feat .ico{font-size:1.1rem;margin-bottom:.3rem}
.feat .ttl{font-size:.85rem;font-weight:600;color:var(--text);margin-bottom:.15rem}
.feat .sub{font-size:.78rem;color:var(--text-faint);line-height:1.4}
.footer{
  margin-top:2.5rem;text-align:center;color:var(--text-faint);
  font-size:.8rem;line-height:1.7;
}
.footer code{
  background:var(--bg-soft);padding:.2rem .5rem;border-radius:5px;
  font-size:.74rem;font-family:'JetBrains Mono',monospace;
  color:var(--text-dim);border:1px solid var(--border-soft);
}
.footer a{color:var(--text-dim);text-decoration:none;border-bottom:1px dotted var(--text-faint)}
.footer a:hover{color:var(--text)}
@media (max-width:520px){
  body{padding:1.5rem .9rem 3rem}
  .toolbar{justify-content:stretch}
  button[type=submit]{flex:1;justify-content:center}
}
</style></head><body>
<div class="container">
<header>
<div class="logo"><span class="dot"></span> Drop · Live HTML Hosting</div>
<h1>Suntuk<span class="q">?</span><br>Drop Aja.</h1>
<p class="tag">Paste HTML, dapat URL <b>langsung dirender</b>.<br>No signup, no API key, no drama.</p>
</header>
<div class="card">
<form method="POST" action="/upload">
<div class="editor">
<div class="editor-bar">
<div class="dots"><span></span><span></span><span></span></div>
<span class="file">untitled.html</span>
</div>
<textarea name="html" placeholder="<!DOCTYPE html>&#10;<html>&#10;  <body>&#10;    <h1>Halo dunia</h1>&#10;  </body>&#10;</html>" required autofocus spellcheck="false"></textarea>
</div>
<div class="toolbar">
<div class="toolbar-left">
<label for="ttl">⏱ Masa berlaku</label>
<select name="ttl" id="ttl">
<option value="0">Selamanya</option>
<option value="3600">1 jam</option>
<option value="86400">1 hari</option>
<option value="604800" selected>1 minggu</option>
<option value="2592000">1 bulan</option>
</select>
</div>
<button type="submit">Drop &amp; dapat URL →</button>
</div>
{{TURNSTILE_WIDGET}}
</form>
</div>
<div class="features">
<div class="feat"><div class="ico">⚡</div><div class="ttl">Instant</div><div class="sub">URL siap pakai dalam &lt;1 detik</div></div>
<div class="feat"><div class="ico">🕶</div><div class="ttl">Anonymous</div><div class="sub">Tanpa akun, tanpa email</div></div>
<div class="feat"><div class="ico">🔌</div><div class="ttl">API ready</div><div class="sub">POST JSON, langsung jadi</div></div>
<div class="feat"><div class="ico">🗑</div><div class="ttl">Delete token</div><div class="sub">Kontrol penuh konten Anda</div></div>
</div>
<div class="footer">
Public service — anyone can post &amp; view.<br>
API: <code>POST /api/upload</code> · JSON: <code>{"html":"...","ttl":"86400"}</code>
</div>
</div></body></html>'''


DONE = '''<!DOCTYPE html>
<html lang="id"><head><meta charset="UTF-8"><title>✓ Live — Suntuk? Drop Aja</title>
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<meta name="robots" content="noindex,nofollow">
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&family=JetBrains+Mono:wght@500&display=swap" rel="stylesheet">
<style>
*{{box-sizing:border-box;margin:0;padding:0}}
body{{
  font-family:'Inter',-apple-system,sans-serif;
  background:#0a0a0b;color:#f0f0f2;min-height:100vh;
  background-image:radial-gradient(at 50% 30%,rgba(52,211,153,.12) 0,transparent 55%);
  display:flex;justify-content:center;align-items:center;padding:1.5rem;
}}
.box{{
  background:#16161a;border:1px solid #26262d;border-radius:18px;
  padding:2.5rem 2rem;max-width:560px;width:100%;text-align:center;
  box-shadow:0 1px 0 rgba(255,255,255,.03) inset, 0 32px 64px -24px rgba(0,0,0,.7);
}}
.check{{
  width:64px;height:64px;border-radius:50%;
  background:linear-gradient(135deg,#34d399 0%,#22d3ee 100%);
  display:inline-flex;align-items:center;justify-content:center;
  font-size:1.8rem;color:#0a0a0b;font-weight:900;margin-bottom:1rem;
  box-shadow:0 12px 32px -8px rgba(52,211,153,.5);
}}
h2{{font-size:1.6rem;font-weight:800;letter-spacing:-.02em;margin-bottom:.4rem}}
.sub{{color:#8a8a93;font-size:.95rem;margin-bottom:1.5rem}}
.url-row{{
  display:flex;gap:.5rem;background:#0d0d10;border:1px solid #1d1d22;
  border-radius:10px;padding:.45rem .45rem .45rem .85rem;
  align-items:center;margin-bottom:1rem;
}}
.url-row a{{
  flex:1;color:#a78bfa;text-decoration:none;font-size:.92rem;
  word-break:break-all;text-align:left;font-family:'JetBrains Mono',monospace;
}}
.url-row a:hover{{color:#c4b5fd}}
.btn{{
  background:linear-gradient(135deg,#a78bfa 0%,#f472b6 100%);
  color:#0a0a0b;border:0;padding:.55rem 1rem;border-radius:7px;
  cursor:pointer;font-weight:700;font-size:.85rem;font-family:inherit;
  white-space:nowrap;transition:transform .1s;
}}
.btn:hover{{transform:translateY(-1px)}}
.actions{{display:flex;gap:.5rem;justify-content:center;flex-wrap:wrap}}
.btn-ghost{{
  background:#1a1a1f;color:#f0f0f2;border:1px solid #26262d;
  padding:.6rem 1.1rem;border-radius:8px;text-decoration:none;
  font-size:.875rem;font-weight:500;font-family:inherit;
  display:inline-flex;align-items:center;gap:.35rem;transition:border-color .15s;
}}
.btn-ghost:hover{{border-color:#3a3a44}}
.token-box{{
  margin-top:1.75rem;padding:1rem;background:#0d0d10;
  border:1px dashed #2a2a30;border-radius:10px;
}}
.token-label{{
  font-size:.72rem;text-transform:uppercase;letter-spacing:.1em;
  color:#8a8a93;font-weight:600;margin-bottom:.45rem;
}}
.token{{
  font-family:'JetBrains Mono',monospace;font-size:.78rem;
  color:#f472b6;word-break:break-all;line-height:1.5;
}}
.token-hint{{font-size:.74rem;color:#555560;margin-top:.55rem;line-height:1.5}}
</style></head><body>
<div class="box">
<div class="check">✓</div>
<h2>Drop berhasil</h2>
<p class="sub">URL Anda live dan siap dibagikan.</p>
<div class="url-row">
<a href="{url}" target="_blank" rel="noopener" id="u">{url}</a>
<button class="btn" onclick="navigator.clipboard.writeText('{url}');this.textContent='Copied ✓';setTimeout(()=>this.textContent='Copy',1500)">Copy</button>
</div>
<div class="actions">
<a href="{url}" target="_blank" class="btn-ghost">↗ Buka URL</a>
<a href="/" class="btn-ghost">+ Drop lagi</a>
</div>
<div class="token-box">
<div class="token-label">🗝 Delete token</div>
<div class="token">{token}</div>
<p class="token-hint">Simpan token ini kalau ingin hapus paste nanti via:<br><code style="font-size:.7rem;color:#8a8a93">{public}/delete/{slug}/{token}</code></p>
</div>
</div></body></html>'''


ERROR = '''<!DOCTYPE html>
<html lang="id"><head><meta charset="UTF-8"><title>✗ Error — Suntuk? Drop Aja</title>
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<meta name="robots" content="noindex,nofollow">
<link rel="preconnect" href="https://fonts.googleapis.com">
<link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&display=swap" rel="stylesheet">
<style>
*{{box-sizing:border-box;margin:0;padding:0}}
body{{font-family:'Inter',-apple-system,sans-serif;background:#0a0a0b;color:#f0f0f2;
min-height:100vh;display:flex;justify-content:center;align-items:center;padding:1.5rem;
background-image:radial-gradient(at 50% 30%,rgba(244,114,182,.12) 0,transparent 55%)}}
.box{{background:#16161a;border:1px solid #26262d;border-radius:18px;
padding:2.5rem 2rem;max-width:480px;width:100%;text-align:center}}
.x{{width:64px;height:64px;border-radius:50%;
background:linear-gradient(135deg,#f472b6 0%,#ef4444 100%);
display:inline-flex;align-items:center;justify-content:center;
font-size:1.8rem;color:#0a0a0b;font-weight:900;margin-bottom:1rem}}
h2{{font-size:1.4rem;font-weight:800;margin-bottom:.5rem}}
p{{color:#8a8a93;font-size:.95rem;margin-bottom:1.5rem;line-height:1.6}}
a{{background:#1a1a1f;color:#f0f0f2;border:1px solid #26262d;
padding:.6rem 1.2rem;border-radius:8px;text-decoration:none;font-weight:500;font-size:.9rem}}
a:hover{{border-color:#3a3a44}}
</style></head><body>
<div class="box"><div class="x">✗</div><h2>{title}</h2><p>{message}</p><a href="/">← Kembali</a></div>
</body></html>'''


def render_index():
    """Render halaman index dengan/tanpa Turnstile sesuai konfigurasi."""
    if TURNSTILE_SITE_KEY:
        script = '<script src="https://challenges.cloudflare.com/turnstile/v0/api.js" async defer></script>'
        widget = (f'<div class="turnstile-wrap">'
                  f'<div class="cf-turnstile" data-sitekey="{TURNSTILE_SITE_KEY}" '
                  f'data-theme="dark" data-size="flexible"></div>'
                  f'</div>')
    else:
        script = ''
        widget = ''
    return INDEX.replace('{{TURNSTILE_SCRIPT}}', script).replace('{{TURNSTILE_WIDGET}}', widget)


def render_error(title, message, status=400):
    return ERROR.format(title=title, message=message), status


def gen_slug(n=7):
    return ''.join(secrets.choice(string.ascii_letters + string.digits) for _ in range(n))


def safe_slug(s):
    return s and len(s) <= 32 and all(c.isalnum() or c in '-_' for c in s)


def save_paste(html, ttl):
    if not html.strip():
        return None, 'HTML kosong'
    if len(html.encode('utf-8')) > MAX_BYTES:
        return None, 'Terlalu besar (max 5MB)'
    for _ in range(10):
        slug = gen_slug()
        path = os.path.join(DATA_DIR, slug + '.html')
        if not os.path.exists(path):
            break
    else:
        return None, 'slug collision'
    token = secrets.token_urlsafe(16)
    meta = {'token': token, 'created': int(time.time())}
    try:
        ttl_int = int(ttl) if ttl else 0
        if ttl_int > 0:
            meta['expires'] = int(time.time()) + ttl_int
    except (ValueError, TypeError):
        pass
    with open(path, 'w', encoding='utf-8') as f:
        f.write(html)
    with open(path + '.json', 'w') as f:
        json.dump(meta, f)
    return (slug, token), None


def client_ip():
    """Ambil IP asli client (Cloudflare-aware)."""
    return request.headers.get('CF-Connecting-IP') or request.remote_addr


@app.route('/', methods=['GET'])
def index():
    return render_index()


@app.route('/upload', methods=['POST'])
def upload():
    # Verifikasi Turnstile (kalau diaktifkan)
    if TURNSTILE_SECRET_KEY:
        token = request.form.get('cf-turnstile-response', '')
        if not verify_turnstile(token, client_ip()):
            return render_error(
                'Verifikasi gagal',
                'Anti-bot check tidak lolos. Refresh halaman dan coba lagi.',
                403
            )

    result, err = save_paste(request.form.get('html', ''), request.form.get('ttl', '0'))
    if err:
        return render_error('Upload gagal', err, 400)
    slug, dtoken = result
    url = f'{PUBLIC_URL}/p/{slug}' if PUBLIC_URL else url_for('view', slug=slug, _external=True)
    return DONE.format(url=url, token=dtoken, slug=slug, public=PUBLIC_URL or '')


@app.route('/api/upload', methods=['POST'])
def api_upload():
    # API endpoint TIDAK memakai Turnstile (untuk automation/script)
    if request.is_json:
        d = request.get_json(silent=True) or {}
        html, ttl = d.get('html', ''), d.get('ttl', '0')
    else:
        html, ttl = request.form.get('html', ''), request.form.get('ttl', '0')
    result, err = save_paste(html, ttl)
    if err:
        return {'error': err}, 400
    slug, dtoken = result
    url = f'{PUBLIC_URL}/p/{slug}' if PUBLIC_URL else url_for('view', slug=slug, _external=True)
    return {'url': url, 'slug': slug, 'delete_token': dtoken}


@app.route('/p/<slug>')
def view(slug):
    if not safe_slug(slug):
        abort(404)
    path = os.path.join(DATA_DIR, slug + '.html')
    meta_path = path + '.json'
    if not os.path.exists(path):
        abort(404)
    if os.path.exists(meta_path):
        try:
            with open(meta_path) as f:
                meta = json.load(f)
            if 'expires' in meta and time.time() > meta['expires']:
                os.remove(path); os.remove(meta_path)
                abort(410)
        except Exception:
            pass
    resp = make_response(send_from_directory(DATA_DIR, slug + '.html'))
    resp.headers['X-Robots-Tag'] = 'noindex, nofollow'
    resp.headers['Content-Security-Policy'] = "frame-ancestors 'self'"
    return resp


@app.route('/delete/<slug>/<token>', methods=['GET', 'POST'])
def delete(slug, token):
    if not safe_slug(slug):
        abort(404)
    path = os.path.join(DATA_DIR, slug + '.html')
    meta_path = path + '.json'
    if not os.path.exists(meta_path):
        abort(404)
    with open(meta_path) as f:
        meta = json.load(f)
    if not secrets.compare_digest(meta.get('token', ''), token):
        abort(403)
    try:
        os.remove(path); os.remove(meta_path)
    except OSError:
        pass
    return 'Deleted', 200


@app.route('/healthz')
def healthz():
    return 'ok'


def gc_loop():
    """Background garbage collector — hapus paste expired tiap 1 jam."""
    while True:
        time.sleep(3600)
        now = time.time()
        try:
            for f in os.listdir(DATA_DIR):
                if f.endswith('.json'):
                    mp = os.path.join(DATA_DIR, f)
                    try:
                        with open(mp) as fh:
                            m = json.load(fh)
                        if 'expires' in m and now > m['expires']:
                            hp = mp[:-5]
                            if os.path.exists(hp):
                                os.remove(hp)
                            os.remove(mp)
                    except Exception:
                        pass
        except Exception:
            pass


threading.Thread(target=gc_loop, daemon=True).start()

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8080)
