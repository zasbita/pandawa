# Roadmap Pengembangan PANDAWA

> Disusun dari sudut pandang product management, berdasarkan kondisi repo per **2026-07-02**.
> PANDAWA saat ini: CLI Spec-Driven Development (fork/turunan `spec-kit`) yang menyiapkan project untuk bekerja dengan Claude Code, mendistribusikan **skill** & **governance** lewat plugin marketplace privat (GitLab), dengan fokus domain TM Forum ODA untuk delivery enterprise.

---

## 1. Tujuan Akhir (North Star)

**"Vibe coding" bukan tujuan — itu justru masalah yang PANDAWA coba selesaikan.**

Definisi tujuan akhir PANDAWA:

> Mengubah AI-assisted coding dari *ad-hoc prompting yang hasilnya tidak dapat diprediksi* menjadi **proses delivery software yang punya kontrak, terukur, dan reusable** — di mana spesifikasi (bukan prompt sesaat) menjadi sumber kebenaran yang bisa dieksekusi ulang, divalidasi, dan diwariskan ke anggota tim/agent lain.

Tiga pilar yang harus terus dijaga selaras di setiap fase roadmap:

| Pilar | Pertanyaan yang harus dijawab tiap fitur baru |
|---|---|
| **People** | Apakah ini mengurangi beban kognitif engineer/PM, atau malah menambah langkah manual? Apakah non-expert (yang tidak paham TM Forum/ODA) bisa tetap produktif? |
| **Process** | Apakah tahapan (specify → plan → tasks → implement → validate) tetap dapat diaudit? Apakah governance (constitution/plugin) bisa di-enforce, bukan sekadar dokumentasi? |
| **Tech** | Apakah kontrak antar-agent (MCP, skill schema, plugin format) tetap kompatibel lintas AI assistant, bukan hanya Claude? |

**Anti-goal**: PANDAWA jangan menjadi "framework prompt yang berat" — kalau overhead spesifikasi lebih mahal dari manfaat prediktabilitasnya untuk task kecil, itu kegagalan desain.

---

## 2. Kondisi Saat Ini (Baseline)

- CLI (`pandawa init/check/skill/governance/run/usage`) berbasis Python + `uv`.
- Distribusi via GitLab privat, terikat ke `GL_TOKEN`.
- Coupling erat ke **Claude Code** (plugin marketplace = mekanisme Claude Code, `.claude/settings.json`).
- Command inti: `/pandawa.constitution`, `/pandawa.specify`, `/pandawa.plan`, `/pandawa.tasks`, `/pandawa.implement`, `/pandawa.test`, orkestrasi `/pandawa.ultimate`. Untuk brownfield: `/pandawa.brd` (reverse-engineer semantic map ringkas per modul dari codebase existing sebagai konteks awal, sebelum `specify`/`constitution`). Operations track (opsional, pasca-implement): `/pandawa.deploy`, `/pandawa.operate`, `/pandawa.postmortem` — meluaskan lifecycle ke rilis/operasional dan menutup loop feedback ke spec, selaras dengan lifecycle penuh AI-DLC.
- Domain-specific: template TM Forum ODA (NestJS backend, React CRACO microfrontend).
- Governance = "satu aktif per project" (constitution), skill = "boleh banyak aktif".
- Belum ada GUI — semuanya CLI + chat (VS Code + Claude Code extension).
- Belum ada marketplace agent lintas-organisasi (baru marketplace plugin internal, privat).

**Koreksi asumsi awal**: PANDAWA **sudah agent-agnostic dan cross-OS** di level command/template — `pandawa init --ai <claude|gemini|copilot|cursor-agent|codex|windsurf|qwen|opencode|...>` men-generate command/rules untuk >10 assistant berbeda (lihat `AGENT_CONFIG` di `src/pandawa_cli/__init__.py`), berjalan di atas Python + `uv` yang portable lintas OS. Jadi **bukan lock-in di layer inti** yang jadi masalah. Satu-satunya bagian yang memang Claude-Code-specific: mekanisme **distribusi plugin (skill/governance) via marketplace** — ini eksplisit disebutkan di CHANGELOG ("Non-Claude assistants are skipped, mekanisme ini Claude Code-specific"). Itu risiko yang sempit (satu subsistem), bukan risiko arsitektur PANDAWA secara keseluruhan.

**Risiko struktural yang lebih relevan untuk disadari:**

1. **Distribusi skill/governance masih 1 mekanisme (Claude Code plugin)** — kalau tim mau pakai skill yang sama di Gemini CLI/Copilot/Cursor, belum ada jalan otomatis; harus rebuild manual per format masing-masing assistant.
2. **Governance sebagai konvensi, bukan enforcement teknis** — constitution/skill baru "dicatat" di settings.json, belum tervalidasi otomatis di CI secara ketat untuk semua repo turunan.
3. **Tidak ada telemetry/analytics penggunaan** di luar `pandawa usage` lokal → PM tidak punya visibilitas agregat (fitur mana yang dipakai, di mana orang macet).
4. **PANDAWA/agent yang dijalankan PANDAWA belum terhubung ke tools eksternal secara standar** — kalau spec/plan/task perlu data dari Jira, GitLab issue, database, TM Forum API catalog, dsb, itu masih manual (copy-paste ke prompt) karena belum ada koneksi MCP client bawaan.

---

## 3. Roadmap

### Fase 0 — Pengerasan Fondasi (0–1 bulan)

Tujuan: pastikan yang sudah ada solid sebelum menambah scope baru.

- [ ] Tuntaskan `/pandawa.test` (sudah "Unreleased" di CHANGELOG) → rilis stabil.
- [ ] Enforcement governance di CI: constitution aktif harus tervalidasi (bukan cuma tercatat), gagal build kalau melanggar.
- [ ] Instrumentasi dasar: `pandawa usage` dikirim (opt-in, anonim) ke satu tempat agregasi → dasar data untuk roadmap berikutnya.
- [ ] Dokumentasi arsitektur plugin (skill vs governance) dipisah jelas dari "cara pakai" (PANDUAN.md) agar bisa dibaca kontributor eksternal.

### Fase 1 — PANDAWA sebagai MCP *Client* Hub, bukan MCP server (1–3 bulan)

Bukan soal portabilitas command (itu sudah selesai) — ini soal **menyambungkan agent yang dijalankan PANDAWA ke tools eksternal** lewat MCP, supaya spec/plan/task tidak lagi bergantung pada copy-paste manual dari sistem lain.

- [ ] `pandawa init` menyediakan **template konfigurasi MCP server** siap pakai per domain (mis. GitLab/Jira untuk tracking, database untuk skema, TM Forum ODA catalog/API registry untuk konteks arsitektur) — supaya assistant apapun (Claude Code, Cursor, dst — semua sudah dukung MCP client) langsung bisa connect begitu project di-init.
- [ ] `pandawa skill` bisa mem-bundle **rekomendasi MCP server** sebagai bagian dari sebuah skill package — contoh: skill "tmf-oda-constitution" merekomendasikan MCP server katalog TM Forum resmi, skill "docs-pack" merekomendasikan MCP server Confluence/Notion.
- [ ] `/pandawa.specify` & `/pandawa.plan` diarahkan untuk **memanfaatkan MCP tools yang ter-connect** (ambil requirement dari Jira via MCP, cek skema DB aktual via MCP) alih-alih assistant menebak dari deskripsi teks — ini yang bikin output spec lebih akurat terhadap kondisi nyata sistem.
- [ ] Governance check bisa memvalidasi **MCP server apa yang boleh/wajib terhubung** di suatu project (mis. project TM Forum wajib connect ke MCP catalog ODA) — governance meluas dari "aturan kode" jadi "aturan koneksi tooling".

**Kenapa ini yang lebih tepat dibanding rencana awal saya**: nilai MCP di sini bukan untuk membuat PANDAWA portable (sudah portable), tapi untuk membuat **setiap agent yang dipakai lewat PANDAWA punya akses konteks eksternal yang konsisten dan ter-govern** — apapun assistant-nya. Ini juga yang bikin ide marketplace kamu (Fase 3) lebih masuk akal: yang dijual bukan cuma "skill/prompt", tapi juga "paket koneksi MCP siap pakai + governance-nya" untuk domain tertentu (mis. paket "TM Forum ODA delivery" = skill + governance + rekomendasi MCP server yang relevan).

### Fase 2 — GUI untuk PANDAWA (3–5 bulan)

Bukan mengganti CLI, tapi **lapisan visual untuk peran yang bukan power-user terminal** (PM, QA, stakeholder non-teknis).

Prioritas fitur GUI (bukan "IDE baru", fokus ke titik lemah CLI saat ini):

1. **Visual spec/plan/tasks viewer & editor** — spec-driven artifacts (`specify`/`plan`/`tasks`) saat ini file markdown mentah. GUI menampilkannya sebagai dokumen terstruktur yang bisa dikomentari/di-approve (mirip PR review), bukan cuma dibaca di editor.
2. **Governance/skill marketplace browser** — install/enable/disable plugin dari UI, lihat versi, compliance status, siapa yang mengaktifkan apa di project mana. Ini mengubah `pandawa skill`/`pandawa governance` dari CLI-only jadi punya dashboard.
3. **Approval gate UI** — tahapan `/pandawa.ultimate` yang "confirmation gate antar fase" saat ini terjadi di chat; di GUI bisa jadi kanban/status pipeline yang approvable oleh non-engineer (PM approve spec, lead approve plan, dst) — ini yang bikin People-Process makin nyambung.
4. **Usage/analytics dashboard** — dari data Fase 0, tampilkan ke tim: skill apa paling dipakai, project mana sering fail governance check, dsb.

**Non-goal GUI**: jangan bikin editor kode di GUI (bukan pesaing VS Code). GUI = *governance & visibility layer*, coding tetap terjadi di assistant/IDE.

### Fase 3 — Marketplace Agentic AI (5–9 bulan)

Setelah katalog koneksi MCP (Fase 1) dan GUI (Fase 2) ada, marketplace jadi natural extension. Yang dijual bukan "assistant baru", tapi **paket delivery**: skill + governance + rekomendasi MCP server, siap pakai untuk domain tertentu (mis. "TM Forum ODA delivery pack").

- [ ] **Marketplace = katalog package** (skill/governance/MCP-connection-set) yang bisa di-*publish* pihak ketiga (internal tim lain, atau nanti publik), dengan metadata: assistant yang didukung (Claude/Gemini/Copilot/dst — sudah dibuktikan bisa lintas-agent di baseline), MCP server yang direkomendasikan, dependency, tingkat trust/governance.
- [ ] **Trust & governance layer di marketplace**: setiap package yang dipublish harus lolos "constitution check" otomatis (linting kualitas, keamanan dasar — cek pola dari `/pandawa.test`, termasuk validasi MCP server yang direkomendasikan tidak mengekspos scope berlebihan) sebelum listed sebagai "verified".
- [ ] **Compatibility matrix**: package menyatakan assistant & MCP client yang didukung → marketplace bisa filter otomatis sesuai tooling user (PANDAWA sudah punya data ini dari `AGENT_CONFIG`, tinggal diekspos ke marketplace metadata).
- [ ] **Monetisasi/akses (opsional, tahap lanjut)**: kalau ke arah lintas-organisasi, perlu model akses (private org catalog vs public), bukan cuma GitLab token seperti sekarang.
- [ ] Integrasi dengan GUI Fase 2: marketplace browser jadi tempat orang menemukan & install, bukan command line `pandawa skill add`.

### Fase 4 — Multi-Agent Orchestration Native (9–12 bulan)

- [ ] PANDAWA sebagai orchestrator yang bisa menjalankan beberapa agent (bukan cuma Claude Code) secara paralel/berurutan sesuai spec — mirip pola "Neuron Code Orchestrator" yang sudah ada tapi digeneralisasi lintas-assistant.
- [ ] Feedback loop otomatis: hasil validasi (`/pandawa.test`, governance check) menjadi input untuk re-plan otomatis (bukan cuma laporan pasif).

---

## 4. Bagaimana PANDAWA Efektif secara People – Process – Tech

### People

- **Kurangi beban terminal untuk non-engineer** → GUI (Fase 2) adalah jawaban langsung.
- **Buat governance jadi bantuan, bukan birokrasi** — constitution harus terasa seperti "linter otomatis", bukan approval manual berlapis. Kalau checking-nya lambat/berat, orang akan bypass.
- **Onboarding**: `PANDUAN.md` sudah bagus untuk pemula, tapi perlu versi "cheat sheet 1 halaman" + video pendek — banyak adopsi tool internal gagal bukan karena fitur kurang, tapi friksi onboarding.

### Process

- **Spec-Driven harus dapat diaudit**: setiap fase (specify/plan/tasks/implement/validate) harus punya artifact yang bisa direview terpisah dari kode — ini yang membedakan PANDAWA dari "vibe coding" biasa. Perkuat ini, jangan biarkan `/pandawa.ultimate` jadi black box satu tombol tanpa jejak per-fase yang mudah ditelusuri.
- **Governance = gate, bukan saran**: pastikan CI benar-benar block kalau constitution dilanggar (lihat Fase 0), bukan sekadar warning.
- **Definisikan "Definition of Done" untuk tiap command** (`/pandawa.specify` selesai kalau apa? `/pandawa.plan` selesai kalau apa?) supaya proses konsisten lintas tim, tidak tergantung gaya prompting individu.

### Tech

- **Manfaatkan portabilitas lintas-agent yang sudah ada** — jangan dibongkar, justru dijadikan selling point: satu spec/skill PANDAWA jalan di Claude/Gemini/Copilot/Cursor/dst. Ini modal yang kompetitor single-assistant tidak punya.
- **Tambahkan MCP sebagai lapisan koneksi keluar** (Fase 1) — supaya spec/plan yang dihasilkan akurat terhadap sistem nyata (Jira, DB, API catalog), dan governance bisa mengatur MCP mana yang boleh/wajib dipakai per domain.
- **Modularisasi skill/governance sebagai package dengan versi semver**, termasuk metadata assistant & MCP server yang direkomendasikan — supaya breaking change di satu skill tidak merusak project lain yang sudah pakai versi lama.
- **Observability**: tanpa data pemakaian (Fase 0), semua keputusan roadmap ke depan berbasis asumsi, bukan bukti.

---

## 5. Rekomendasi Prioritas (kalau resource terbatas)

Kalau harus pilih **satu** hal untuk dikerjakan lebih dulu dari dua ide besar kamu (GUI vs marketplace agentic):

**Dahulukan katalog koneksi MCP (Fase 1) sebelum GUI atau marketplace — bukan karena PANDAWA perlu jadi portable (sudah), tapi karena marketplace dan GUI baru punya "isi" yang kuat kalau ada lapisan koneksi tools eksternal yang bisa dikemas dan di-govern.**

Alasan: kalau langsung loncat ke GUI atau marketplace sekarang, yang dijual/ditampilkan cuma skill & governance yang sudah ada — bagus, tapi belum banyak nilai tambah baru. Dengan MCP connection layer lebih dulu, marketplace punya produk yang lebih kaya ("paket delivery" = skill + governance + koneksi tools siap pakai), dan GUI punya sesuatu yang lebih substantif untuk ditampilkan (status koneksi MCP per project, bukan cuma daftar plugin). Urutan yang efisien:

**Fase 0 (harden) → Fase 1 (MCP connection layer) → Fase 2 (GUI, sekaligus jadi "dogfooding" awal marketplace browser) → Fase 3 (marketplace penuh).**

GUI versi awal (Fase 2) bisa langsung dirancang *sebagai antarmuka marketplace* juga — jadi tidak ada kerja dua kali antara "PANDAWA GUI" dan "marketplace GUI"; keduanya satu produk yang berkembang bertahap.
