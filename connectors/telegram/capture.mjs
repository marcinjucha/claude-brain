#!/usr/bin/env node
// Telegram capture → zapisuje wiadomości jako notatki w 00-Inbox vaultu.
// Zero zależności (Node 18+: wbudowany fetch). Long-polling getUpdates.
//
// Konfiguracja:
//   ENV  TELEGRAM_BOT_TOKEN       (wymagane)  token od @BotFather
//   ENV  TELEGRAM_ALLOWED_CHATS   (zalecane)  CSV id czatów, które mogą pisać; puste = każdy
//   config.json → vault.path + vault.inbox  (ścieżka docelowa)
//
// Uruchomienie:  node connectors/telegram/capture.mjs

import { readFile, writeFile, mkdir } from 'node:fs/promises';
import { existsSync, readFileSync } from 'node:fs';
import { join, dirname } from 'node:path';
import { fileURLToPath } from 'node:url';

const ROOT = join(dirname(fileURLToPath(import.meta.url)), '..', '..');
const STATE_FILE = join(dirname(fileURLToPath(import.meta.url)), '.state.json');

const TOKEN = process.env.TELEGRAM_BOT_TOKEN;
if (!TOKEN) {
  console.error('Brak TELEGRAM_BOT_TOKEN. Ustaw env (patrz connectors/telegram/README.md).');
  process.exit(1);
}
const ALLOWED = (process.env.TELEGRAM_ALLOWED_CHATS || '')
  .split(',').map((s) => s.trim()).filter(Boolean);

const cfg = JSON.parse(readFileSync(join(ROOT, 'config.json'), 'utf8'));
const INBOX = join(cfg.vault.path, cfg.vault.inbox);
const API = `https://api.telegram.org/bot${TOKEN}`;

function loadOffset() {
  if (!existsSync(STATE_FILE)) return 0;
  try { return JSON.parse(readFileSync(STATE_FILE, 'utf8')).offset || 0; }
  catch { return 0; }
}
async function saveOffset(offset) {
  await writeFile(STATE_FILE, JSON.stringify({ offset }), 'utf8');
}

async function tg(method, body) {
  const res = await fetch(`${API}/${method}`, {
    method: 'POST',
    headers: { 'content-type': 'application/json' },
    body: JSON.stringify(body),
  });
  const json = await res.json();
  if (!json.ok) throw new Error(`${method}: ${json.description}`);
  return json.result;
}

function slug(text) {
  return (text || 'note').toLowerCase()
    .replace(/[^\p{L}\p{N}]+/gu, '-').replace(/^-+|-+$/g, '').slice(0, 50) || 'note';
}

function pad(n) { return String(n).padStart(2, '0'); }

async function saveNote(msg) {
  const text = msg.text || msg.caption || '';
  const d = new Date(msg.date * 1000);
  const stamp = `${d.getFullYear()}-${pad(d.getMonth() + 1)}-${pad(d.getDate())}-${pad(d.getHours())}${pad(d.getMinutes())}`;
  const file = join(INBOX, `${stamp}-${slug(text)}.md`);
  const from = [msg.from?.first_name, msg.from?.last_name].filter(Boolean).join(' ') || 'unknown';
  const attach = msg.photo ? 'photo' : msg.document ? 'document' : msg.voice ? 'voice' : null;

  const frontmatter = [
    '---',
    'source: telegram',
    `captured: ${d.toISOString()}`,
    `from: "${from}"`,
    `chat_id: ${msg.chat.id}`,
    `message_id: ${msg.message_id}`,
    attach ? `attachment: ${attach}` : null,
    'status: inbox',
    'tags: [inbox, telegram]',
    '---',
  ].filter((l) => l !== null).join('\n');

  const body = text || (attach ? `_(${attach} — nieobsłużony załącznik, dograj ręcznie)_` : '_(pusta wiadomość)_');
  await mkdir(INBOX, { recursive: true });
  await writeFile(file, `${frontmatter}\n\n${body}\n`, 'utf8');
  return file;
}

async function loop() {
  let offset = loadOffset();
  console.log(`Telegram capture aktywny. Inbox: ${INBOX}`);
  console.log(ALLOWED.length ? `Allowlist czatów: ${ALLOWED.join(', ')}` : 'UWAGA: brak allowlisty — każdy może pisać do bota.');

  for (;;) {
    try {
      const updates = await tg('getUpdates', { offset, timeout: 30, allowed_updates: ['message'] });
      for (const u of updates) {
        offset = u.update_id + 1;
        const msg = u.message;
        if (!msg) continue;
        if (ALLOWED.length && !ALLOWED.includes(String(msg.chat.id))) {
          console.log(`Pominięto wiadomość z niedozwolonego czatu ${msg.chat.id}`);
          continue;
        }
        if ((msg.text || '').startsWith('/')) {
          console.log(`Pominięto komendę: ${msg.text}`);
          continue;
        }
        const file = await saveNote(msg);
        console.log(`Zapisano: ${file}`);
        await tg('sendMessage', { chat_id: msg.chat.id, text: `✅ Zapisane do Inbox: ${file.split('/').pop()}` }).catch(() => {});
      }
      await saveOffset(offset);
    } catch (err) {
      console.error(`Błąd: ${err.message}. Ponawiam za 5s...`);
      await new Promise((r) => setTimeout(r, 5000));
    }
  }
}

loop();
