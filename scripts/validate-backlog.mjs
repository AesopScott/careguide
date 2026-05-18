#!/usr/bin/env node
import { readFileSync } from 'node:fs';

const path = 'docs/backlog.json';
const data = JSON.parse(readFileSync(path, 'utf8'));
const tasks = data.tasks ?? [];

const required = ['number', 'title', 'category', 'priority', 'status', 'dependencies', 'description'];
const validStatus = new Set(['backlog', 'ready', 'in-progress', 'in-review', 'complete']);

const errors = [];
const seen = new Set();

for (const t of tasks) {
  for (const k of required) {
    if (!(k in t)) errors.push(`task ${JSON.stringify(t).slice(0, 80)}... missing field "${k}"`);
  }
  if (seen.has(t.number)) errors.push(`duplicate task number ${t.number}`);
  seen.add(t.number);
  if (t.status && !validStatus.has(t.status)) {
    errors.push(`task #${t.number} has invalid status "${t.status}" (expected one of: ${[...validStatus].join(', ')})`);
  }
  if (!Array.isArray(t.dependencies)) errors.push(`task #${t.number} dependencies must be an array`);
}

for (const t of tasks) {
  for (const dep of t.dependencies ?? []) {
    if (!seen.has(dep)) errors.push(`task #${t.number} references missing dep #${dep}`);
  }
}

if (errors.length) {
  for (const e of errors) console.error(`::error::${e}`);
  process.exit(1);
}

console.log(`Backlog OK: ${tasks.length} tasks validated.`);
