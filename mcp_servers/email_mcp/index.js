#!/usr/bin/env node
/**
 * email_mcp/index.js — Silver Tier Email MCP Server
 *
 * Exposes two tools to Claude:
 *   send_email   — Sends a Gmail message. REQUIRES approval_file in /Approved/.
 *   draft_email  — Creates a Gmail draft without sending (no approval needed).
 *
 * Environment variables (set in .env or mcp.json):
 *   GMAIL_CREDENTIALS_PATH  — path to gmail_credentials.json
 *   GMAIL_TOKEN_PATH        — path to gmail_token.json
 *   DRY_RUN                 — "true" to log without actually sending (default: true)
 *   MAX_EMAILS_PER_HOUR     — rate limit (default: 10)
 */

import { Server } from '@modelcontextprotocol/sdk/server/index.js';
import { StdioServerTransport } from '@modelcontextprotocol/sdk/server/stdio.js';
import {
  CallToolRequestSchema,
  ListToolsRequestSchema,
} from '@modelcontextprotocol/sdk/types.js';
import { google } from 'googleapis';
import fs from 'fs';
import path from 'path';

// ── Config ────────────────────────────────────────────────────────────────

const DRY_RUN = process.env.DRY_RUN !== 'false';
const MAX_PER_HOUR = parseInt(process.env.MAX_EMAILS_PER_HOUR || '10', 10);

// Simple in-memory rate limiter (resets on restart)
const sentTimestamps = [];

function checkRateLimit() {
  const now = Date.now();
  const oneHourAgo = now - 3_600_000;
  const recent = sentTimestamps.filter((t) => t > oneHourAgo);
  if (recent.length >= MAX_PER_HOUR) {
    return false;
  }
  sentTimestamps.push(now);
  return true;
}

// ── Gmail auth ────────────────────────────────────────────────────────────

async function getGmailClient() {
  const credsPath = process.env.GMAIL_CREDENTIALS_PATH;
  const tokenPath = process.env.GMAIL_TOKEN_PATH;

  if (!credsPath || !tokenPath) {
    throw new Error(
      'GMAIL_CREDENTIALS_PATH and GMAIL_TOKEN_PATH must be set in environment.'
    );
  }

  const creds = JSON.parse(fs.readFileSync(credsPath, 'utf8'));
  const { client_id, client_secret, redirect_uris } =
    creds.installed || creds.web;

  const auth = new google.auth.OAuth2(client_id, client_secret, redirect_uris[0]);
  auth.setCredentials(JSON.parse(fs.readFileSync(tokenPath, 'utf8')));
  return google.gmail({ version: 'v1', auth });
}

// ── Build RFC 2822 message ────────────────────────────────────────────────

function buildRawMessage({ to, subject, body, replyTo }) {
  const lines = [
    `To: ${to}`,
    `Subject: ${subject}`,
    replyTo ? `Reply-To: ${replyTo}` : '',
    'Content-Type: text/plain; charset=utf-8',
    '',
    body,
  ].filter((l) => l !== null);
  return Buffer.from(lines.join('\r\n')).toString('base64url');
}

// ── Security: approval file check ────────────────────────────────────────

function isApproved(approvalFilePath) {
  const abs = path.resolve(approvalFilePath);
  const normalised = abs.replace(/\\/g, '/');
  return normalised.includes('/Approved/') && fs.existsSync(abs);
}

// ── MCP Server ────────────────────────────────────────────────────────────

const server = new Server(
  { name: 'email-mcp', version: '1.0.0' },
  { capabilities: { tools: {} } }
);

server.setRequestHandler(ListToolsRequestSchema, async () => ({
  tools: [
    {
      name: 'send_email',
      description:
        'Send an email via Gmail. Requires a valid approval_file path inside /Approved/.',
      inputSchema: {
        type: 'object',
        properties: {
          to: { type: 'string', description: 'Recipient email address' },
          subject: { type: 'string', description: 'Email subject line' },
          body: { type: 'string', description: 'Plain-text email body' },
          approval_file: {
            type: 'string',
            description: 'Absolute path to the approval file inside /Approved/',
          },
          reply_to: {
            type: 'string',
            description: 'Optional Reply-To address',
          },
        },
        required: ['to', 'subject', 'body', 'approval_file'],
      },
    },
    {
      name: 'draft_email',
      description:
        'Create a Gmail draft without sending. No approval file required.',
      inputSchema: {
        type: 'object',
        properties: {
          to: { type: 'string', description: 'Recipient email address' },
          subject: { type: 'string', description: 'Email subject line' },
          body: { type: 'string', description: 'Plain-text email body' },
        },
        required: ['to', 'subject', 'body'],
      },
    },
  ],
}));

server.setRequestHandler(CallToolRequestSchema, async (req) => {
  const { name, arguments: args } = req.params;

  // ── send_email ──────────────────────────────────────────────────────────
  if (name === 'send_email') {
    // Security gate: must have a valid approval file in /Approved/
    if (!isApproved(args.approval_file)) {
      return {
        content: [
          {
            type: 'text',
            text: 'ERROR: approval_file must exist inside the /Approved/ folder. Move the file there first.',
          },
        ],
      };
    }

    // Rate limit
    if (!checkRateLimit()) {
      return {
        content: [
          {
            type: 'text',
            text: `ERROR: Rate limit reached (${MAX_PER_HOUR} emails/hour). Try again later.`,
          },
        ],
      };
    }

    if (DRY_RUN) {
      return {
        content: [
          {
            type: 'text',
            text: `[DRY RUN] Would send email to ${args.to} — subject: "${args.subject}". Set DRY_RUN=false to enable.`,
          },
        ],
      };
    }

    try {
      const gmail = await getGmailClient();
      const raw = buildRawMessage({
        to: args.to,
        subject: args.subject,
        body: args.body,
        replyTo: args.reply_to,
      });
      await gmail.users.messages.send({ userId: 'me', requestBody: { raw } });
      return {
        content: [{ type: 'text', text: `✅ Email sent successfully to ${args.to}` }],
      };
    } catch (err) {
      return {
        content: [{ type: 'text', text: `ERROR sending email: ${err.message}` }],
      };
    }
  }

  // ── draft_email ─────────────────────────────────────────────────────────
  if (name === 'draft_email') {
    if (DRY_RUN) {
      return {
        content: [
          {
            type: 'text',
            text: `[DRY RUN] Would create Gmail draft to ${args.to} — subject: "${args.subject}". Set DRY_RUN=false to enable.`,
          },
        ],
      };
    }

    try {
      const gmail = await getGmailClient();
      const raw = buildRawMessage({
        to: args.to,
        subject: args.subject,
        body: args.body,
      });
      await gmail.users.drafts.create({
        userId: 'me',
        requestBody: { message: { raw } },
      });
      return {
        content: [{ type: 'text', text: `✅ Gmail draft created for ${args.to}` }],
      };
    } catch (err) {
      return {
        content: [{ type: 'text', text: `ERROR creating draft: ${err.message}` }],
      };
    }
  }

  return {
    content: [{ type: 'text', text: `Unknown tool: ${name}` }],
  };
});

// ── Start ─────────────────────────────────────────────────────────────────

await server.connect(new StdioServerTransport());
