<div align="center">
    <img src="./media/logo_large.png" alt="Pandawa Logo" width="200" height="200"/>
    <h1>Pandawa</h1>
    <h3><em>Bangun software berkualitas tinggi lebih cepat.</em></h3>
</div>

<p align="center">
    <strong>Toolkit open source yang membuat Anda fokus pada skenario produk dan hasil yang bisa diprediksi, bukan vibe coding tiap bagian dari nol.</strong>
</p>

<p align="center">
    <a href="https://git.neuron.id/research/pandawa/-/pipelines"><img src="https://git.neuron.id/research/pandawa/badges/main/pipeline.svg" alt="Pipeline"/></a>
    <a href="https://git.neuron.id/research/pandawa/blob/main/LICENSE"><img src="https://img.shields.io/badge/license-MIT-blue" alt="License"/></a>
    <a href="https://git.neuron.id/research/pandawa"><img src="https://img.shields.io/badge/source-git.neuron.id-orange" alt="Source"/></a>
</p>

---

## Daftar Isi

- [🤔 Apa itu Spec-Driven Development?](#-apa-itu-spec-driven-development)
- [⚡ Memulai](#-memulai)
  - [Workflow Terpandu (`/pandawa.ultimate`)](#2-jalankan-workflow-terpandu-disarankan)
  - [Command Langkah-demi-Langkah](#3-alternatif-command-langkah-demi-langkah)
- [🤖 Agen AI yang Didukung](#-agen-ai-yang-didukung)
- [🔧 Referensi CLI Pandawa](#-referensi-cli-pandawa)
  - [Profil Domain](#profil-domain)
  - [`pandawa usage`](#pandawa-usage)
  - [`pandawa version`](#pandawa-version)
  - [`pandawa governance`](#pandawa-governance)
  - [`pandawa skill`](#pandawa-skill)
  - [`pandawa run`](#pandawa-run)
- [📚 Filosofi Inti](#-filosofi-inti)
- [🌟 Fase Pengembangan](#-fase-pengembangan)
- [🎯 Tujuan Eksperimental](#-tujuan-eksperimental)
- [🔧 Prasyarat](#-prasyarat)
- [📖 Pelajari Lebih Lanjut](#-pelajari-lebih-lanjut)
- [🔍 Pemecahan Masalah](#-pemecahan-masalah)
- [💬 Dukungan](#-dukungan)
- [📄 Lisensi](#-lisensi)

## 🤔 Apa itu Spec-Driven Development?

Spec-Driven Development **membalik urutan** yang biasa dipakai dalam pengembangan software. Selama puluhan tahun, kode adalah rajanya — spesifikasi hanyalah perancah yang dibangun lalu dibuang begitu "kerja nyata" menulis kode dimulai. Spec-Driven Development mengubah ini: **spesifikasi menjadi executable**, langsung menghasilkan implementasi yang jalan, bukan sekadar jadi panduan.

## ⚡ Memulai

### 1. Instal CLI Pandawa

Pilih metode instalasi yang Anda inginkan:

#### Opsi 1: Instalasi Persisten (Disarankan)

Instal sekali, pakai di mana saja:

```bash
uv tool install pandawa-cli --from git+https://git.neuron.id/research/pandawa.git
```

Lalu pakai tool-nya langsung:

```bash
# Buat project baru
pandawa init <NAMA_PROJECT>

# Atau inisialisasi di project yang sudah ada
pandawa init . --ai claude
# atau
pandawa init --here --ai claude

# Cek tool yang terinstal
pandawa check
```

Untuk upgrade Pandawa, lihat [Panduan Upgrade](./docs/upgrade.md) untuk instruksi lengkap. Upgrade cepat:

```bash
uv tool install pandawa-cli --force --from git+https://git.neuron.id/research/pandawa.git
```

#### Opsi 2: Pemakaian Sekali Pakai

Jalankan langsung tanpa instalasi:

```bash
uvx --from git+https://git.neuron.id/research/pandawa.git pandawa init <NAMA_PROJECT>
```

**Keuntungan instalasi persisten:**

- Tool tetap terinstal dan tersedia di PATH
- Tidak perlu membuat shell alias
- Manajemen tool lebih baik dengan `uv tool list`, `uv tool upgrade`, `uv tool uninstall`
- Konfigurasi shell lebih bersih

### 2. Jalankan workflow terpandu (disarankan)

Jalankan asisten AI Anda di direktori project. Command `/pandawa.*` akan tersedia di asisten tersebut.

Cara tercepat dari ide sampai implementasi adalah command **`/pandawa.ultimate`**. Command ini mengorkestrasi seluruh lifecycle — dari menetapkan prinsip project sampai mengeksekusi implementasi — dengan gate konfirmasi di antara tiap fase:

```bash
/pandawa.ultimate Buat aplikasi yang bisa membantu saya mengorganisir foto-foto ke dalam album terpisah
```

Command ini akan:

1. Cek (atau buat) constitution project Anda
2. Buat spesifikasi fitur dari deskripsi Anda
3. Opsional: klarifikasi requirement yang ambigu
4. Menghasilkan technical plan
5. Memecah plan menjadi task yang bisa dieksekusi
6. Opsional: menjalankan analisis konsistensi
7. Mengimplementasikan fitur

Anda tetap memegang kendali — setelah setiap fase, Anda bisa memilih **lanjut**, **skip** (untuk fase opsional), atau **stop**.

> [!TIP]
> Kalau Anda lebih suka menjalankan tiap fase secara manual, atau butuh kontrol lebih pada tiap langkah, Anda bisa memakai command individual di bawah ini.

### 3. (Alternatif) Command langkah-demi-langkah

Kalau Anda lebih suka menjalankan tiap fase satu per satu:

#### Tetapkan prinsip project

Gunakan command **`/pandawa.constitution`** untuk membuat prinsip pengaturan dan pedoman pengembangan project Anda yang akan memandu semua pengembangan berikutnya.

```bash
/pandawa.constitution Buat prinsip yang berfokus pada kualitas kode, standar testing, konsistensi user experience, dan requirement performa
```

#### Buat spec

Gunakan command **`/pandawa.specify`** untuk mendeskripsikan apa yang ingin Anda bangun. Fokus pada **apa** dan **mengapa**, bukan tech stack.

```bash
/pandawa.specify Buat aplikasi yang bisa membantu saya mengorganisir foto-foto ke dalam album terpisah. Album dikelompokkan berdasarkan tanggal dan bisa diorganisir ulang dengan drag-and-drop di halaman utama. Album tidak pernah bersarang di dalam album lain. Di dalam setiap album, foto di-preview dalam tampilan seperti tile.
```

#### Buat technical implementation plan

Gunakan command **`/pandawa.plan`** untuk menyediakan tech stack dan pilihan arsitektur Anda.

```bash
/pandawa.plan Aplikasi ini menggunakan Vite dengan jumlah library seminimal mungkin. Gunakan HTML, CSS, dan JavaScript murni sebisa mungkin. Gambar tidak diunggah ke mana pun dan metadata disimpan di database SQLite lokal.
```

#### Pecah menjadi task

Gunakan **`/pandawa.tasks`** untuk membuat daftar task yang actionable dari implementation plan Anda.

```bash
/pandawa.tasks
```

#### Eksekusi implementasi

Gunakan **`/pandawa.implement`** untuk mengeksekusi semua task dan membangun fitur Anda sesuai plan.

```bash
/pandawa.implement
```

Untuk instruksi langkah-demi-langkah yang lebih rinci, lihat [panduan lengkap](./spec-driven.md) kami.

## 🤖 Agen AI yang Didukung

| Agen                                                                                  | Dukungan | Catatan                                                                                                                                     |
| -------------------------------------------------------------------------------------- | ------- | ----------------------------------------------------------------------------------------------------------------------------------------- |
| [Qoder CLI](https://qoder.com/cli)                                                   | ✅      |                                                                                                                                           |
| [Amazon Q Developer CLI](https://aws.amazon.com/developer/learning/q-developer-cli/) | ⚠️      | Amazon Q Developer CLI [tidak mendukung](https://github.com/aws/amazon-q-developer-cli/issues/3064) argumen custom untuk slash command. |
| [Amp](https://ampcode.com/)                                                          | ✅      |                                                                                                                                           |
| [Auggie CLI](https://docs.augmentcode.com/cli/overview)                              | ✅      |                                                                                                                                           |
| [Claude Code](https://www.anthropic.com/claude-code)                                 | ✅      |                                                                                                                                           |
| [CodeBuddy CLI](https://www.codebuddy.ai/cli)                                        | ✅      |                                                                                                                                           |
| [Codex CLI](https://github.com/openai/codex)                                         | ✅      |                                                                                                                                           |
| [Cursor](https://cursor.sh/)                                                         | ✅      |                                                                                                                                           |
| [Gemini CLI](https://github.com/google-gemini/gemini-cli)                            | ✅      |                                                                                                                                           |
| [GitHub Copilot](https://code.visualstudio.com/)                                     | ✅      |                                                                                                                                           |
| [IBM Bob](https://www.ibm.com/products/bob)                                          | ✅      | Agen berbasis IDE dengan dukungan slash command                                                                                          |
| [Kilo Code](https://github.com/Kilo-Org/kilocode)                                    | ✅      |                                                                                                                                           |
| [opencode](https://opencode.ai/)                                                     | ✅      |                                                                                                                                           |
| [Qwen Code](https://github.com/QwenLM/qwen-code)                                     | ✅      |                                                                                                                                           |
| [Roo Code](https://roocode.com/)                                                     | ✅      |                                                                                                                                           |
| [SHAI (OVHcloud)](https://github.com/ovh/shai)                                       | ✅      |                                                                                                                                           |
| [Windsurf](https://windsurf.com/)                                                    | ✅      |                                                                                                                                           |

## 🔧 Referensi CLI Pandawa

Command `pandawa` mendukung opsi-opsi berikut:

### Command

| Command      | Deskripsi                                                                                                                                             |
| ------------ | ------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `init`       | Inisialisasi project Pandawa baru dari template terbaru                                                                                                 |
| `profile`    | Kelola profil domain knowledge — daftar, cek update (`status`), tarik update (`update`), sematkan path lokal                                          |
| `check`      | Cek `git` plus setiap tool CLI/IDE [agen AI yang didukung](#-agen-ai-yang-didukung) yang terinstal di mesin Anda                                          |
| `version`    | Tampilkan versi CLI, info platform, dan release template terbaru                                                                                         |
| `usage`      | Tampilkan pemakaian token Claude Code dan estimasi biaya untuk project saat ini                                                                                 |
| `governance` | Kelola plugin governance (list, install, uninstall, activate, disable)                                                                                 |
| `skill`      | Kelola plugin skill (list, install, uninstall, enable, disable)                                                                                        |
| `run`        | Jalankan skill `/pandawa.*` lewat Claude Code dari terminal                                                                                                 |

Setiap command mencetak panel **Process Audit** kecil ketika selesai (durasi, dan untuk command berbasis AI, pemakaian token/estimasi biaya) dan menambahkan record JSON-lines ke `.pandawa/audit.log` di project (atau `~/.config/pandawa/audit.log` jika dijalankan di luar sebuah project). Ini hanyalah log lokal yang informatif untuk pencatatan Anda sendiri — tidak ada yang dikirim ke mana pun. `pandawa usage` membaca data sesi yang sama untuk merangkum biaya lintas sesi atau command.

### Profil Domain

Profil adalah **overlay domain knowledge** yang mengajarkan agen AI Anda standar, pattern, dan keputusan arsitektur dari domain tertentu — tanpa mengubah template dasar Anda.

> [!NOTE]
> Profil diterapkan lewat `pandawa init`, bukan lewat command `pandawa profile install` yang terpisah — `pandawa profile` punya `list`, `refresh`, `set-local`, `status`, dan `update` (lihat di bawah).

Terapkan sebuah profil saat Anda menginisialisasi project baru:

```bash
pandawa init my-project --ai claude --profile tmforum-oda
```

Atau saat menjalankan `pandawa init` secara interaktif (tanpa flag `--profile`), Anda akan diminta memilih dari menu arrow-key.

Untuk menambahkan profil ke project yang sudah diinisialisasi tanpa profil, jalankan ulang `init` di tempat:

```bash
pandawa init --here --force --ai claude --profile tmforum-oda
```

Folder profil diambil langsung dari git (`main`, tanpa perlu release CLI) dan diekstrak ke `.pandawa/profiles/<profile-id>/`. File instruksi agen AI Anda otomatis diperbarui untuk membaca constitution-nya dan mengikuti standarnya.

#### Profil yang Tersedia

| ID Profil | Nama | Deskripsi |
| --- | --- | --- |
| `tmforum-oda` | TM Forum ODA Constitution | Framework constitution TM Forum Open Digital Architecture yang reusable: API governance, DDD, CQRS, pattern event-driven untuk sistem BSS/OSS |
| `tmforum-oda-door-v3` | TM Forum ODA Design DOOR v3 | Semua yang ada di `tmforum-oda`, plus design system DOOR v3 — NestJS, CQRS, React MFE, Module Federation |
| `pegadaian` | Pegadaian Support Service Constitution | Constitution NestJS backend + Vue 3 Module Federation frontend untuk layanan tim AI Pegadaian. **Status: Draft** — lihat Known Gaps di `constitution/00-index.md` milik profil ini sebelum dianggap mengikat |

Jalankan `pandawa profile list` kapan saja untuk melihat kumpulan ID dan nama profil yang tersedia saat ini (tabel ini bisa berubah seiring bertambahnya profil baru — daftar dari CLI adalah sumber kebenarannya). Jalankan `pandawa profile refresh` untuk menyinkronkan katalog lokal dengan `main` — profil akan muncul di sini begitu ter-merge, tanpa perlu release CLI.

#### Menambahkan profil baru (self-service)

Profil berada di repo **`pandawa-marketplace-tooling`** (`https://git.neuron.id/research/pandawa-marketplace-tooling.git`), bersebelahan dengan plugin skill/agent, sebagai konsep top-level yang terpisah — satu repo, satu alur kontribusi, satu job validasi CI untuk keduanya. Menambahkan profil sepenuhnya self-service — tanpa perubahan kode CLI, tanpa release CLI, tanpa langkah packaging:

1. Di clone `pandawa-marketplace-tooling`, tambahkan folder di `profiles/<profil-anda>/` dengan manifest `profile.json` (`{"id", "name", "description"}`) plus `constitution/`, `architecture/`, `governance/`, `validation/`, `prompts/`, `SKILL.md`, dst milik Anda sendiri — termasuk stack frontend apa pun yang menjadi target profil Anda.
2. Tambahkan satu entri `{"id": "<id-anda>", "path": "profiles/<profil-anda>"}` ke `profiles.json` di root repo tersebut — ini satu-satunya file bersama yang Anda sentuh, dan memakai pola registrasi satu-baris yang sama seperti `.claude-plugin/marketplace.json`.
3. Jalankan `python tools/validate-marketplace.py .` di sana, lalu buka merge request (lihat `CONTRIBUTING.md`/`CODEOWNERS` repo tersebut). Begitu ter-merge ke `main`, `pandawa init --profile <id-anda>` langsung berfungsi untuk semua orang — `pandawa` mengambil folder profil Anda secara live lewat GitLab repository-archive API, tanpa langkah zip/release/CI di repo ini.

Sebelum merge, uji dulu secara lokal terhadap clone Anda dengan `pandawa init --profile <id-anda> --profile-path <path-ke-clone-anda>/profiles/<profil-anda>` (melewati pengecekan katalog sepenuhnya, karena sumbernya sudah eksplisit).

> [!TIP]
> Untuk panduan kolaborasi lengkap dari awal sampai akhir (keputusan plugin vs profil, anatomi lengkap folder domain-profile, CODEOWNERS, aturan breaking-change), lihat [`pandawa-marketplace-tooling/docs/PANDUAN-KOLABORASI.md`](https://git.neuron.id/research/pandawa-marketplace-tooling/blob/main/docs/PANDUAN-KOLABORASI.md), atau [dokumen Marketplace](docs/marketplace.md) milik repo ini sendiri.

#### Apa yang diinstal oleh sebuah profil

```text
.pandawa/
└── profiles/
    └── tmforum-oda/
        ├── SKILL.md                  ← Definisi sub-agent (Claude)
        ├── constitution/             ← 16 file hukum engineering (MUST/SHOULD/MUST NOT)
        ├── architecture/             ← Pattern ODA Canvas, tabel referensi
        ├── governance/               ← Aturan governance repository & PR
        ├── prompts/                  ← Prompt agen siap-pakai untuk generasi backend/frontend
        ├── templates/                ← Template scaffolding module
        ├── validation/               ← Rule book untuk API, backend, frontend
        └── recommendations/          ← Template gap analysis & migration roadmap
```

File instruksi agen AI Anda (`CLAUDE.md`, `GEMINI.md`, dst) diperbarui agar selalu memuat constitution profil di setiap sesi. Untuk Claude, sub-agent `.claude/agents/<profile-id>.md` juga diinstal untuk dipakai sesuai kebutuhan.

> [!NOTE]
> Folder `governance/` milik sebuah profil tidak berhubungan dengan command [`pandawa governance`](#pandawa-governance) di bawah — kata yang sama, konsep yang berbeda. `governance/` milik profil adalah dokumen referensi statis (aturan repo/PR) yang disalin agar bisa dibaca agen; ini tidak pernah terdaftar di governance guard dan tidak punya enforcement apa pun di baliknya. `pandawa governance` adalah sistem plugin Claude Code yang berbeda dan saling eksklusif, dilengkapi hook runtime nyata yang bisa memblokir pemakaian tool. Menginstal sebuah profil tidak menginstal atau mengaktifkan plugin governance apa pun.

### `pandawa profile` — daftar, cek update, & sematkan profil lokal

| Subcommand | Deskripsi |
| ---------- | ----------- |
| `list` | Daftar semua ID/nama/versi profil yang dikenal (dengan refresh best-effort terlebih dahulu), plus path lokal jika ada yang disematkan lewat `set-local` |
| `refresh` | Sinkronkan katalog profil lokal dari `profiles.json` milik `pandawa-marketplace-tooling` di `main`, tanpa bergantung pada release CLI apa pun |
| `status` | Di dalam sebuah project: bandingkan versi profil yang ter-install (`.pandawa/profile-lock.json`) dengan versi terbaru di katalog, tandai mana yang "update available" |
| `update <key>` | Di dalam sebuah project: ambil ulang isi profil `<key>` dari `main` (atau `--profile-path` lokal), timpa `.pandawa/profiles/<key>/`, dan perbarui lockfile |
| `set-local <key> <path>` | Sematkan direktori lokal sebagai sumber sebuah profil, sehingga `pandawa init --profile <key>` memakainya alih-alih mengunduh dari GitLab (berguna saat menulis/menguji sebuah profil) |

```bash
# Lihat profil yang tersedia (beserta versi terbaru masing-masing)
pandawa profile list

# Di dalam project yang sudah punya profil ter-install: cek apakah ada update
pandawa profile status

# Tarik update tersebut
pandawa profile update tmforum-oda

# Arahkan sebuah profil ke direktori lokal alih-alih mengunduhnya
pandawa profile set-local tmforum-oda-door-v3 ../pandawa-marketplace-tooling/profiles/tmforum-oda-door-v3
```

> [!NOTE]
> `version` di `profile.json` **bukan** mekanisme pin — `pandawa init --profile` dan
> `pandawa profile update` selalu mengambil `main` yang terkini. Versi ini murni untuk
> visibilitas: `pandawa` mencatat versi yang ter-install di `.pandawa/profile-lock.json`
> tiap project, dan `pandawa profile status` membandingkannya dengan katalog supaya
> update yang sudah di-merge ke `pandawa-marketplace-tooling` benar-benar **keliatan**,
> bukan cuma berubah diam-diam di `main`.

### Argumen & Opsi `pandawa init`

| Argumen/Opsi | Tipe | Deskripsi |
| --------------- | ---- | ----------- |
| `<project-name>` | Argumen | Nama untuk direktori project baru Anda (opsional jika memakai `--here`, atau pakai `.` untuk direktori saat ini) |
| `--ai` | Opsi | Asisten AI yang dipakai: `claude`, `gemini`, `copilot`, `cursor-agent`, `qwen`, `opencode`, `codex`, `windsurf`, `kilocode`, `auggie`, `roo`, `codebuddy`, `amp`, `shai`, `q`, `bob`, atau `qoder` |
| `--script` | Opsi | Varian script yang dipakai: `sh` (bash/zsh) atau `ps` (PowerShell) |
| `--ignore-agent-tools` | Flag | Skip pengecekan tool agen AI seperti Claude Code |
| `--no-git` | Flag | Skip inisialisasi repository git |
| `--here` | Flag | Inisialisasi project di direktori saat ini alih-alih membuat direktori baru |
| `--force` | Flag | Paksa merge/overwrite saat memakai `--here` (skip konfirmasi) — juga cara Anda menerapkan ulang `init` (mis. untuk menambahkan `--profile`) ke project yang sudah diinisialisasi |
| `--skip-tls` | Flag | Skip verifikasi SSL/TLS (tidak disarankan) |
| `--debug` | Flag | Tampilkan output diagnostik verbose untuk kegagalan network dan ekstraksi |
| `--gitlab-token` | Opsi | Token GitLab untuk request API (atau set variabel environment `GL_TOKEN`) — release template (repo ini) dan konten profil (`pandawa-marketplace-tooling`) sama-sama dihosting di GitLab, bukan GitHub |
| `--profile` | Opsi | Profil domain yang diterapkan (mis. `tmforum-oda`) — lihat [Profil Domain](#profil-domain) |
| `--profile-path` | Opsi | Pakai direktori lokal sebagai sumber profil alih-alih mengunduh (development/testing) |
| `--no-marketplace` | Flag | Skip pendaftaran marketplace plugin Pandawa di project (khusus Claude) |
| `--marketplace-url` | Opsi | Override URL git marketplace Pandawa (atau set `PANDAWA_MARKETPLACE_URL`) |
| `--no-guardrails` | Flag | Skip penulisan guardrail permission deny-first baseline ke `.claude/settings.json` (khusus Claude) |
| `--no-claude-md` | Flag | Skip scaffolding file starter `CLAUDE.md` untuk konteks project |

### Contoh

```bash
# Inisialisasi project dasar
pandawa init my-project

# Inisialisasi dengan asisten AI tertentu
pandawa init my-project --ai claude

# Inisialisasi dengan dukungan Cursor
pandawa init my-project --ai cursor-agent

# Inisialisasi dengan dukungan Qoder
pandawa init my-project --ai qoder

# Inisialisasi dengan dukungan Windsurf
pandawa init my-project --ai windsurf

# Inisialisasi dengan dukungan Amp
pandawa init my-project --ai amp

# Inisialisasi dengan dukungan SHAI
pandawa init my-project --ai shai

# Inisialisasi dengan dukungan IBM Bob
pandawa init my-project --ai bob

# Inisialisasi dengan script PowerShell (Windows/cross-platform)
pandawa init my-project --ai copilot --script ps

# Inisialisasi di direktori saat ini
pandawa init . --ai copilot
# atau pakai flag --here
pandawa init --here --ai copilot

# Paksa merge ke direktori saat ini (tidak kosong) tanpa konfirmasi
pandawa init . --force --ai copilot
# atau
pandawa init --here --force --ai copilot

# Skip inisialisasi git
pandawa init my-project --ai gemini --no-git

# Aktifkan output debug untuk troubleshooting
pandawa init my-project --ai claude --debug

# Pakai token GitLab untuk request API (berguna untuk environment korporat/instance privat)
pandawa init my-project --ai claude --gitlab-token glpat_your_token_here

# Cek requirement sistem
pandawa check

# Inisialisasi dengan profil domain TM Forum ODA
pandawa init my-project --ai claude --profile tmforum-oda

# Tambahkan profil ke project yang sudah ada di direktori saat ini
pandawa init --here --force --ai claude --profile tmforum-oda
```

![Specify CLI bootstrapping a new project in the terminal](./media/pandawa_cli.gif)

---

### `pandawa usage`

Tampilkan pemakaian token Claude Code dan estimasi biaya untuk project saat ini. Membaca riwayat sesi dari `~/.claude/projects/` dan mengagregasi token input/output/cache, jumlah turn, model, dan estimasi biaya per sesi.

```bash
# Tampilkan 10 sesi terakhir (default)
pandawa usage

# Tampilkan semua sesi
pandawa usage --limit 0

# Tampilkan breakdown per-command dengan biaya dan durasi
pandawa usage --commands

# Tampilkan metrik delivery gaya AI-DLC (predictability, cycle time, phase mix)
pandawa usage --delivery

# Tampilkan pemakaian untuk direktori project tertentu
pandawa usage --cwd /path/to/my-project
```

| Opsi | Deskripsi |
| ------ | ----------- |
| `--limit`, `-n` | Jumlah sesi terbaru yang ditampilkan (default: `10`, `0` = semua) |
| `--cwd` | Direktori project untuk membaca sesi (default: direktori saat ini) |
| `--commands`, `-c` | Tampilkan breakdown per-command `/pandawa.*` dengan biaya dan durasi |
| `--delivery`, `-d` | Tampilkan metrik delivery gaya AI-DLC: **predictability rate** (task selesai vs direncanakan di `tasks.md`, target >80%), **cycle time** end-to-end, dan **phase mix** per command. Metrik yang butuh baseline A/B (peningkatan velocity vs non-AI, defect rate ternormalisasi) sengaja tidak dikarang — dilaporkan apa adanya sebagai butuh pembanding |

---

### `pandawa version`

Tampilkan versi CLI, info platform, dan release template terbaru dari registry.

```bash
pandawa version
```

| Opsi | Deskripsi |
| ------ | ----------- |
| `--gitlab-token` | Token GitLab (atau set variabel environment `GL_TOKEN` / `GITLAB_TOKEN`) |

---

### `pandawa governance`

Kelola **plugin governance** — plugin yang menegakkan aturan dan constitution project secara menyeluruh. Hanya satu plugin governance yang boleh aktif dalam satu waktu.

> [!NOTE]
> Jangan disamakan dengan folder `governance/` milik sebuah profil (lihat [Apa yang diinstal oleh sebuah profil](#apa-yang-diinstal-oleh-sebuah-profil)) — itu konten referensi statis yang dibundel bersama profil domain, tanpa enforcement runtime. Command ini mengelola tipe plugin yang berbeda dan terpisah: plugin Claude Code yang bisa diinstal, dilengkapi hook guard `PreToolUse` yang secara aktif memblokir pemakaian tool jika invariant satu-aktif dilanggar.

```bash
# Daftar plugin governance yang terinstal lokal
pandawa governance list

# Daftar semua plugin governance yang tersedia (terinstal + marketplace)
pandawa governance list marketplace

# Sinkronkan katalog dari marketplace
pandawa governance refresh

# Unduh plugin governance ke local store
pandawa governance install tmf-oda-constitution

# Aktifkan plugin governance
pandawa governance use tmf-oda-constitution

# Tampilkan plugin governance mana yang sedang aktif
pandawa governance status

# Nonaktifkan plugin governance yang aktif
pandawa governance disable

# Hapus plugin governance dari local store
pandawa governance uninstall tmf-oda-constitution
```

| Subcommand | Deskripsi |
| ---------- | ----------- |
| `list [marketplace]` | Daftar plugin governance yang terinstal lokal; tambahkan `marketplace` untuk menyertakan semua yang tersedia |
| `refresh` | Sinkronkan katalog governance dari marketplace |
| `install <name>` | Unduh plugin governance ke local store (tidak mengaktifkannya) |
| `uninstall <name>` | Hapus plugin governance dari local store |
| `use <name>` | Aktifkan plugin governance (menonaktifkan yang sebelumnya aktif) |
| `status` | Tampilkan plugin governance yang sedang aktif |
| `disable [name]` | Nonaktifkan plugin governance yang aktif (atau yang disebutkan namanya) |

---

### `pandawa skill`

Kelola **plugin skill** — kemampuan on-demand yang memperluas apa yang bisa dilakukan agen AI Anda. Beberapa skill bisa aktif secara bersamaan.

```bash
# Daftar skill yang terinstal lokal
pandawa skill list

# Daftar semua skill yang tersedia (terinstal + marketplace)
pandawa skill list marketplace

# Unduh dan aktifkan sebuah skill
pandawa skill install neuron-plan

# Aktifkan skill yang sudah terinstal
pandawa skill enable neuron-plan

# Nonaktifkan sebuah skill (tetap terinstal)
pandawa skill disable neuron-plan

# Hapus sebuah skill dari local store
pandawa skill uninstall neuron-plan
```

| Subcommand | Deskripsi |
| ---------- | ----------- |
| `list [marketplace]` | Daftar skill yang terinstal lokal; tambahkan `marketplace` untuk menyertakan semua yang tersedia |
| `install <name>` | Unduh plugin skill dan langsung aktifkan |
| `uninstall <name>` | Hapus plugin skill dari local store |
| `enable <name>` | Aktifkan plugin skill yang sudah terinstal |
| `disable <name>` | Nonaktifkan plugin skill tanpa menghapus instalasinya |

---

### `pandawa run`

Jalankan skill `/pandawa.*` langsung lewat Claude Code dari terminal — berguna untuk scripting atau pipeline CI.

```bash
pandawa run constitution "Buat REST API untuk aplikasi todo"
pandawa run brd "fokus pada modul billing"
pandawa run specify "autentikasi user dengan OAuth2"
pandawa run plan
pandawa run clarify
pandawa run tasks
pandawa run implement
pandawa run analyze
pandawa run checklist
pandawa run test src/
pandawa run redesign "form create Projected Cost, ikuti file desain baru"
pandawa run deploy "siapkan pipeline staging"
pandawa run operate "wire observability untuk service billing"
pandawa run postmortem "insiden latency spike di endpoint orders"
```

| Subcommand | Deskripsi |
| ---------- | ----------- |
| `constitution [goal]` | Jalankan `/pandawa.constitution` — buat atau perbarui prinsip pengaturan project |
| `brd [scope]` | Jalankan `/pandawa.brd` — reverse-engineer BRD dari codebase yang sudah ada |
| `specify [goal]` | Jalankan `/pandawa.specify` — definisikan requirement dan user story |
| `plan [goal]` | Jalankan `/pandawa.plan` — buat technical implementation plan |
| `tasks [goal]` | Jalankan `/pandawa.tasks` — generate daftar task yang actionable |
| `implement [goal]` | Jalankan `/pandawa.implement` — eksekusi task untuk membangun fitur |
| `clarify [goal]` | Jalankan `/pandawa.clarify` — klarifikasi requirement yang underspecified |
| `analyze [goal]` | Jalankan `/pandawa.analyze` — analisis konsistensi & coverage lintas-artefak |
| `checklist [goal]` | Jalankan `/pandawa.checklist` — generate checklist kualitas |
| `test [path]` | Jalankan `/pandawa.test` — generate test, jalankan pengecekan kualitas kode, dan laporkan bug |
| `redesign [target]` | Jalankan `/pandawa.redesign` — rework satu bagian dari fitur yang sudah terimplementasi secara incremental |
| `deploy [scope]` | Jalankan `/pandawa.deploy` — siapkan otomasi deployment (containerization, pipeline CI/CD, config) |
| `operate [mode]` | Jalankan `/pandawa.operate` — wire observability, analisis telemetry/anomali, dan penyelesaian insiden |
| `postmortem [insiden]` | Jalankan `/pandawa.postmortem` — ubah insiden/pembelajaran produksi menjadi update spec & constitution |

---

### Command Slash yang Tersedia

Setelah menjalankan `pandawa init`, agen coding AI Anda akan punya akses ke slash command berikut untuk pengembangan yang terstruktur:

#### Command Workflow

Jalankan seluruh lifecycle SDD dalam satu sesi terpandu:

| Command | Deskripsi |
| --- | --- |
| `/pandawa.ultimate` | Orkestrator end-to-end — menjalankan constitution sampai implementasi dengan gate konfirmasi di antara tiap fase. Mendeteksi artefak yang sudah ada dan menawarkan untuk melanjutkan dari titik terakhir |

```bash
/pandawa.ultimate Buat aplikasi yang membantu saya mengorganisir foto ke dalam album terpisah
```

Command tunggal ini membawa Anda melalui semua fase build (constitution, specify, clarify, plan, tasks, analyze, implement), berhenti setelah masing-masing untuk konfirmasi Anda sebelum melanjutkan. Fase opsional (clarify, analyze) bisa di-skip di gate-nya. Command operations (`/pandawa.deploy`, `/pandawa.operate`, `/pandawa.postmortem`) tidak termasuk dalam orkestrasi ini — jalankan sendiri di sesi terpisah saat Anda siap rilis.

Jika Anda menjalankan `/pandawa.ultimate` lagi di project yang sudah punya beberapa artefak (mis. spec sudah ada tapi plan belum), ia akan memindai apa yang ada di disk lebih dulu dan menawarkan untuk **(A)** mulai fitur baru, **(B)** melanjutkan dari fase setelah artefak terakhir yang selesai, atau **(C)** restart penuh fitur saat ini. Berhenti di gate mana pun akan mencetak ringkasan abort dengan command manual yang tepat untuk dilanjutkan nanti — tidak ada yang hilang jika Anda berhenti di tengah jalan.

#### Command untuk Project yang Sudah Ada

Untuk project brownfield (`pandawa init --here` pada codebase yang sudah ada), jalankan ini dulu supaya sisa workflow punya konteks nyata alih-alih mulai dari spec kosong:

| Command | Deskripsi |
| --- | --- |
| `/pandawa.brd` | Reverse-engineer Business Requirements Document dari codebase yang sudah ada — menjadi konteks latar belakang untuk `/pandawa.specify` dan `/pandawa.constitution` di project tersebut |

```bash
/pandawa.brd
```

#### Command Inti

Command esensial untuk workflow Spec-Driven Development (juga bisa dijalankan satu per satu):

| Command               | Deskripsi                                                              |
| --------------------- | ------------------------------------------------------------------------ |
| `/pandawa.constitution` | Buat atau perbarui prinsip pengaturan project dan pedoman pengembangan |
| `/pandawa.specify`      | Definisikan apa yang ingin Anda bangun (requirement dan user story)            |
| `/pandawa.plan`         | Buat technical implementation plan dengan tech stack pilihan Anda        |
| `/pandawa.tasks`        | Generate daftar task yang actionable untuk implementasi             |
| `/pandawa.implement`    | Eksekusi semua task untuk membangun fitur sesuai plan             |

#### Command Opsional

Command tambahan untuk kualitas dan validasi yang lebih baik:

| Command            | Deskripsi                                                                                                                          |
| ------------------ | ------------------------------------------------------------------------------------------------------------------------------------ |
| `/pandawa.clarify`   | Klarifikasi area yang underspecified (disarankan sebelum `/pandawa.plan`; dulunya `/quizme`)                                                  |
| `/pandawa.analyze`   | Analisis konsistensi & coverage lintas-artefak (jalankan setelah `/pandawa.tasks`, sebelum `/pandawa.implement`)                                 |
| `/pandawa.checklist` | Generate checklist kualitas custom yang memvalidasi kelengkapan, kejelasan, dan konsistensi requirement (seperti "unit test untuk Bahasa Indonesia") |
| `/pandawa.test`      | Generate unit test yang belum ada, jalankan pengecekan kualitas kode gaya SonarQube (code smell, duplikasi, kompleksitas, keamanan), dan deteksi bug fungsional — membuktikan tiap bug dengan failing test dan melaporkan Bug Report bila ditemukan |
| `/pandawa.redesign`  | Rework satu bagian dari fitur yang sudah terimplementasi secara incremental (form, page, endpoint, atau table) — edit yang terlingkupi dengan checkpoint & rollback, alih-alih generate ulang dari nol |
| `/pandawa.taskstoissues` | Buat GitHub issue dari `tasks.md` lewat GitHub MCP server. Hanya jalan jika `git remote` project adalah URL GitHub — skip ini untuk project yang dihosting di GitLab |

#### Command Operations (pasca-implementasi)

Setelah fitur terimplementasi, command ini meneruskan lifecycle ke arah rilis dan operasional — biasanya dijalankan di sesi terpisah saat Anda siap ship:

| Command | Deskripsi |
| ------- | ----------- |
| `/pandawa.deploy` | Siapkan otomasi deployment — containerization, pipeline CI/CD, dan config environment — mengikuti Plan-Verify-Generate. Tidak pernah melakukan deploy live tanpa konfirmasi eksplisit; secara default berhenti di artefak yang tervalidasi + dry-run |
| `/pandawa.operate` | Wire observability (log/metric/trace/health), analisis telemetry untuk mendeteksi anomali, dan bantu investigasi + penyelesaian insiden produksi (memakai disiplin scoped-edit `/pandawa.redesign`) |
| `/pandawa.postmortem` | Tutup loop feedback SDD — ubah insiden/telemetry/pembelajaran produksi menjadi update spec, NFR, dan constitution supaya perbaikan bertahan di regenerasi berikutnya. Tidak menyentuh kode aplikasi |

### Variabel Environment

| Variabel | Deskripsi |
| -------- | ----------- |
| `PANDAWA_FEATURE` | Override deteksi fitur untuk repository non-Git. Set ke nama direktori fitur (mis., `001-photo-albums`) untuk mengerjakan fitur tertentu saat tidak memakai Git branch.<br/>**Harus di-set dalam konteks agen yang Anda pakai sebelum memakai `/pandawa.plan` atau command lanjutannya.** |

## 📚 Filosofi Inti

Spec-Driven Development adalah proses terstruktur yang menekankan:

- **Pengembangan berbasis intent** di mana spesifikasi mendefinisikan "*apa*" sebelum "*bagaimana*"
- **Pembuatan spesifikasi yang kaya** memakai guardrail dan prinsip organisasi
- **Refinement multi-langkah** alih-alih generasi kode sekali-jadi dari prompt
- **Bergantung besar** pada kemampuan model AI tingkat lanjut untuk interpretasi spesifikasi

## 🌟 Fase Pengembangan

| Fase                                    | Fokus                    | Aktivitas Utama                                                                                                                                                     |
| ---------------------------------------- | ------------------------ | ------------------------------------------------------------------------------------------------------------------------------------------------------------------ |
| **Pengembangan 0-ke-1** ("Greenfield")    | Generate dari nol    | <ul><li>Mulai dari requirement level tinggi</li><li>Generate spesifikasi</li><li>Rencanakan langkah implementasi</li><li>Bangun aplikasi yang siap produksi</li></ul> |
| **Eksplorasi Kreatif**                 | Implementasi paralel | <ul><li>Eksplorasi solusi yang beragam</li><li>Dukung berbagai tech stack & arsitektur</li><li>Eksperimen dengan pattern UX</li></ul>                         |
| **Peningkatan Iteratif** ("Brownfield") | Modernisasi brownfield | <ul><li>Tambah fitur secara iteratif</li><li>Modernisasi sistem legacy</li><li>Adaptasi proses</li></ul>                                                                |

## 🎯 Tujuan Eksperimental

Riset dan eksperimen kami berfokus pada:

### Kemandirian teknologi

- Membuat aplikasi memakai tech stack yang beragam
- Memvalidasi hipotesis bahwa Spec-Driven Development adalah sebuah proses, bukan terikat pada teknologi, bahasa programming, atau framework tertentu

### Batasan enterprise

- Mendemonstrasikan pengembangan aplikasi mission-critical
- Menggabungkan batasan organisasi (cloud provider, tech stack, praktik engineering)
- Mendukung design system enterprise dan requirement compliance

### Pengembangan yang berpusat pada user

- Membangun aplikasi untuk kohor dan preferensi user yang berbeda
- Mendukung berbagai pendekatan pengembangan (dari vibe-coding sampai AI-native development)

### Proses kreatif & iteratif

- Memvalidasi konsep eksplorasi implementasi paralel
- Menyediakan workflow pengembangan fitur iteratif yang robust
- Memperluas proses untuk menangani upgrade dan modernisasi

## 🔧 Prasyarat

- **Linux/macOS/Windows**
- Agen coding AI yang [didukung](#-agen-ai-yang-didukung).
- [uv](https://docs.astral.sh/uv/) untuk manajemen package
- [Python 3.11+](https://www.python.org/downloads/)
- [Git](https://git-scm.com/downloads)

Jika Anda mengalami masalah dengan sebuah agen, silakan buka issue supaya kami bisa memperbaiki integrasinya.

## 📖 Pelajari Lebih Lanjut

- **[Metodologi Spec-Driven Development Lengkap](./spec-driven.md)** - Pendalaman proses secara menyeluruh
- **[Walkthrough Detail](#-proses-detail)** - Panduan implementasi langkah-demi-langkah

---

## 📋 Proses Detail

<details>
<summary>Klik untuk membuka walkthrough langkah-demi-langkah secara detail</summary>

Anda bisa memakai CLI Pandawa untuk bootstrap project Anda, yang akan membawa masuk artefak yang dibutuhkan ke environment Anda. Jalankan:

```bash
pandawa init <nama_project>
```

Atau inisialisasi di direktori saat ini:

```bash
pandawa init .
# atau pakai flag --here
pandawa init --here
# Skip konfirmasi saat direktori sudah punya file
pandawa init . --force
# atau
pandawa init --here --force
```

![Specify CLI bootstrapping a new project in the terminal](./media/pandawa_cli.gif)

Anda akan diminta memilih agen AI yang Anda pakai. Anda juga bisa langsung menyebutkannya di terminal:

```bash
pandawa init <nama_project> --ai claude
pandawa init <nama_project> --ai gemini
pandawa init <nama_project> --ai copilot

# Atau di direktori saat ini:
pandawa init . --ai claude
pandawa init . --ai codex

# atau pakai flag --here
pandawa init --here --ai claude
pandawa init --here --ai codex

# Paksa merge ke direktori saat ini yang tidak kosong
pandawa init . --force --ai claude

# atau
pandawa init --here --force --ai claude
```

CLI akan mengecek apakah Anda punya Claude Code, Gemini CLI, Cursor CLI, Qwen CLI, opencode, Codex CLI, Qoder CLI, atau Amazon Q Developer CLI terinstal. Jika tidak, atau Anda lebih memilih mendapatkan template tanpa pengecekan tool yang tepat, pakai `--ignore-agent-tools` dengan command Anda:

```bash
pandawa init <nama_project> --ai claude --ignore-agent-tools
```

### **LANGKAH 1:** Tetapkan prinsip project

Buka folder project dan jalankan agen AI Anda. Dalam contoh kami, kami memakai `claude`.

Anda akan tahu semuanya sudah dikonfigurasi dengan benar jika Anda melihat command `/pandawa.constitution`, `/pandawa.specify`, `/pandawa.plan`, `/pandawa.tasks`, dan `/pandawa.implement` tersedia.

Langkah pertama sebaiknya menetapkan prinsip pengaturan project Anda memakai command `/pandawa.constitution`. Ini membantu memastikan pengambilan keputusan yang konsisten di semua fase pengembangan berikutnya:

```text
/pandawa.constitution Buat prinsip yang berfokus pada kualitas kode, standar testing, konsistensi user experience, dan requirement performa. Sertakan governance tentang bagaimana prinsip-prinsip ini harus memandu keputusan teknis dan pilihan implementasi.
```

Langkah ini membuat atau memperbarui file `.pandawa/memory/constitution.md` dengan pedoman fundamental project Anda yang akan dirujuk oleh agen AI selama fase spesifikasi, planning, dan implementasi.

### **LANGKAH 2:** Buat spesifikasi project

Setelah prinsip project ditetapkan, Anda sekarang bisa membuat spesifikasi fungsional. Gunakan command `/pandawa.specify` lalu berikan requirement konkret untuk project yang ingin Anda kembangkan.

> [!IMPORTANT]
> Jelaskan sedetail mungkin tentang *apa* yang Anda coba bangun dan *mengapa*. **Jangan fokus ke tech stack pada tahap ini**.

Contoh prompt:

```text
Kembangkan Taskify, platform produktivitas tim. Aplikasi ini harus memungkinkan user membuat project, menambah anggota
tim, menugaskan task, berkomentar dan memindahkan task antar board dengan gaya Kanban. Di fase awal untuk fitur ini,
kita sebut "Create Taskify", kita akan punya banyak user tapi user-nya akan dideklarasikan lebih dulu, sudah ditentukan.
Saya ingin lima user dalam dua kategori berbeda, satu product manager dan empat engineer. Buat tiga project sample
yang berbeda. Kita pakai kolom Kanban standar untuk status setiap task, seperti "To Do,"
"In Progress," "In Review," dan "Done." Tidak akan ada login untuk aplikasi ini karena ini baru pengujian awal
untuk memastikan fitur dasar kita sudah siap. Untuk setiap task di UI, di kartu task,
Anda harus bisa mengubah status task saat ini antar kolom di board Kanban. Anda harus bisa
meninggalkan komentar tanpa batas untuk sebuah kartu tertentu. Anda harus bisa, dari kartu task
itu, menugaskan salah satu user yang valid. Saat pertama kali membuka Taskify, akan muncul daftar lima user untuk dipilih.
Tidak akan ada password yang dibutuhkan. Saat Anda klik seorang user, Anda masuk ke tampilan utama, yang menampilkan daftar
project. Saat Anda klik sebuah project, Anda membuka board Kanban untuk project tersebut. Anda akan melihat kolom-kolomnya.
Anda bisa drag-and-drop kartu bolak-balik antar kolom yang berbeda. Anda akan melihat kartu apa pun yang
ditugaskan ke Anda, user yang sedang login saat ini, dengan warna berbeda dari yang lain, agar Anda bisa cepat
melihat milik Anda. Anda bisa mengedit komentar yang Anda buat sendiri, tapi tidak bisa mengedit komentar orang lain. Anda bisa
menghapus komentar yang Anda buat sendiri, tapi tidak bisa menghapus komentar milik orang lain.
```

Setelah prompt ini dimasukkan, Anda akan melihat Claude Code memulai proses planning dan penyusunan spec. Claude Code juga akan memicu beberapa script built-in untuk menyiapkan repository.

Setelah langkah ini selesai, Anda seharusnya sudah punya branch baru (mis., `001-create-taskify`), plus spesifikasi baru di direktori `specs/001-create-taskify`.

Spesifikasi yang dihasilkan sebaiknya berisi kumpulan user story dan functional requirement, sesuai yang didefinisikan dalam template.

Pada tahap ini, isi folder project Anda seharusnya mirip seperti ini:

```text
└── .pandawa
    ├── memory
    │  └── constitution.md
    ├── scripts
    │  ├── check-prerequisites.sh
    │  ├── common.sh
    │  ├── create-new-feature.sh
    │  ├── setup-plan.sh
    │  └── update-claude-md.sh
    ├── specs
    │  └── 001-create-taskify
    │      └── spec.md
    └── templates
        ├── plan-template.md
        ├── spec-template.md
        └── tasks-template.md
```

### **LANGKAH 3:** Klarifikasi spesifikasi fungsional (wajib sebelum planning)

Dengan spesifikasi dasar sudah dibuat, Anda bisa lanjut mengklarifikasi requirement mana pun yang belum tertangkap dengan tepat pada percobaan pertama.

Anda sebaiknya menjalankan workflow klarifikasi terstruktur **sebelum** membuat technical plan untuk mengurangi rework di kemudian hari.

Urutan yang disarankan:

1. Gunakan `/pandawa.clarify` (terstruktur) – pertanyaan sekuensial berbasis coverage yang mencatat jawaban di section Clarifications.
2. Opsional: lanjutkan dengan refinement ad-hoc bebas jika masih ada yang terasa kurang jelas.

Jika Anda sengaja ingin skip klarifikasi (mis., spike atau prototipe eksploratif), sebutkan itu secara eksplisit supaya agen tidak terhenti karena klarifikasi yang belum ada.

Contoh prompt refinement bebas (setelah `/pandawa.clarify` jika masih dibutuhkan):

```text
Untuk setiap project sample atau project yang Anda buat harus ada jumlah task yang bervariasi antara 5 sampai 15
task untuk masing-masing, terdistribusi secara acak ke berbagai status penyelesaian. Pastikan ada
minimal satu task di setiap tahap penyelesaian.
```

Anda juga sebaiknya meminta Claude Code memvalidasi **Review & Acceptance Checklist**, mencentang hal-hal yang sudah divalidasi/lolos requirement, dan membiarkan yang belum tetap tidak tercentang. Prompt berikut bisa dipakai:

```text
Baca review and acceptance checklist, dan centang setiap item di checklist jika feature spec memenuhi kriterianya. Biarkan kosong jika tidak.
```

Penting untuk memanfaatkan interaksi dengan Claude Code sebagai kesempatan untuk mengklarifikasi dan mengajukan pertanyaan seputar spesifikasi - **jangan anggap percobaan pertamanya sebagai final**.

### **LANGKAH 4:** Generate plan

Anda sekarang bisa spesifik tentang tech stack dan requirement teknis lainnya. Anda bisa memakai command `/pandawa.plan` yang sudah built-in di template project dengan prompt seperti ini:

```text
Kita akan generate ini memakai .NET Aspire, dengan Postgres sebagai database. Frontend-nya harus memakai
Blazor server dengan drag-and-drop task board, real-time update. Harus ada REST API yang dibuat dengan projects API,
tasks API, dan notifications API.
```

Output dari langkah ini akan mencakup sejumlah dokumen detail implementasi, dengan struktur direktori Anda mirip seperti ini:

```text
.
├── CLAUDE.md
├── memory
│  └── constitution.md
├── scripts
│  ├── check-prerequisites.sh
│  ├── common.sh
│  ├── create-new-feature.sh
│  ├── setup-plan.sh
│  └── update-claude-md.sh
├── specs
│  └── 001-create-taskify
│      ├── contracts
│      │  ├── api-spec.json
│      │  └── signalr-spec.md
│      ├── data-model.md
│      ├── plan.md
│      ├── quickstart.md
│      ├── research.md
│      └── spec.md
└── templates
    ├── CLAUDE-template.md
    ├── plan-template.md
    ├── spec-template.md
    └── tasks-template.md
```

Cek dokumen `research.md` untuk memastikan tech stack yang tepat dipakai, sesuai instruksi Anda. Anda bisa meminta Claude Code memperbaikinya jika ada komponen yang terasa aneh, atau bahkan meminta ia mengecek versi platform/framework yang terinstal lokal yang Anda inginkan (mis., .NET).

Selain itu, Anda mungkin ingin meminta Claude Code meriset detail tentang tech stack yang dipilih jika itu sesuatu yang berubah cepat (mis., .NET Aspire, framework JS), dengan prompt seperti ini:

```text
Saya ingin Anda menelusuri implementation plan dan detail implementasi, mencari area yang bisa
diuntungkan dari riset tambahan karena .NET Aspire adalah library yang cepat berubah. Untuk area yang Anda identifikasi
membutuhkan riset lebih lanjut, saya ingin Anda memperbarui dokumen riset dengan detail tambahan tentang versi
spesifik yang akan kita pakai di aplikasi Taskify ini dan menjalankan task riset paralel untuk mengklarifikasi
detail apa pun memakai riset dari web.
```

Selama proses ini, Anda mungkin menemukan Claude Code terjebak meriset hal yang salah - Anda bisa membantu mengarahkannya ke arah yang benar dengan prompt seperti ini:

```text
Saya pikir kita perlu memecah ini menjadi serangkaian langkah. Pertama, identifikasi daftar task
yang Anda perlukan selama implementasi yang Anda belum yakin atau akan diuntungkan
dari riset lebih lanjut. Tuliskan daftar task-task tersebut. Lalu untuk setiap task ini,
saya ingin Anda menjalankan task riset terpisah sehingga hasil akhirnya kita
meriset semua task spesifik tersebut secara paralel. Yang saya lihat Anda lakukan sepertinya Anda
meriset .NET Aspire secara umum dan saya tidak yakin itu akan berguna banyak untuk kita dalam kasus ini.
Riset itu terlalu tidak terarah. Riset perlu membantu Anda menyelesaikan pertanyaan spesifik yang tertarget.
```

> [!NOTE]
> Claude Code mungkin terlalu bersemangat dan menambahkan komponen yang tidak Anda minta. Minta ia mengklarifikasi rationale dan sumber dari perubahan tersebut.

### **LANGKAH 5:** Minta Claude Code memvalidasi plan

Dengan plan sudah ada, Anda sebaiknya meminta Claude Code menelusurinya untuk memastikan tidak ada bagian yang terlewat. Anda bisa memakai prompt seperti ini:

```text
Sekarang saya ingin Anda mengaudit implementation plan dan file detail implementasi.
Baca dengan fokus menentukan apakah ada urutan task yang perlu Anda lakukan yang jelas
terlihat dari membacanya. Karena saya tidak tahu apakah ini cukup lengkap. Misalnya,
saat saya lihat core implementation, akan berguna untuk merujuk ke bagian yang tepat di detail
implementasi tempat ia bisa menemukan informasi saat menelusuri setiap langkah di core implementation atau di refinement.
```

Ini membantu memperbaiki implementation plan dan membantu Anda menghindari potensi blind spot yang terlewat oleh Claude Code di siklus planning-nya. Setelah pass refinement awal selesai, minta Claude Code menelusuri checklist sekali lagi sebelum Anda lanjut ke implementasi.

Anda juga bisa meminta Claude Code (jika Anda punya [GitHub CLI](https://docs.github.com/en/github-cli/github-cli) terinstal) untuk membuat pull request dari branch Anda saat ini ke `main` dengan deskripsi lengkap, untuk memastikan upaya ini terlacak dengan baik.

> [!NOTE]
> Sebelum Anda meminta agen mengimplementasikannya, ada baiknya juga meminta Claude Code untuk cross-check detailnya, melihat apakah ada bagian yang over-engineered (ingat - ia bisa terlalu bersemangat). Jika ada komponen atau keputusan yang over-engineered, Anda bisa meminta Claude Code menyelesaikannya. Pastikan Claude Code mengikuti [constitution](base/memory/constitution.md) sebagai bagian fundamental yang harus dipatuhi saat menetapkan plan.

### **LANGKAH 6:** Generate task breakdown dengan /pandawa.tasks

Setelah implementation plan divalidasi, Anda sekarang bisa memecah plan menjadi task spesifik dan actionable yang bisa dieksekusi dalam urutan yang benar. Gunakan command `/pandawa.tasks` untuk secara otomatis menghasilkan task breakdown detail dari implementation plan Anda:

```text
/pandawa.tasks
```

Langkah ini membuat file `tasks.md` di direktori spesifikasi fitur Anda yang berisi:

- **Task breakdown yang diorganisir per user story** - Setiap user story menjadi fase implementasi terpisah dengan kumpulan task-nya sendiri
- **Manajemen dependency** - Task diurutkan untuk menghormati dependency antar komponen (mis., model sebelum service, service sebelum endpoint)
- **Marker eksekusi paralel** - Task yang bisa berjalan paralel ditandai dengan `[P]` untuk mengoptimalkan workflow pengembangan
- **Spesifikasi file path** - Setiap task mencakup file path yang tepat tempat implementasi harus dilakukan
- **Struktur test-driven development** - Jika test diminta, task test disertakan dan diurutkan agar ditulis sebelum implementasi
- **Validasi checkpoint** - Setiap fase user story menyertakan checkpoint untuk memvalidasi fungsionalitas independen

File tasks.md yang dihasilkan menyediakan roadmap yang jelas untuk command `/pandawa.implement`, memastikan implementasi sistematis yang mempertahankan kualitas kode dan memungkinkan delivery user story secara incremental.

### **LANGKAH 7:** Implementasi

Setelah siap, gunakan command `/pandawa.implement` untuk mengeksekusi implementation plan Anda:

```text
/pandawa.implement
```

Command `/pandawa.implement` akan:

- Memvalidasi bahwa semua prerequisite sudah ada (constitution, spec, plan, dan tasks)
- Mem-parse task breakdown dari `tasks.md`
- Mengeksekusi task dalam urutan yang benar, menghormati dependency dan marker eksekusi paralel
- Mengikuti pendekatan TDD yang didefinisikan di task plan Anda
- Menyediakan update progress dan menangani error dengan tepat

> [!IMPORTANT]
> Agen AI akan mengeksekusi command CLI lokal (seperti `dotnet`, `npm`, dst) - pastikan Anda punya tool yang dibutuhkan terinstal di mesin Anda.

Setelah implementasi selesai, uji aplikasinya dan selesaikan error runtime apa pun yang mungkin tidak terlihat di log CLI (mis., error console browser). Anda bisa menyalin dan menempelkan error semacam itu kembali ke agen AI Anda untuk diselesaikan.

</details>

---

## 🔍 Pemecahan Masalah

### Git Credential Manager di Linux

Jika Anda mengalami masalah dengan autentikasi Git di Linux, Anda bisa menginstal Git Credential Manager:

```bash
#!/usr/bin/env bash
set -e
echo "Downloading Git Credential Manager v2.6.1..."
wget https://github.com/git-ecosystem/git-credential-manager/releases/download/v2.6.1/gcm-linux_amd64.2.6.1.deb
echo "Installing Git Credential Manager..."
sudo dpkg -i gcm-linux_amd64.2.6.1.deb
echo "Configuring Git to use GCM..."
git config --global credential.helper manager
echo "Cleaning up..."
rm gcm-linux_amd64.2.6.1.deb
```

## 💬 Dukungan

Untuk dukungan, silakan buka [GitHub issue](https://git.neuron.id/research/pandawa/issues/new). Kami menyambut laporan bug, permintaan fitur, dan pertanyaan seputar pemakaian Spec-Driven Development.

## 📄 Lisensi

Project ini dilisensikan di bawah ketentuan lisensi open source MIT. Silakan lihat file [LICENSE](./LICENSE) untuk ketentuan lengkapnya.
