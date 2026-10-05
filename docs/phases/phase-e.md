# Phase E — Open-source adoption

## Need

A useful local service still fails as an open-source project if a new developer
cannot install it, understand it, verify it, or contribute safely.

## Plan

- Choose and publish an Apache-2.0 or MIT license.
- Add a contributor guide and code-of-conduct expectations.
- Maintain a good-first-issue backlog.
- Keep the Docker quickstart under ten minutes.
- Publish API, integration, security, and migration documentation.
- Record architecture decisions and compatibility guarantees.
- Define upgrade and migration policy.

## Status

Planned. README, Docker setup, API docs, integration guides, security notes,
and regression commands are already available as the foundation.

## Acceptance

A new developer can install Attic, ingest a file, query memory, run the
regression suite, understand the architecture, and submit a focused change
without maintainer help.

## First delivery checklist

- [ ] Select license and add `LICENSE`.
- [ ] Add `CONTRIBUTING.md` and issue templates.
- [ ] Add architecture decision records.
- [ ] Document supported API compatibility window.
- [ ] Add CI for regression and Docker build.
