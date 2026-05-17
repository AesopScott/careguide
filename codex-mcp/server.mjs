#!/usr/bin/env node
import { Server } from "@modelcontextprotocol/sdk/server/index.js";
import { StdioServerTransport } from "@modelcontextprotocol/sdk/server/stdio.js";
import {
  CallToolRequestSchema,
  ListToolsRequestSchema,
} from "@modelcontextprotocol/sdk/types.js";
import { spawn } from "node:child_process";
import fs from "node:fs";
import path from "node:path";
import os from "node:os";

// ---------------------------------------------------------------------------
// Companion script resolution
// Finds the latest installed version automatically; override with
// CODEX_COMPANION_PATH env var if needed.
// ---------------------------------------------------------------------------
function findCompanionScript() {
  if (process.env.CODEX_COMPANION_PATH) {
    return process.env.CODEX_COMPANION_PATH;
  }
  const pluginBase = path.join(
    os.homedir(),
    ".claude", "plugins", "cache", "openai-codex", "codex"
  );
  if (!fs.existsSync(pluginBase)) {
    throw new Error(
      `Codex plugin not found at ${pluginBase}. ` +
      `Install it with /plugin install codex@openai-codex, ` +
      `or set CODEX_COMPANION_PATH to the full path of codex-companion.mjs.`
    );
  }
  const versions = fs.readdirSync(pluginBase).sort().reverse();
  if (!versions.length) {
    throw new Error(`No Codex versions found in ${pluginBase}.`);
  }
  const script = path.join(pluginBase, versions[0], "scripts", "codex-companion.mjs");
  if (!fs.existsSync(script)) {
    throw new Error(`Codex companion script not found at ${script}.`);
  }
  return script;
}

const COMPANION_SCRIPT = findCompanionScript();

// ---------------------------------------------------------------------------
// Runner
// ---------------------------------------------------------------------------
function runCompanion(args, cwd) {
  return new Promise((resolve, reject) => {
    const child = spawn(process.execPath, [COMPANION_SCRIPT, ...args], {
      cwd: cwd || process.cwd(),
      env: process.env,
      windowsHide: true,
    });

    let stdout = "";
    let stderr = "";
    child.stdout.on("data", (d) => { stdout += d; });
    child.stderr.on("data", (d) => { stderr += d; });
    child.on("close", (code) => resolve({ stdout: stdout.trim(), stderr: stderr.trim(), exitCode: code ?? 0 }));
    child.on("error", reject);
  });
}

function formatResult({ stdout, stderr, exitCode }) {
  const parts = [];
  if (stdout) parts.push(stdout);
  if (stderr) parts.push(`[stderr] ${stderr}`);
  if (exitCode !== 0) parts.push(`[exit ${exitCode}]`);
  return parts.join("\n") || "(no output)";
}

// ---------------------------------------------------------------------------
// MCP server
// ---------------------------------------------------------------------------
const server = new Server(
  { name: "codex-mcp", version: "1.0.0" },
  { capabilities: { tools: {} } }
);

server.setRequestHandler(ListToolsRequestSchema, async () => ({
  tools: [
    {
      name: "codex_setup",
      description: "Check Codex CLI setup status — auth, availability, review-gate config.",
      inputSchema: {
        type: "object",
        properties: {
          cwd: { type: "string", description: "Working directory (defaults to cwd)" },
          enable_review_gate: { type: "boolean", description: "Enable the stop-time review gate" },
          disable_review_gate: { type: "boolean", description: "Disable the stop-time review gate" },
        },
      },
    },
    {
      name: "codex_review",
      description: "Run a Codex code review on current working-tree or branch changes.",
      inputSchema: {
        type: "object",
        properties: {
          cwd: { type: "string", description: "Repository working directory" },
          scope: { type: "string", enum: ["auto", "working-tree", "branch"], description: "What to review" },
          base: { type: "string", description: "Base ref for branch-scope review" },
          model: { type: "string", description: "Model override" },
        },
      },
    },
    {
      name: "codex_adversarial_review",
      description: "Run a Codex adversarial code review with optional focus text.",
      inputSchema: {
        type: "object",
        properties: {
          cwd: { type: "string" },
          focus: { type: "string", description: "What to focus the adversarial review on" },
          scope: { type: "string", enum: ["auto", "working-tree", "branch"] },
          base: { type: "string", description: "Base ref for branch-scope review" },
          model: { type: "string" },
        },
      },
    },
    {
      name: "codex_task",
      description: "Run a Codex agentic task with a prompt. Supports background execution and resume.",
      inputSchema: {
        type: "object",
        required: ["prompt"],
        properties: {
          cwd: { type: "string" },
          prompt: { type: "string", description: "Task prompt for Codex" },
          write: { type: "boolean", description: "Allow file writes (workspace-write sandbox)" },
          background: { type: "boolean", description: "Run in background; returns job ID immediately" },
          resume_last: { type: "boolean", description: "Resume the last task thread" },
          model: { type: "string", description: "Model override" },
          effort: {
            type: "string",
            enum: ["none", "minimal", "low", "medium", "high", "xhigh"],
            description: "Reasoning effort level",
          },
        },
      },
    },
    {
      name: "codex_status",
      description: "Check status of Codex jobs. Pass job_id for a specific job, omit for all active jobs.",
      inputSchema: {
        type: "object",
        properties: {
          cwd: { type: "string" },
          job_id: { type: "string", description: "Specific job ID to check" },
          all: { type: "boolean", description: "Show all jobs, not just current session" },
          wait: { type: "boolean", description: "Wait for the job to complete before returning" },
        },
      },
    },
    {
      name: "codex_result",
      description: "Get the full result of a completed Codex job.",
      inputSchema: {
        type: "object",
        properties: {
          cwd: { type: "string" },
          job_id: { type: "string", description: "Job ID to retrieve result for" },
        },
      },
    },
    {
      name: "codex_cancel",
      description: "Cancel a running Codex job.",
      inputSchema: {
        type: "object",
        properties: {
          cwd: { type: "string" },
          job_id: { type: "string", description: "Job ID to cancel (omit to cancel latest)" },
        },
      },
    },
  ],
}));

server.setRequestHandler(CallToolRequestSchema, async (req) => {
  const { name, arguments: args = {} } = req.params;
  const cwd = args.cwd || process.cwd();

  try {
    let result;

    switch (name) {
      case "codex_setup": {
        const flags = [];
        if (args.enable_review_gate) flags.push("--enable-review-gate");
        if (args.disable_review_gate) flags.push("--disable-review-gate");
        result = await runCompanion(["setup", ...flags], cwd);
        break;
      }
      case "codex_review": {
        const flags = [];
        if (args.scope) flags.push("--scope", args.scope);
        if (args.base) flags.push("--base", args.base);
        if (args.model) flags.push("--model", args.model);
        result = await runCompanion(["review", ...flags], cwd);
        break;
      }
      case "codex_adversarial_review": {
        const flags = [];
        if (args.scope) flags.push("--scope", args.scope);
        if (args.base) flags.push("--base", args.base);
        if (args.model) flags.push("--model", args.model);
        const positionals = args.focus ? [args.focus] : [];
        result = await runCompanion(["adversarial-review", ...flags, ...positionals], cwd);
        break;
      }
      case "codex_task": {
        const flags = [];
        if (args.model) flags.push("--model", args.model);
        if (args.effort) flags.push("--effort", args.effort);
        if (args.write) flags.push("--write");
        if (args.background) flags.push("--background");
        if (args.resume_last) flags.push("--resume-last");
        const positionals = args.prompt ? [args.prompt] : [];
        result = await runCompanion(["task", ...flags, ...positionals], cwd);
        break;
      }
      case "codex_status": {
        const flags = [];
        if (args.all) flags.push("--all");
        if (args.wait) flags.push("--wait");
        const positionals = args.job_id ? [args.job_id] : [];
        result = await runCompanion(["status", ...flags, ...positionals], cwd);
        break;
      }
      case "codex_result": {
        const positionals = args.job_id ? [args.job_id] : [];
        result = await runCompanion(["result", ...positionals], cwd);
        break;
      }
      case "codex_cancel": {
        const positionals = args.job_id ? [args.job_id] : [];
        result = await runCompanion(["cancel", ...positionals], cwd);
        break;
      }
      default:
        throw new Error(`Unknown tool: ${name}`);
    }

    return {
      content: [{ type: "text", text: formatResult(result) }],
      isError: result.exitCode !== 0,
    };
  } catch (err) {
    return {
      content: [{ type: "text", text: `Error: ${err.message}` }],
      isError: true,
    };
  }
});

const transport = new StdioServerTransport();
await server.connect(transport);
