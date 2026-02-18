/**
 * ecosystem.config.js — Silver Tier PM2 Process Manager Config
 *
 * Manages 6 processes:
 *   1. orchestrator      — Main brain loop (polls Needs_Action)
 *   2. gmail-watcher     — Gmail IMAP monitor (every 2 min)
 *   3. wa-watcher        — WhatsApp Web via Playwright (every 30 sec)
 *   4. fs-watcher        — Drop folder watchdog
 *   5. approval-watcher  — Approved/ folder watchdog → MCP trigger
 *   6. scheduler         — Daily + weekly Claude briefings
 *
 * Usage:
 *   pm2 start ecosystem.config.js
 *   pm2 save
 *   pm2 startup   ← follow the printed command
 *   pm2 status
 */

module.exports = {
  apps: [
    {
      name: 'orchestrator',
      script: 'scripts/orchestrator.py',
      interpreter: 'python',
      watch: false,
      restart_delay: 5000,
      max_restarts: 10,
      env: {
        VAULT_PATH: process.env.VAULT_PATH || '.',
      },
      log_date_format: 'YYYY-MM-DD HH:mm:ss',
    },
    {
      name: 'gmail-watcher',
      script: 'watchers/gmail_watcher.py',
      interpreter: 'python',
      watch: false,
      restart_delay: 10000,
      max_restarts: 10,
      env: {
        VAULT_PATH: process.env.VAULT_PATH || '.',
      },
      log_date_format: 'YYYY-MM-DD HH:mm:ss',
    },
    {
      name: 'wa-watcher',
      script: 'watchers/whatsapp_watcher.py',
      interpreter: 'python',
      watch: false,
      restart_delay: 15000,
      max_restarts: 10,
      env: {
        VAULT_PATH: process.env.VAULT_PATH || '.',
      },
      log_date_format: 'YYYY-MM-DD HH:mm:ss',
    },
    {
      name: 'fs-watcher',
      script: 'watchers/filesystem_watcher.py',
      interpreter: 'python',
      watch: false,
      restart_delay: 5000,
      max_restarts: 10,
      env: {
        VAULT_PATH: process.env.VAULT_PATH || '.',
      },
      log_date_format: 'YYYY-MM-DD HH:mm:ss',
    },
    {
      name: 'approval-watcher',
      script: 'watchers/approval_watcher.py',
      interpreter: 'python',
      watch: false,
      restart_delay: 5000,
      max_restarts: 10,
      env: {
        VAULT_PATH: process.env.VAULT_PATH || '.',
      },
      log_date_format: 'YYYY-MM-DD HH:mm:ss',
    },
    {
      name: 'scheduler',
      script: 'scheduler.py',
      interpreter: 'python',
      watch: false,
      restart_delay: 5000,
      max_restarts: 10,
      env: {
        VAULT_PATH: process.env.VAULT_PATH || '.',
      },
      log_date_format: 'YYYY-MM-DD HH:mm:ss',
    },
  ],
};
