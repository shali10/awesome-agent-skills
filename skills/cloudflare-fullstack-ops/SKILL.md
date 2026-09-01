---
name: cloudflare-fullstack-ops
description: Use when deploying, configuring, or managing Cloudflare full-stack edge infrastructure including Pages, Workers, D1 SQL databases, R2 object storage, KV, and DNS routing.
version: 1.0.0
author: shali10
license: MIT
platforms: [linux, macos, windows]
metadata:
  tags: [cloudflare, serverless, workers, d1, r2, dns, edge-computing]
  related_skills: [cloudflare-worker-api-proxy]
---

# Cloudflare Full-Stack Edge Infrastructure Operations

## Overview

A complete operational guide and automation toolkit for managing Cloudflare edge resources. It covers continuous deployment on **Cloudflare Pages, serverless compute via Workers, serverless relational storage with D1, S3-compatible asset hosting on R2, low-latency KV, and programmatic DNS management**.

## When to Use & When NOT to Use

### When to Use
- Deploying frontend SPAs / SSG sites to Cloudflare Pages with zero server maintenance.
- Setting up Hono/TypeScript backend microservices on Cloudflare Workers.
- Managing D1 SQLite schemas, migrations, and full-text search (FTS5).
- Configuring R2 custom domains, CORS, and S3-compatible access tokens.
- Automating DNS records, SSL/TLS encryption modes, and WAF security rules.

### When NOT to Use
- Traditional bare-metal or long-running Stateful TCP server orchestration.
- Deploying complex containerized Kubernetes workloads (use standard Docker/K8s tools).

## Core CLI Workflows (Wrangler & API)

```bash
# 1. Cloudflare Pages Deployment
npx wrangler pages deploy ./dist --project-name my-portal

# 2. Cloudflare D1 Database Migrations
npx wrangler d1 execute my-database --command "CREATE TABLE IF NOT EXISTS posts (id INTEGER PRIMARY KEY, title TEXT);"
npx wrangler d1 execute my-database --file=./schema.sql

# 3. Cloudflare R2 Bucket Management
npx wrangler r2 bucket create my-assets-bucket
npx wrangler r2 object put my-assets-bucket/logo.png --file=./logo.png

# 4. Programmatic DNS Record Update
curl -X POST "https://api.cloudflare.com/client/v4/zones/<ZONE_ID>/dns_records" \
  -H "X-Auth-Email: <YOUR_EMAIL>" \
  -H "X-Auth-Key: <YOUR_GLOBAL_KEY>" \
  -H "Content-Type: application/json" \
  -d '{"type":"A","name":"api.example.com","content":"198.51.100.1","proxied":true}'
```

## Common Pitfalls

1. **Bearer Token vs Global Key Auth Mismatch**: Cloudflare API endpoints differ in auth requirements; if Bearer returns Code 1000, use `X-Auth-Email` + `X-Auth-Key` headers.
2. **Orange Cloud (Proxied) 522 Origin Timeout**: When Cloudflare proxy is active, the origin firewall (UFW/iptables) must whitelist Cloudflare IP ranges, or SSL mode must match (Full vs Strict).
3. **D1 Read/Write Boundaries in Workers**: Remember D1 transactions are atomic per execute call; batch multi-statement queries in a single `.batch([...])` call.

## Verification Checklist

- [ ] Pages project status is `active` and reachable over HTTPS.
- [ ] D1 queries execute with valid response data.
- [ ] R2 custom domain responds with valid CORS headers.
- [ ] DNS records propagate with correct proxy status.
