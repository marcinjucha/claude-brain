# claude-brain — infrastruktura second brain

To repo to **hydraulika**, nie treść. Treść (notatki) żyje w vaulcie Obsidiana,
którego ścieżka jest w `config.json` → `vault.path`. Zawsze czytaj tę ścieżkę stąd,
nie hardkoduj jej w skryptach.

## Co tu należy, a co nie

- **TU:** connectory (`connectors/`), konfiguracje MCP (`mcp/`), workflowy n8n (`n8n/`),
  skrypty setup/sync/maintenance (`scripts/`), dokumentacja architektury (`docs/`).
- **NIE TU:** notatki, wiedza, zadania-jako-treść — to idzie do vaultu.

## Operowanie na vaulcie

Vault to zwykłe pliki `.md` na dysku — czytaj/pisz je bezpośrednio (Read/Write/Edit).
**Nie potrzeba MCP do dostępu do vaultu** — MCP/connectory są wyłącznie dla systemów
zewnętrznych (Notion, Telegram), nie dla plików lokalnych.

Struktura vaultu (PARA): `00-Inbox`, `01-Projects/{work,clients}`, `02-Areas`,
`03-Resources`, `04-Archive`, `_system/templates`.

## Routing zadań (z globalnego CLAUDE.md użytkownika)

- legal-mind / Halo Efekt → **ClickUp** (NIE Notion Agency DB).
- Reszta (personal, Scandit/Stepstone) → **Notion Private Dashboard**.

## Status i kolejność

Patrz tabela statusu w `README.md`. Kolejność budowy: connectory → n8n → automatyzacje.
