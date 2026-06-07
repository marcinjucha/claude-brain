# Architektura second brain

## Dwa repozytoria, dwie role

| Warstwa | Lokalizacja | Rola | Wersjonowanie |
|---------|-------------|------|---------------|
| **Treść** | Obsidian vault `.../Documents/AI` | notatki, wiedza, zadania-jako-pliki | iCloud sync |
| **Hydraulika** | `claude-brain` (to repo) | connectory, MCP, n8n, skrypty | git |

Rozdział jest celowy: treść ma być przenośna i niezależna (zwykły markdown), a hydraulika
ma być wersjonowalna, odtwarzalna i wymienna bez dotykania notatek.

## Podział ról: Notion vs Obsidian (NIE sync, tylko własność danych)

To nie jest dwustronna synchronizacja tej samej treści. Każda warstwa jest **właścicielem
innych danych**, więc nie ma konfliktów do rozwiązywania:

| | **Notion** | **Obsidian (vault)** |
|---|------------|----------------------|
| Trzyma | zadania (zarządzanie), **finalny produkt** | wiedza robocza, detal techniczny, "jak co robimy" |
| Właściciel statusu zadania | Notion | — |
| Właściciel procesu/detalu | — | vault |

Mechanizm spinający: notatka robocza w vaulcie nosi w frontmatter `notion_id` / `notion_url`
linkującym do zadania w Notion.

```
                  pull tasks                         publish final
   Notion  ──────────────────────►  Obsidian  ──────────────────────►  Notion
 (zadania)   scaffold notatki        (praca:        finalny produkt    (strona/zadanie)
             roboczej w 01-Projects   detal,
             z notion_id w froncie)   proces)
```

1. **pull** — Claude pobiera zadania z Notion (przez MCP) → zakłada/znajduje notatkę roboczą
   w `01-Projects` z `notion_id` w nagłówku.
2. **praca** — cała wiedza techniczna i proces powstają w vaulcie.
3. **publish** — gotowy efekt Claude wypycha jako finalny produkt do Notion.

## Przepływ capture (Telegram, wklejki)

```
Telegram ─────► 00-Inbox (surowe) ─────► klasyfikacja → PARA (Claude/ręcznie)
```

Wszystko surowe ląduje w `00-Inbox`; przetwarzanie (tagowanie, linkowanie, przeniesienie
do właściwego folderu PARA) jest osobnym krokiem.

## Konteksty użycia

Second brain ma działać w wielu miejscach — odzwierciedla to struktura `01-Projects`:

- `01-Projects/work/` — Scandit / Stepstone
- `01-Projects/clients/` — współpraca z klientami (per-klient podfolder)
- inne — pozostałe aktywne projekty

## Decyzje

- **Notion ↔ Obsidian** — ROZSTRZYGNIĘTE: podział ról (Notion = zadania + finał, vault = detal),
  nie dwustronny sync. Patrz sekcja wyżej.
- **Telegram: zakres** — START: tylko capture do `00-Inbox`. Później ewentualnie zapytania do mózgu (RAG).
- **n8n: gdzie hostowany** — otwarte (lokalnie vs VPS). Telegram na start bez n8n (lekki poller).

## Mapowanie do baz Notion (z globalnego CLAUDE.md)

- Praca/personal → Private Dashboard (Tasks `collection://29084f14-76e0-80be-ac06-000b9ee2fc4f`)
- Agency/legal-mind → ClickUp (NIE Notion Agency DB — zdeprecjonowana dla legal-mind)
