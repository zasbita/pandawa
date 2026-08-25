# Panduan Instalasi & Penggunaan Pandawa

Panduan praktis memakai **Pandawa** pada project Anda — dioptimalkan untuk alur kerja umum:
**buka project di VS Code** (untuk terminal) + **Claude Code lewat extension VS Code**.

> Ringkas: `pandawa` adalah **CLI** (dijalankan di **terminal**) yang menyiapkan project untuk
> Spec-Driven Development dan mengelola plugin (skill & governance) dari marketplace privat.
> Pekerjaan AI sehari-hari (`/pandawa.*`, skill) berjalan **di dalam Claude Code**.

---

## 1. Konsep penting (baca dulu)

### Dua "permukaan" yang berbeda

| Di mana | Untuk apa | Contoh |
|---|---|---|
| **Terminal VS Code** (shell, di root project) | Setup project & **kelola plugin** | `pandawa init`, `pandawa skill …`, `pandawa governance …` |
| **Extension Claude Code** (chat) | Pekerjaan AI | `/pandawa.specify`, `/pandawa.plan`, concierge `/pandawa`, skill auto-trigger |

`pandawa …` **selalu** di terminal, dengan **cwd = root project** (ia membaca `.claude/` & `.pandawa/`
dari direktori aktif).

### Dua tipe plugin

- **`skill`** — kemampuan biasa (mis. `docs-pack` = docx/pdf/pptx/xlsx). **Boleh banyak aktif.**
- **`governance`** — kerangka standar/konstitusi (mis. `tmf-oda-constitution`). **Hanya satu boleh aktif** per project. Pola **unduh dulu → baru aktifkan**.

### Alur status plugin

```text
available (di marketplace) ──install──▶ installed (lokal) ──use/enable──▶ active
```

- Konten plugin diunduh ke **store lokal Claude Code** (lewat `claude plugin install` yang dipanggil pandawa).
- Aktivasi dicatat di `.claude/settings.json` (`enabledPlugins`).

---

## 2. Prasyarat

- **VS Code** + **extension Claude Code**.
- **Claude Code CLI** (`claude`) di PATH — wajib untuk install/uninstall plugin (skill & governance bersifat Claude-only).
- **Python ≥ 3.11** dan **uv** (untuk memasang CLI pandawa).
- **GitLab token** (`GL_TOKEN` atau `GITLAB_TOKEN`) — repo pandawa & marketplace bersifat privat.

---

## 3. Pasang CLI Pandawa (sekali per mesin)

```bash
uv tool install pandawa-cli --from git+https://git.neuron.id/research/pandawa.git
pandawa check        # verifikasi tooling
pandawa version
```

Set token (sekali):

```bash
export GL_TOKEN="<personal-access-token>"   # scope: read_api
# Windows PowerShell: $env:GL_TOKEN="<token>"
```

---

## 4. Inisialisasi di project Anda

Buka folder app Anda di VS Code, lalu di **terminal terintegrasi** (View → Terminal):

**Project yang sudah ada (sedang dikembangkan):**

```bash
cd /path/ke/app-anda      # pastikan di root project
pandawa init --here         # tanpa --ai → default ke claude
```

**Project baru:**

```bash
pandawa init nama-project   # default claude
```

`pandawa init` bersifat **aman & additive** untuk project existing:

- Menulis: `.claude/settings.json` (pointer marketplace + `pandawa-core` aktif + guardrail + hook guard), `.pandawa/` (katalog governance + skрипt guard), command `/pandawa.*`, dan `CLAUDE.md` (jika belum ada).
- **Tidak menyentuh** source code Anda; settings di-*merge*, `CLAUDE.md` tidak ditimpa.

Flag berguna: `--ai <agent>` (override), `--no-marketplace`, `--no-guardrails`, `--no-git`,
`--script sh|ps`, `--ignore-agent-tools`.

Setelah init: project **fresh** — hanya `pandawa-core` (skill) yang aktif; **belum ada governance**.

> **Project yang sudah ada?** Setelah init, jalankan `/pandawa.brd` di Claude Code
> **sebelum** `/pandawa.specify` — perintah ini membaca codebase existing dan membuat
> semantic map ringkas per modul di `docs/brd/` (`00-overview.md` sistem-wide, plus
> satu `modules/<slug>.md` terse per modul: capability, entity, API surface, data flow,
> dependency, test coverage) sebagai konteks bisnis awal, supaya fitur baru bisa
> direncanakan dengan pemahaman penuh tentang sistem yang sudah berjalan (bukan mulai
> dari nol) — dengan biaya token jauh lebih kecil dari dokumen penuh.

---

## 5. Aktifkan di Claude Code (extension)

1. Buka/segarkan project di VS Code.
2. Claude Code akan meminta **Trust folder** → setujui. Ia otomatis mendaftarkan marketplace `pandawa` (clone ke lokal) dan mengaktifkan `pandawa-core`.
3. Mulai pakai SDD di chat:
   - `/pandawa.brd` → (project existing) generate BRD dari codebase sebagai konteks
   - `/pandawa.specify` → definisikan kebutuhan fitur
   - `/pandawa.plan` → rencana teknis
   - `/pandawa.tasks` → pecah menjadi tugas
   - `/pandawa.implement` → implementasi
   - atau `/pandawa <maksud Anda>` (concierge yang merutekan otomatis)

> Setiap kali Anda mengubah plugin lewat terminal (langkah 6–7), **reload Claude Code**:
> `Ctrl/Cmd+Shift+P` → **Developer: Reload Window**.

---

## 6. Kelola SKILL (di terminal)

```bash
pandawa skill list marketplace     # lihat skill tersedia (tanda terinstall/belum)
pandawa skill install docs-pack    # unduh + aktifkan (langsung siap)
pandawa skill list                 # konfirmasi yang terinstall lokal
pandawa skill disable docs-pack    # matikan tanpa hapus (opsional)
pandawa skill enable  docs-pack    # nyalakan lagi
pandawa skill uninstall docs-pack  # hapus dari lokal
```

→ **Reload Claude Code.** Skill (mis. docx/pdf) akan otomatis dipakai saat relevan.

---

## 7. Kelola GOVERNANCE (di terminal) — unduh dulu, baru pakai

```bash
pandawa governance list marketplace             # lihat governance tersedia
pandawa governance install tmf-oda-constitution # 1) UNDUH ke lokal (belum aktif)
pandawa governance use tmf-oda-constitution      # 2) AKTIFKAN (eksklusif, satu saja)
pandawa governance status                        # cek governance aktif
pandawa governance list                          # governance terinstall lokal
```

→ **Reload Claude Code.**

**Ganti governance** (eksklusif — nonaktifkan dulu):

```bash
pandawa governance disable                       # matikan yang aktif
pandawa governance use <governance-lain>         # harus sudah ter-install
# atau satu langkah:
pandawa governance use <governance-lain> --force
```

→ **Reload Claude Code.**

**Sinkron katalog** saat kontributor menambah governance baru di marketplace:

```bash
pandawa governance refresh
```

> **Guard otomatis:** jika sampai **dua governance aktif** bersamaan (mis. akibat edit manual),
> hook akan **memblokir perubahan repositori** sampai Anda menyisakan satu (`pandawa governance disable`
> lalu `use`), kemudian reload.

---

## 8. Kerja tim

`.claude/settings.json` dan `.pandawa/` **di-commit** ke repo project:

```bash
git add .claude/settings.json .pandawa CLAUDE.md
git commit -m "Aktifkan Pandawa untuk project ini"
```

Rekan setim cukup **Trust folder** di Claude Code → mendapat marketplace, plugin aktif, katalog
governance, dan guard yang sama.

---

## 9. Troubleshooting

| Gejala | Penyebab & solusi |
|---|---|
| `claude CLI not found` saat install plugin | Pasang Claude Code CLI / tambahkan ke PATH. |
| Gagal fetch marketplace / `refresh` exit 1 | Cek jaringan & `GL_TOKEN`. Katalog cache tetap dipakai (offline aman). |
| `'<x>' is not installed locally yet` saat `use` | Jalankan `pandawa governance install <x>` dulu, baru `use`. |
| Perubahan plugin tak terasa | **Reload Claude Code** (Developer: Reload Window). |
| Peringatan/blokir "GOVERNANCE CONFLICT" | Dua governance aktif → `pandawa governance disable` lalu `use` satu, reload. |
| Perintah `pandawa …` menyasar project lain | Pastikan terminal **di root project** (cwd benar). |

---

## 10. Ringkasan perintah

**Terminal (di root project):**

```bash
pandawa init --here                         # setup (default claude)
pandawa skill list | list marketplace | install <x> | uninstall <x> | enable <x> | disable <x>
pandawa governance list | list marketplace | install <x> | use <x> [--force] | disable | uninstall <x> | status | refresh
pandawa check | version
```

**Di Claude Code (chat):**

```text
/pandawa.constitution  /pandawa.brd  /pandawa.specify  /pandawa.plan  /pandawa.tasks  /pandawa.implement
/pandawa.clarify  /pandawa.analyze  /pandawa.checklist  /pandawa.test  /pandawa.redesign
/pandawa <maksud bebas>      # concierge
```

---

**Inti:** kelola plugin di **terminal** (`pandawa …`), kerjakan fitur di **Claude Code** (`/pandawa.*`),
dan **reload Claude Code** setiap selesai mengubah plugin.
