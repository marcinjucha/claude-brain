# Konteksty (mapa mózgu)

Second brain obsługuje cztery konteksty. Każdy ma własny tracker zadań, własne miejsce
w Notion i (czasem) powiązane repo. Notatki robocze linkują do zadań przez frontmatter
`tracker` + `task_id` (patrz `connectors/`).

## 1. Personal
- **Tracker:** Notion — Private Tasks Table `collection://29084f14-76e0-80be-ac06-000b9ee2fc4f`
- **Repo:** brak
- **Vault:** `01-Projects` (osobiste) / `02-Areas`
- Drobne errandy zostają w Notion (bez notatek roboczych).

## 2. Praca — Scandit
- **Tracker:** JIRA — projekt **SHELF** (`scandit.atlassian.net`, cloudId `a19c74f3-95cf-4d55-9d33-366adfe6f7a0`)
- **Repo:** `~/Scandit/digital-shelf-ios/`
- **Vault:** `01-Projects/work/SHELF-<nr>-<slug>.md`
- Connector: `connectors/jira/`.
- **Autorytet JIRA/Confluence/Sprint:** skill `~/Scandit/digital-shelf-ios/.claude/skills/project-management/SKILL.md`
  (agent `atlassian-manager`) — reguły: Markdown-not-ADF, cloudId, komponenty iOS/SHELFVIEW-APP,
  sprint przez CQL, tech debt → Confluence parent `7171866823`.

## 3. Shadow Operator (własny venture)
Pomoc kreatorom YouTube/IG w monetyzacji przez produkty cyfrowe. Ja robię back-end
marketingu, kreatorzy tworzą produkty. Dla każdego kreatora: **Intel Audit** + **skrypty**.
Notion służy też do udostępniania materiałów kreatorom.
- **Notion:** Shadow Operator `https://app.notion.com/p/1d984f1476e0821eaa98817a218ff9b3`
  - **Prospecting Tracker** `collection://9cd84f14-76e0-823a-9146-876ae3400d3c` (statusy outreach, kreatorzy)
  - Bootcamp OS: Finding/Vetting → Outreach → Pilot Launch → Roadmap; szablony follow-up (EN/PL)
- **Repo:** `~/Prywatne/projects/claude-marketing/` — silnik (skille):
  `mkr-youtube-creator-prospecting`, `mkr-instagram-creator-prospecting`,
  `mkr-outreach-creator-messaging`, `mkr-creator-loom-script`,
  `mkr-creator-monetisation-audit`, `mrk-offer`, `ag-knowledge`
- **Vault (propozycja):** `01-Projects/shadow-operator/<kreator>/` (Intel Audit, skrypty)

## 4. HaloEfekt (agencja ze znajomymi)
- **Notion:** Agency Dashboard `https://app.notion.com/p/29084f1476e080d1bbb7f111d659e9ca`
  - **Agency Tasks Table** `collection://29284f14-76e0-8062-a18d-000bfce0cf23` (tracker zadań)
  - Agency Projects, Agency Clients, Marketing Docs, Klienci Docs
  - **Social Media** `https://app.notion.com/p/36784f1476e080169aa4d3ca99abbb54` ← **obecnie najwięcej czasu**
    (tutoriale Google Workspace short-form; wskazówki nagraniowe; Resources
    `collection://36784f14-76e0-805b-95cb-000be4f783bc`)
- **Repos:** `~/Prywatne/projects/legal-mind/` (AI Agency), `~/Prywatne/projects/doc-forge/` (DocForge, Notion AAA-P-6)
- **Vault (propozycja):** `01-Projects/agency/{social-media,legal-mind,doc-forge}/`

> Korekta vs globalny CLAUDE.md: HaloEfekt/legal-mind jedzie na **Notion Agency Database**
> (`collection://29284f14-76e0-8062-a18d-000bfce0cf23`), nie ClickUp — ClickUp nie istnieje.
