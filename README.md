# stockimgtrend 🍌📊

Sistem AI Multi-Agent & Dashboard TUI interaktif bergaya `btop` untuk riset tren visual stock image (Adobe Stock) memanfaatkan **Google Trends**, **Tavily Search API (Cloud Proxy)**, dan **OpenRouter AI**.

Dilengkapi dengan generator **1 Master Prompt & Tema Kuat** yang dioptimalkan khusus untuk engine **Nanobanana**, serta ekspor otomatis ke Markdown dan SQLite.

---

## ⚡ Cara Menjalankan Super Cepat

Cukup jalankan script launcher:

```bash
./start.sh
```

### Navigasi Shortcut Keyboard di Dashboard:
- **`[a]`**: **Auto Discovery** (AI mengecek SQLite, merumuskan 3 niche baru 2026, dan menganalisis live).
- **`[k]`**: **Ketik Keyword** (Popup minimalis untuk memasukkan kata kunci kustom).
- **`[g]`**: **Gen Nanobanana** (Meracik Master Prompt, Negative Prompt, dan 50 Tags dari riset aktif).
- **`[h]`**: **Riwayat (DB)** (Popup viewer tabel database SQLite).
- **`[c]`**: **Clear Log** (Bersihkan activity log).
- **`[q]`**: **Keluar**.

---

## 🛠️ Parameter Tambahan (Opsional)

Script `start.sh` mendukung seluruh argumen CLI:

```bash
# Riset keyword tertentu langsung
./start.sh -k "bionic athlete outdoors"

# Langsung jalankan Autonomous Discovery
./start.sh --auto

# Cek tabel riwayat SQLite secara instan di terminal
./start.sh -H
```

---

## 🔒 Keamanan IP (Zero Local Scraping)

Seluruh riset pasar dan pelacakan hasil Adobe Stock dilakukan **100% melalui Tavily Search API di cloud**. Komputer Anda tidak melakukan scraping langsung ke `stock.adobe.com`, sehingga IP Anda aman dari rate limit, CAPTCHA, atau IP ban.

Dokumentasi lengkap arsitektur multi-agent dapat dibaca di [AGENTS.md](AGENTS.md).
