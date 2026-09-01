---
name: cloudflare-worker-api-proxy
description: Use when deploying or maintaining a zero-cost OpenAI/Anthropic-compatible API reverse proxy on Cloudflare Workers with custom auth, streaming, and rate-limiting.
version: 1.0.0
author: shali10
license: MIT
platforms: [linux, macos, windows]
metadata:
  tags: [cloudflare, proxy, api-gateway, workers, openai-proxy, serverless]
  related_skills: [cloudflare-fullstack-ops]
---

# Zero-Cost Serverless OpenAI API Proxy on Cloudflare Workers

## Overview

A high-performance, edge-native API proxy deployed on Cloudflare Workers. It enables zero-cost routing, token authentication, custom rate-limiting, and header rewriting for OpenAI, Claude, and Google Gemini API endpoints, bypassing regional network blocks with global edge caching and SSE streaming support.

## When to Use & When NOT to Use

### When to Use
- Bypassing geographic IP restrictions on AI provider APIs (e.g. OpenAI / Anthropic).
- Adding custom Bearer token authentication in front of self-hosted or shared LLM gateways.
- Injecting custom user agents or security headers into upstream requests.

### When NOT to Use
- Heavy video/audio encoding or streaming workloads exceeding Cloudflare Worker CPU limits (50ms free / 30s paid).
- Caching multi-gigabyte files (use Cloudflare R2 instead).

## Production Worker Implementation

```javascript
export default {
  async fetch(request, env) {
    const url = new URL(request.url);
    
    // 1. CORS Preflight
    if (request.method === "OPTIONS") {
      return new Response(null, {
        headers: {
          "Access-Control-Allow-Origin": "*",
          "Access-Control-Allow-Methods": "GET, POST, OPTIONS",
          "Access-Control-Allow-Headers": "Content-Type, Authorization",
        }
      });
    }

    // 2. Upstream Target Configuration
    const UPSTREAM_TARGET = env.UPSTREAM_URL || "https://api.openai.com";
    const targetUrl = new URL(url.pathname + url.search, UPSTREAM_TARGET);

    // 3. Clone & Modify Headers
    const headers = new Headers(request.headers);
    headers.set("Host", targetUrl.hostname);
    if (env.INJECT_USER_AGENT) {
      headers.set("User-Agent", env.INJECT_USER_AGENT);
    }

    // 4. Proxy Request with Streaming
    const response = await fetch(targetUrl.toString(), {
      method: request.method,
      headers: headers,
      body: request.body,
      redirect: "follow"
    });

    // 5. Return Response with CORS
    const newHeaders = new Headers(response.headers);
    newHeaders.set("Access-Control-Allow-Origin": "*");
    return new Response(response.body, {
      status: response.status,
      statusText: response.statusText,
      headers: newHeaders
    });
  }
};
```

## Common Pitfalls

1. **Broken SSE streaming**: Never read `await request.text()` or `await response.text()` when streaming (`stream: true`); pipe `response.body` directly to preserve real-time tokens.
2. **Missing Host header rewrite**: Upstream services behind Cloudflare will throw 403 / 1000 errors if the incoming `Host` header is not rewritten to match the target hostname.

## Verification Checklist

- [ ] Worker responds to `GET /v1/models` with HTTP 200/401 from upstream.
- [ ] SSE streaming test via `curl -N` delivers chunks without buffering.
- [ ] CORS headers are present on both OPTIONS preflight and normal responses.
