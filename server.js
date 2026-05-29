#!/usr/bin/env node
import express from "express";
import crypto from "node:crypto";
import { Server } from "@modelcontextprotocol/sdk/server/index.js";
import { StreamableHTTPServerTransport } from "@modelcontextprotocol/sdk/server/streamableHttp.js";
import {
  CallToolRequestSchema,
  ListToolsRequestSchema,
} from "@modelcontextprotocol/sdk/types.js";

// ---- Configuration ----
const PORT = parseInt(process.env.PORT || "8080", 10);
const MODEL = process.env.GEMINI_IMAGE_MODEL || "gemini-3.1-flash-image-preview";
const GEMINI_API_KEY = process.env.GEMINI_API_KEY;
const MCP_AUTH_TOKEN = process.env.MCP_AUTH_TOKEN; // optional Bearer token
const API_BASE = "https://generativelanguage.googleapis.com/v1beta/models";

const PERPLEXITY_API_KEY = process.env.PERPLEXITY_API_KEY;
const PERPLEXITY_BASE_URL = process.env.PERPLEXITY_BASE_URL || "https://api.perplexity.ai";
const PERPLEXITY_TIMEOUT_MS = parseInt(process.env.PERPLEXITY_TIMEOUT_MS || "300000", 10);

if (!GEMINI_API_KEY) {
  console.error("FATAL: GEMINI_API_KEY environment variable is not set.");
  process.exit(1);
}
if (!MCP_AUTH_TOKEN) {
  console.warn("WARNING: MCP_AUTH_TOKEN not set — server is unauthenticated.");
}
if (!PERPLEXITY_API_KEY) {
  console.warn("WARNING: PERPLEXITY_API_KEY not set — deep_research tool will error if called.");
}

const ASPECT_RATIOS = ["1:1","16:9","9:16","4:5","5:4","3:4","4:3","21:9","2:3","3:2","1:4","4:1","1:8","8:1"];
const IMAGE_SIZES = ["512","1K","2K","4K"];

// ---- Gemini API helpers ----
async function callGemini(parts, { aspectRatio, imageSize } = {}) {
  const generationConfig = { responseModalities: ["TEXT", "IMAGE"] };
  if (aspectRatio || imageSize) {
    generationConfig.responseFormat = {
      image: {
        ...(aspectRatio ? { aspectRatio } : {}),
        ...(imageSize ? { imageSize } : {}),
      },
    };
  }

  const res = await fetch(`${API_BASE}/${MODEL}:generateContent`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
      "x-goog-api-key": GEMINI_API_KEY,
    },
    body: JSON.stringify({ contents: [{ parts }], generationConfig }),
  });

  if (!res.ok) {
    throw new Error(`Gemini API ${res.status}: ${await res.text()}`);
  }

  const data = await res.json();
  const allParts = data.candidates?.[0]?.content?.parts || [];
  const imagePart = allParts.find(
    (p) => (p.inlineData?.mimeType || p.inline_data?.mime_type || "").startsWith("image/")
  );
  const text = allParts.filter((p) => p.text).map((p) => p.text).join("\n");

  if (!imagePart) {
    throw new Error(`No image returned. Model said: ${text || "(nothing)"}`);
  }

  const inline = imagePart.inlineData || imagePart.inline_data;
  return {
    base64: inline.data,
    mimeType: inline.mimeType || inline.mime_type,
    text,
  };
}

async function fetchImageAsBase64(input) {
  if (!/^https?:\/\//.test(input)) {
    throw new Error("edit_image requires an HTTPS URL (local file paths are not accessible from a remote server).");
  }
  const res = await fetch(input);
  if (!res.ok) throw new Error(`Failed to fetch image: HTTP ${res.status}`);
  const buf = Buffer.from(await res.arrayBuffer());
  const mimeType = (res.headers.get("content-type") || "image/jpeg").split(";")[0];
  return { base64: buf.toString("base64"), mimeType };
}

// ---- Perplexity Sonar Deep Research helpers ----
const REASONING_EFFORTS = ["minimal", "low", "medium", "high"];
const RECENCY_FILTERS = ["hour", "day", "week", "month", "year"];

function stripThinkingTokens(content) {
  return content.replace(/<think>[\s\S]*?<\/think>/g, "").trim();
}

async function consumeSonarStream(response) {
  const reader = response.body.getReader();
  const decoder = new TextDecoder();
  const contentParts = [];
  let citations;
  let buffer = "";

  while (true) {
    const { done, value } = await reader.read();
    if (done) break;
    buffer += decoder.decode(value, { stream: true });

    const lines = buffer.split("\n");
    buffer = lines.pop() || "";

    for (const line of lines) {
      const trimmed = line.trim();
      if (!trimmed.startsWith("data:")) continue;
      const data = trimmed.slice(5).trim();
      if (data === "[DONE]") continue;
      try {
        const parsed = JSON.parse(data);
        if (parsed.citations) citations = parsed.citations;
        const delta = parsed.choices?.[0]?.delta;
        if (delta?.content) contentParts.push(delta.content);
      } catch {
        // skip malformed chunks / keep-alives
      }
    }
  }

  return { content: contentParts.join(""), citations };
}

async function callSonarDeepResearch(query, opts = {}) {
  if (!PERPLEXITY_API_KEY) {
    throw new Error("PERPLEXITY_API_KEY environment variable is required for deep_research.");
  }

  const messages = [];
  if (opts.system) messages.push({ role: "system", content: opts.system });
  messages.push({ role: "user", content: query });

  const body = {
    model: "sonar-deep-research",
    messages,
    stream: true,
    ...(opts.reasoningEffort && { reasoning_effort: opts.reasoningEffort }),
    ...(opts.searchRecencyFilter && { search_recency_filter: opts.searchRecencyFilter }),
    ...(opts.searchDomainFilter && { search_domain_filter: opts.searchDomainFilter }),
  };

  const controller = new AbortController();
  const timeoutId = setTimeout(() => controller.abort(), PERPLEXITY_TIMEOUT_MS);

  let res;
  try {
    res = await fetch(`${PERPLEXITY_BASE_URL}/chat/completions`, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        Authorization: `Bearer ${PERPLEXITY_API_KEY}`,
        "User-Agent": "nanobanana-mcp/sonar-deep-research",
      },
      body: JSON.stringify(body),
      signal: controller.signal,
    });
  } catch (error) {
    clearTimeout(timeoutId);
    if (error.name === "AbortError") {
      throw new Error(`Perplexity API timed out after ${PERPLEXITY_TIMEOUT_MS}ms. Raise PERPLEXITY_TIMEOUT_MS to allow longer deep-research runs.`);
    }
    throw new Error(`Network error calling Perplexity API: ${error.message}`);
  }
  clearTimeout(timeoutId);

  if (!res.ok) {
    const errorText = await res.text().catch(() => "(unreadable error body)");
    throw new Error(`Perplexity API ${res.status} ${res.statusText}: ${errorText}`);
  }

  const { content, citations } = await consumeSonarStream(res);
  let text = opts.stripThinking ? stripThinkingTokens(content) : content;

  if (Array.isArray(citations) && citations.length > 0) {
    text += "\n\nCitations:\n" + citations.map((c, i) => `[${i + 1}] ${c}`).join("\n");
  }
  return text;
}

// ---- Clothing shopping (style-aware) helpers ----
// Builds a stylist-grade research brief for Sonar from structured shopping inputs.
// The heavy lifting (live web search, citations) is Sonar's; this just shapes the
// query + system persona so results come back as concrete, purchasable items.
function buildClothingShoppingPrompt(args) {
  const {
    request,
    style_preferences,
    budget,
    sizes,
    gender,
    region,
    occasion,
    avoid,
  } = args;

  const constraints = [];
  if (style_preferences) constraints.push(`Style preferences: ${style_preferences}`);
  if (budget) constraints.push(`Budget: ${budget}`);
  if (sizes) constraints.push(`Size(s): ${sizes}`);
  if (gender) constraints.push(`Fit/gender section: ${gender}`);
  if (region) constraints.push(`Shopper region (ship-to + currency): ${region}`);
  if (occasion) constraints.push(`Occasion / use case: ${occasion}`);
  if (avoid) constraints.push(`Avoid: ${avoid}`);

  const userQuery = [
    `Shopping request: ${request}`,
    "",
    constraints.length ? constraints.join("\n") : "(no extra constraints given)",
    "",
    "Find specific, currently-purchasable clothing items from real online retailers that match the request and the style preferences above.",
  ].join("\n");

  const system = [
    "You are a personal shopping stylist. The user wants to BUY clothes online that fit their taste, budget, size and region.",
    "Search current retailer and marketplace listings and return a concrete shortlist of 5-8 items.",
    "For EACH item provide, as a markdown list entry:",
    "- Item name + brand",
    "- Price with currency (note it must be verified at checkout — it may be stale)",
    "- Retailer name and a DIRECT product-page URL (not a homepage or search page)",
    "- Available sizes if visible, otherwise say 'check listing'",
    "- One sentence on why it matches the user's stated style",
    "Prioritise items that ship to the user's region. Respect the budget — do not pad the list with items far above it.",
    "If you cannot confirm a direct product URL for an item, say so rather than inventing a link.",
    "End with a short 'How to style these together' note (2-3 sentences) and a one-line reminder to verify price, stock and shipping before buying.",
    "Never fabricate prices, stock status, or links.",
  ].join("\n");

  return { userQuery, system };
}

// ---- MCP server factory (one per request, stateless) ----
function buildServer() {
  const server = new Server(
    { name: "nanobanana", version: "2.0.0" },
    { capabilities: { tools: {} } }
  );

  server.setRequestHandler(ListToolsRequestSchema, async () => ({
    tools: [
      {
        name: "generate_image",
        description: "Generate an image from a text prompt using Google's Nano Banana (Gemini Flash Image). Best for marketing visuals, product mockups, social media content. Supports Hebrew prompts.",
        inputSchema: {
          type: "object",
          properties: {
            prompt: { type: "string", description: "Detailed description: style, lighting, composition, mood, colors." },
            aspectRatio: { type: "string", enum: ASPECT_RATIOS, description: "1:1 Instagram post, 9:16 Stories/Reels, 4:5 IG portrait, 16:9 banner. Default 1:1." },
            imageSize: { type: "string", enum: IMAGE_SIZES, description: "Resolution. Default 1K. Use 2K/4K for production assets." },
          },
          required: ["prompt"],
        },
      },
      {
        name: "edit_image",
        description: "Edit an existing image with a text instruction (image-to-image). For retouching, background changes, adding/removing elements while preserving the subject. Requires a publicly accessible HTTPS URL for the source image.",
        inputSchema: {
          type: "object",
          properties: {
            imageUrl: { type: "string", description: "HTTPS URL of source image (publicly accessible)." },
            instruction: { type: "string", description: "What to change. Be specific and explicitly preserve elements that should stay unchanged." },
            aspectRatio: { type: "string", enum: ASPECT_RATIOS, description: "Output aspect ratio. Defaults to match input." },
            imageSize: { type: "string", enum: IMAGE_SIZES, description: "Output resolution. Default 1K." },
          },
          required: ["imageUrl", "instruction"],
        },
      },
      {
        name: "deep_research",
        description: "Conduct deep, multi-source web research using Perplexity's sonar-deep-research model. Best for literature reviews, comprehensive market analysis, investigative briefs. Slow (30s+), returns a detailed answer with numbered citations. For quick factual Q&A this is overkill — use a normal search tool instead.",
        inputSchema: {
          type: "object",
          properties: {
            query: { type: "string", description: "The research question. Be specific about scope, time window, and what kind of synthesis you want." },
            system: { type: "string", description: "Optional system instruction (e.g. persona, output format constraints)." },
            reasoning_effort: { type: "string", enum: REASONING_EFFORTS, description: "Depth of reasoning. Higher = more thorough but slower/costlier. Default: model default." },
            strip_thinking: { type: "boolean", description: "If true, removes <think>...</think> blocks from the response to save tokens. Default false." },
            search_recency_filter: { type: "string", enum: RECENCY_FILTERS, description: "Limit sources by recency (e.g. 'week' for this week's news)." },
            search_domain_filter: { type: "array", items: { type: "string" }, description: "Restrict to / exclude domains. Use '-' prefix to exclude (e.g. ['-reddit.com'])." },
          },
          required: ["query"],
        },
      },
      {
        name: "shop_for_clothes",
        description: "Personal clothing-shopping stylist. Given a request plus the shopper's style preferences, budget, size and region, it searches live online retailers (via Perplexity Sonar) and returns a shortlist of 5-8 specific, purchasable items with direct product links, prices and styling notes. Use this to DISCOVER and recommend clothes to buy — it does not place orders or handle payment. Pair it with the media-memory skill to persist style preferences and with generate_image to visualize the recommended looks. Slow (30s+). Supports Hebrew.",
        inputSchema: {
          type: "object",
          properties: {
            request: { type: "string", description: "What the shopper wants to find, e.g. 'a winter capsule of 5 pieces' or 'a linen shirt for a beach wedding'." },
            style_preferences: { type: "string", description: "The shopper's taste: aesthetics, brands, colors, silhouettes, materials they love. Pull this from the stored style profile (media-memory) when available." },
            budget: { type: "string", description: "Budget per item or total, with currency, e.g. 'under $80 each' or '₪500 total'." },
            sizes: { type: "string", description: "Sizes/measurements, e.g. 'M tops, 32 waist, EU 42 shoes'." },
            gender: { type: "string", description: "Fit / retailer section to search, e.g. 'women', 'men', 'unisex'." },
            region: { type: "string", description: "Where to ship and which currency to price in, e.g. 'Israel / ILS' or 'US / USD'." },
            occasion: { type: "string", description: "Context the clothes are for, e.g. 'office', 'wedding guest', 'everyday casual'." },
            avoid: { type: "string", description: "Things to exclude, e.g. 'no fast fashion', 'no synthetics', 'no logos'." },
            reasoning_effort: { type: "string", enum: REASONING_EFFORTS, description: "Search depth. Higher = more thorough but slower. Default: model default." },
            search_domain_filter: { type: "array", items: { type: "string" }, description: "Restrict to / exclude retailer domains. Use '-' prefix to exclude (e.g. ['zara.com','-ebay.com'])." },
          },
          required: ["request"],
        },
      },
    ],
  }));

  server.setRequestHandler(CallToolRequestSchema, async (request) => {
    const { name, arguments: args } = request.params;
    try {
      if (name === "deep_research") {
        const text = await callSonarDeepResearch(args.query, {
          system: args.system,
          reasoningEffort: args.reasoning_effort,
          stripThinking: args.strip_thinking === true,
          searchRecencyFilter: args.search_recency_filter,
          searchDomainFilter: args.search_domain_filter,
        });
        return { content: [{ type: "text", text }] };
      }

      if (name === "shop_for_clothes") {
        if (!args.request) {
          throw new Error("shop_for_clothes requires a 'request' describing what to shop for.");
        }
        const { userQuery, system } = buildClothingShoppingPrompt(args);
        const text = await callSonarDeepResearch(userQuery, {
          system,
          reasoningEffort: args.reasoning_effort,
          searchDomainFilter: args.search_domain_filter,
          stripThinking: true,
        });
        return { content: [{ type: "text", text }] };
      }

      let parts;
      if (name === "generate_image") {
        parts = [{ text: args.prompt }];
      } else if (name === "edit_image") {
        const { base64, mimeType } = await fetchImageAsBase64(args.imageUrl);
        parts = [
          { inline_data: { mime_type: mimeType, data: base64 } },
          { text: args.instruction },
        ];
      } else {
        throw new Error(`Unknown tool: ${name}`);
      }

      const result = await callGemini(parts, {
        aspectRatio: args.aspectRatio,
        imageSize: args.imageSize,
      });

      return {
        content: [
          { type: "image", data: result.base64, mimeType: result.mimeType },
          ...(result.text ? [{ type: "text", text: `Model notes: ${result.text}` }] : []),
        ],
      };
    } catch (error) {
      return {
        content: [{ type: "text", text: `Error: ${error.message}` }],
        isError: true,
      };
    }
  });

  return server;
}

// ---- Express HTTP layer ----
const app = express();
app.use(express.json({ limit: "50mb" }));

// Health check (Cloud Run hits this)
app.get("/", (_req, res) => {
  res.json({ status: "ok", server: "nanobanana-mcp", model: MODEL });
});

// Optional Bearer-token auth on the MCP endpoint
function authenticate(req, res, next) {
  if (!MCP_AUTH_TOKEN) return next();
  const header = req.headers.authorization || "";
  const token = header.replace(/^Bearer\s+/i, "");
  if (token !== MCP_AUTH_TOKEN) {
    return res.status(401).json({
      jsonrpc: "2.0",
      error: { code: -32000, message: "Unauthorized" },
      id: null,
    });
  }
  next();
}

// MCP endpoint — stateless, per-request transport
app.post("/mcp", authenticate, async (req, res) => {
  try {
    const server = buildServer();
    const transport = new StreamableHTTPServerTransport({
      sessionIdGenerator: undefined, // stateless
    });

    res.on("close", () => {
      transport.close().catch(() => {});
      server.close().catch(() => {});
    });

    await server.connect(transport);
    await transport.handleRequest(req, res, req.body);
  } catch (error) {
    console.error("MCP request error:", error);
    if (!res.headersSent) {
      res.status(500).json({
        jsonrpc: "2.0",
        error: { code: -32603, message: `Internal error: ${error.message}` },
        id: null,
      });
    }
  }
});

// GET/DELETE on /mcp are not supported in stateless mode
app.get("/mcp", (_req, res) => res.status(405).json({ error: "Method Not Allowed" }));
app.delete("/mcp", (_req, res) => res.status(405).json({ error: "Method Not Allowed" }));

app.listen(PORT, () => {
  console.log(`Nanobanana MCP server (${MODEL}) listening on port ${PORT}`);
  console.log(`Auth: ${MCP_AUTH_TOKEN ? "Bearer token required" : "UNAUTHENTICATED"}`);
});
