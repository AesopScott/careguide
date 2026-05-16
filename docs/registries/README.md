# Registries

Living documents that enumerate every named contract crossing a boundary in CareGuide.

A **boundary** is anywhere two pieces of code, config, or infrastructure refer to the same name independently and can disagree about it. For each name, we list every place that produces it and every place that consumes it. Mismatches are bugs.

## Files

- [collections.md](collections.md) — every Firestore collection: writers, readers, rule status, index status.
- [claims.md](claims.md) — every Firebase custom claim: who sets it, who checks it.
- [endpoints.md](endpoints.md) — every API endpoint: server, callers, request/response shape.

## Maintenance rules

1. **Every PR that touches a collection, claim, or endpoint updates the registry in the same commit.** If the PR introduces a new name, add a row. If it removes one, remove the row. If it changes the shape, update the shape.
2. **Every architecture-phase output ends by populating these files** before build begins. Cross-model review runs against the registries, not against prose.
3. **The review rubric is one question:** every name has matching producers and consumers, with matching shapes. Flag everything that doesn't.
4. **Severity convention:** ⚠ CRITICAL = will break a happy-path flow; ⚠ orphan = producer or consumer with no counterpart; ✓ = wired.

## Why these three

These were the boundary kinds that this project's architecture turned out to have. A different project would have different ones — for a Postgres+Rails app, you'd list tables, controllers, jobs, migrations. For a Stripe SaaS, products, webhooks, customer states. Auto-detect what your project has rather than copying this file.
