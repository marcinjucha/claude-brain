---
description: Scaffold a social content note and draft hook + script + copy for it
argument-hint: <temat> [--platform reels|tiktok|yt]
allowed-tools: Read, Write, Edit, Bash, Grep
---

# /brain-social — nowy content + copy

Zakłada notatkę contentu w pipeline social i pisze pierwszy draft (hook, skrypt, opis).
Pipeline etapów: idea → script → record → edit → publish → done. Globalna.

Repo mózgu (config/ścieżki): `/Users/marcinjucha/Prywatne/projects/claude-brain`.
Folder docelowy: `<vault.path>/01-Projects/agency/social-media/`.

## Faza 0 — przygotuj
Wczytaj `vault.path` z `config.json`. Temat = `$ARGUMENTS` (bez flag). Slug z tematu.

## Faza 1 — utwórz notatkę
Z szablonu `_system/templates/content.md` → plik `<slug>.md`. Wypełnij `topic`, `platform`
(domyślnie reels), `stage: script` (bo od razu piszemy copy), `created`/`updated` = dziś.

## Faza 2 — napisz draft (copy)
Zastosuj wskazówki z [[nagrania-wskazowki]] (hook w 1.5s, captions, każda akcja = shot, CTA „Zapisz"):
1. **Hook** — pierwszy frame / pierwsze słowa (mocny, konkretny efekt).
2. **Skrypt / copy** — krótkie beaty pod short-form, tempo +10-15%.
3. **Plan nagrania** — shoty, zoomy, cięcia per akcja.
4. **Opis + hashtagi + CTA** — hashtagi PL z resource note.

> Dla tonu/oferty możesz sięgnąć po skille `claude-marketing` (`mrk-offer`, `mkr-creator-loom-script`)
> — ale to content HaloEfekt (tutoriale Google Workspace), nie outreach do kreatorów.

## Faza 3 — raport
Ścieżka notatki + przypomnienie: przesuwaj `stage` w miarę postępu; tablica [[_social-board]]
pokazuje pipeline. Jeśli content mapuje się na zadanie w Notion (projekt AAA-P-10) — po skończeniu
`/brain-publish`.
