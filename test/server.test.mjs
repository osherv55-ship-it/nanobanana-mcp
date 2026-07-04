// Integration smoke test: boots the real server on a random port with dummy
// keys and exercises everything that doesn't require a live Gemini call.
// Run with: npm test

import { test, before, after } from "node:test";
import assert from "node:assert/strict";
import { spawn } from "node:child_process";

const PORT = 8100 + Math.floor(Math.random() * 400);
const BASE = `http://127.0.0.1:${PORT}`;
const TOKEN = "test-token-123";

let server;

before(async () => {
  server = spawn("node", ["server.js"], {
    env: {
      ...process.env,
      PORT: String(PORT),
      GEMINI_API_KEY: "dummy-key-for-tests",
      MCP_AUTH_TOKEN: TOKEN,
    },
    stdio: ["ignore", "pipe", "pipe"],
  });

  // Wait for the health endpoint to come up.
  const deadline = Date.now() + 10_000;
  while (true) {
    try {
      const res = await fetch(`${BASE}/`);
      if (res.ok) break;
    } catch {
      if (Date.now() > deadline) throw new Error("server did not start within 10s");
      await new Promise((r) => setTimeout(r, 100));
    }
  }
});

after(() => {
  server?.kill();
});

function mcpRequest(body, { token = TOKEN } = {}) {
  return fetch(`${BASE}/mcp`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
      Accept: "application/json, text/event-stream",
      ...(token ? { Authorization: `Bearer ${token}` } : {}),
    },
    body: JSON.stringify(body),
  });
}

const TOOLS_LIST = { jsonrpc: "2.0", id: 1, method: "tools/list", params: {} };

test("health endpoint reports ok", async () => {
  const res = await fetch(`${BASE}/`);
  assert.equal(res.status, 200);
  const body = await res.json();
  assert.equal(body.status, "ok");
  assert.equal(body.server, "nanobanana-mcp");
});

test("MCP endpoint rejects missing token", async () => {
  const res = await mcpRequest(TOOLS_LIST, { token: null });
  assert.equal(res.status, 401);
});

test("MCP endpoint rejects wrong token", async () => {
  const res = await mcpRequest(TOOLS_LIST, { token: "wrong-token" });
  assert.equal(res.status, 401);
});

test("tools/list returns all five tools", async () => {
  const res = await mcpRequest(TOOLS_LIST);
  assert.equal(res.status, 200);
  const text = await res.text();
  for (const tool of ["generate_image", "edit_image", "gpt_image_generate", "gpt_image_edit", "deep_research"]) {
    assert.ok(text.includes(`"name":"${tool}"`), `missing tool ${tool}`);
  }
});

test("edit_image without a source image returns a helpful error", async () => {
  const res = await mcpRequest({
    jsonrpc: "2.0",
    id: 2,
    method: "tools/call",
    params: { name: "edit_image", arguments: { instruction: "make it blue" } },
  });
  const text = await res.text();
  assert.ok(text.includes("imageUrl or imageBase64"), `unexpected: ${text.slice(0, 300)}`);
});

test("GET /mcp is not allowed in stateless mode", async () => {
  const res = await fetch(`${BASE}/mcp`);
  assert.equal(res.status, 405);
});
