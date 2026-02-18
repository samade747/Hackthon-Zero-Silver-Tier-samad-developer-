#!/usr/bin/env node
/**
 * browser_mcp/index.js — Silver Tier Browser / Payment MCP Server
 *
 * Exposes three tools to Claude via Playwright:
 *   navigate_and_screenshot  — Open a URL, return a screenshot for review (no approval needed)
 *   fill_payment_form        — Fill form fields. STOPS before submitting. REQUIRES /Approved/ file.
 *   click_element            — Click a CSS-selected element. REQUIRES /Approved/ file.
 *
 * SAFETY RULES (hard-coded, cannot be overridden by Claude):
 *   1. fill_payment_form NEVER auto-submits — always returns before clicking submit.
 *   2. All write actions (fill, click) require an /Approved/ file.
 *   3. DRY_RUN=true logs intent without launching a browser.
 *
 * Environment variables:
 *   DRY_RUN  — "true" to log without acting (default: true)
 */

import { Server } from '@modelcontextprotocol/sdk/server/index.js';
import { StdioServerTransport } from '@modelcontextprotocol/sdk/server/stdio.js';
import {
  CallToolRequestSchema,
  ListToolsRequestSchema,
} from '@modelcontextprotocol/sdk/types.js';
import { chromium } from 'playwright';
import fs from 'fs';
import path from 'path';

// ── Config ────────────────────────────────────────────────────────────────

const DRY_RUN = process.env.DRY_RUN !== 'false';

// ── Security: approval file check ────────────────────────────────────────

function isApproved(approvalFilePath) {
  if (!approvalFilePath) return false;
  const abs = path.resolve(approvalFilePath);
  const normalised = abs.replace(/\\/g, '/');
  return normalised.includes('/Approved/') && fs.existsSync(abs);
}

// ── MCP Server ────────────────────────────────────────────────────────────

const server = new Server(
  { name: 'browser-mcp', version: '1.0.0' },
  { capabilities: { tools: {} } }
);

server.setRequestHandler(ListToolsRequestSchema, async () => ({
  tools: [
    {
      name: 'navigate_and_screenshot',
      description:
        'Navigate to a URL and return a base64 screenshot for human review. No approval needed.',
      inputSchema: {
        type: 'object',
        properties: {
          url: { type: 'string', description: 'The URL to navigate to' },
          wait_ms: {
            type: 'number',
            description: 'Milliseconds to wait after page load (default: 2000)',
          },
        },
        required: ['url'],
      },
    },
    {
      name: 'fill_payment_form',
      description:
        'Fill form fields on a page. STOPS BEFORE SUBMITTING — manual confirmation required. Needs /Approved/ file.',
      inputSchema: {
        type: 'object',
        properties: {
          url: { type: 'string', description: 'URL of the form page' },
          field_values: {
            type: 'object',
            description: 'Map of CSS selector → value to fill',
            additionalProperties: { type: 'string' },
          },
          submit_selector: {
            type: 'string',
            description: 'CSS selector of the submit button (will NOT be clicked)',
          },
          approval_file: {
            type: 'string',
            description: 'Absolute path to approval file inside /Approved/',
          },
        },
        required: ['url', 'field_values', 'approval_file'],
      },
    },
    {
      name: 'click_element',
      description:
        'Click a CSS-selected element on a page. Requires /Approved/ file.',
      inputSchema: {
        type: 'object',
        properties: {
          url: { type: 'string', description: 'URL of the page' },
          selector: { type: 'string', description: 'CSS selector of element to click' },
          approval_file: {
            type: 'string',
            description: 'Absolute path to approval file inside /Approved/',
          },
        },
        required: ['url', 'selector', 'approval_file'],
      },
    },
  ],
}));

server.setRequestHandler(CallToolRequestSchema, async (req) => {
  const { name, arguments: args } = req.params;

  // ── navigate_and_screenshot ─────────────────────────────────────────────
  if (name === 'navigate_and_screenshot') {
    if (DRY_RUN) {
      return {
        content: [
          {
            type: 'text',
            text: `[DRY RUN] Would navigate to: ${args.url}. Set DRY_RUN=false to enable.`,
          },
        ],
      };
    }

    let browser;
    try {
      browser = await chromium.launch({ headless: true, args: ['--no-sandbox'] });
      const page = await browser.newPage();
      await page.goto(args.url, { waitUntil: 'networkidle', timeout: 30_000 });
      await page.waitForTimeout(args.wait_ms ?? 2_000);
      const screenshot = await page.screenshot({ fullPage: false });
      const b64 = screenshot.toString('base64');
      return {
        content: [
          {
            type: 'text',
            text: `✅ Screenshot taken of ${args.url}\nbase64 PNG (${b64.length} chars):\ndata:image/png;base64,${b64}`,
          },
        ],
      };
    } catch (err) {
      return { content: [{ type: 'text', text: `ERROR: ${err.message}` }] };
    } finally {
      await browser?.close();
    }
  }

  // ── fill_payment_form ───────────────────────────────────────────────────
  if (name === 'fill_payment_form') {
    // Security gate
    if (!isApproved(args.approval_file)) {
      return {
        content: [
          {
            type: 'text',
            text: 'ERROR: approval_file must exist inside the /Approved/ folder.',
          },
        ],
      };
    }

    if (DRY_RUN) {
      const fields = Object.entries(args.field_values)
        .map(([sel, val]) => `  ${sel} = "${val}"`)
        .join('\n');
      return {
        content: [
          {
            type: 'text',
            text: `[DRY RUN] Would fill form at ${args.url}:\n${fields}\nSubmit selector: ${args.submit_selector ?? 'not specified'}\nAuto-submit is DISABLED for safety.`,
          },
        ],
      };
    }

    let browser;
    try {
      browser = await chromium.launch({ headless: true, args: ['--no-sandbox'] });
      const page = await browser.newPage();
      await page.goto(args.url, { waitUntil: 'networkidle', timeout: 30_000 });

      // Fill each field
      const filled = [];
      for (const [selector, value] of Object.entries(args.field_values)) {
        try {
          await page.fill(selector, String(value));
          filled.push(selector);
        } catch (e) {
          filled.push(`${selector} (FAILED: ${e.message})`);
        }
      }

      // Take screenshot of filled form
      const screenshot = await page.screenshot({ fullPage: false });
      const b64 = screenshot.toString('base64');

      // ⚠️ HARD STOP — never auto-submit
      return {
        content: [
          {
            type: 'text',
            text: [
              `✅ Form filled at ${args.url}`,
              `Fields set: ${filled.join(', ')}`,
              `Submit button: ${args.submit_selector ?? 'not specified'}`,
              '',
              '⚠️  AUTO-SUBMIT IS DISABLED FOR SAFETY.',
              'To submit, click the submit button manually in the browser.',
              '',
              `Screenshot (base64): data:image/png;base64,${b64}`,
            ].join('\n'),
          },
        ],
      };
    } catch (err) {
      return { content: [{ type: 'text', text: `ERROR: ${err.message}` }] };
    } finally {
      await browser?.close();
    }
  }

  // ── click_element ───────────────────────────────────────────────────────
  if (name === 'click_element') {
    if (!isApproved(args.approval_file)) {
      return {
        content: [
          {
            type: 'text',
            text: 'ERROR: approval_file must exist inside the /Approved/ folder.',
          },
        ],
      };
    }

    if (DRY_RUN) {
      return {
        content: [
          {
            type: 'text',
            text: `[DRY RUN] Would click "${args.selector}" on ${args.url}. Set DRY_RUN=false to enable.`,
          },
        ],
      };
    }

    let browser;
    try {
      browser = await chromium.launch({ headless: true, args: ['--no-sandbox'] });
      const page = await browser.newPage();
      await page.goto(args.url, { waitUntil: 'networkidle', timeout: 30_000 });
      await page.click(args.selector);
      await page.waitForTimeout(1_000);
      const screenshot = await page.screenshot({ fullPage: false });
      const b64 = screenshot.toString('base64');
      return {
        content: [
          {
            type: 'text',
            text: `✅ Clicked "${args.selector}" on ${args.url}\nScreenshot: data:image/png;base64,${b64}`,
          },
        ],
      };
    } catch (err) {
      return { content: [{ type: 'text', text: `ERROR: ${err.message}` }] };
    } finally {
      await browser?.close();
    }
  }

  return {
    content: [{ type: 'text', text: `Unknown tool: ${name}` }],
  };
});

// ── Start ─────────────────────────────────────────────────────────────────

await server.connect(new StdioServerTransport());
