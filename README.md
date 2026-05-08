# Drop Aja 🎯

> **Suntuk? Drop Aja.** — Self-hosted instant HTML hosting.

[![BtTwBRe.md.png](https://iili.io/BtTwBRe.md.png)](https://freeimage.host/i/BtTwBRe)

[![BtTwxxj.md.png](https://iili.io/BtTwxxj.md.png)](https://freeimage.host/i/BtTwxxj)

Paste HTML, dapat URL live yang langsung dirender. No signup, no API key, no drama.
Open-source alternative untuk [pagedrop.io](https://pagedrop.io), [tiiny.host](https://tiiny.host), dan teman-temannya.

![License](https://img.shields.io/badge/license-MIT-blue.svg)
![Python](https://img.shields.io/badge/python-3.12-yellow.svg)
![Docker](https://img.shields.io/badge/docker-ready-blue.svg)

## ✨ Fitur

- ⚡ **Instant** — paste HTML, dapat URL siap pakai dalam <1 detik
- 🕶 **Anonymous** — tanpa akun, tanpa email, tanpa tracking
- 🎨 **Auto-render** — file di-serve dengan `Content-Type: text/html`, browser langsung render
- 🔌 **API ready** — endpoint JSON untuk integrasi script/CI/CD
- 🗑 **Delete token** — kontrol penuh untuk hapus paste Anda
- ⏱ **TTL pilihan user** — selamanya, 1 jam, 1 hari, 1 minggu, 1 bulan
- 🤖 **Auto-cleanup** — garbage collector hapus paste expired tiap 1 jam
- 🔒 **Anti-indexing** — header `X-Robots-Tag: noindex`, tidak masuk Google
- 📦 **Single container** — Flask + Gunicorn, footprint kecil

## 🚀 Quick Start

### Pakai Docker Compose

```bash
git clone https://github.com/ariefadi/drop-aja.git
cd drop-aja
cp docker-compose.example.yml docker-compose.yml
cp .env.example .env

# Edit .env, set PUBLIC_URL ke domain Anda
nano .env

docker compose up -d --build
```

Buka `http://localhost:8080` (atau domain Anda) → done.

### Pakai dengan reverse proxy / Cloudflare Tunnel

App listen di port `8080`. Arahkan reverse proxy (Caddy / Nginx / Traefik / Cloudflare Tunnel) ke port itu. Pastikan set `PUBLIC_URL` ke domain final supaya URL hasil paste benar.

## 📡 API

### Upload

```bash
curl -X POST https://your-domain.com/api/upload \
  -H "Content-Type: application/json" \
  -d '{"html":"<h1>Hello</h1>","ttl":"86400"}'
```

Response:

```json
{
  "url": "https://your-domain.com/p/Ab3xK9q",
  "slug": "Ab3xK9q",
  "delete_token": "xxx"
}
```

### TTL values (detik)

| Value | Arti |
|---|---|
| `0` | Selamanya |
| `3600` | 1 jam |
| `86400` | 1 hari |
| `604800` | 1 minggu |
| `2592000` | 1 bulan |

### Delete

```bash
curl https://your-domain.com/delete/<slug>/<delete_token>
```

## 🛠 Konfigurasi

| Env var | Default | Keterangan |
|---|---|---|
| `PUBLIC_URL` | *(empty)* | Domain publik app, dipakai untuk generate URL hasil paste |
| `TZ` | `UTC` | Timezone container |

## 🗂 Struktur
drop-aja/

├── Dockerfile

├── docker-compose.example.yml

├── app.py              # Flask app, single file (~280 baris)

├── .env.example

├── .gitignore

├── LICENSE

└── README.md

## 🔐 Catatan Keamanan

Aplikasi ini di-design sebagai **public open service** — siapapun yang akses domain Anda bisa upload HTML. Risiko: phishing, spam, abuse.

Mitigasi yang sudah aktif:
- Header `X-Robots-Tag: noindex` (tidak masuk Google)
- CSP `frame-ancestors 'self'` (tidak bisa di-iframe)
- Limit ukuran 5 MB per paste
- Slug random 7 char (~3.5T kombinasi, anti-enumeration)

Mitigasi tambahan yang **disarankan** (tidak built-in, set di reverse proxy):
- Cloudflare Turnstile / hCaptcha di form upload
- Rate limiting (misal 10 upload/IP/menit)
- Cloudflare Access policy untuk private mode

## 🤝 Kontribusi

PR welcome. Issue lebih welcome lagi.

## 📜 Lisensi

[MIT](LICENSE)

---

Made with ☕ in Indonesia.
