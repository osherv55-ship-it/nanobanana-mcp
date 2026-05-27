#!/usr/bin/env node
import express from "express";
import crypto from "node:crypto";
import path from "node:path";
import { promises as fs } from "node:fs";
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

const OPENAI_API_KEY = process.env.OPENAI_API_KEY;
const OPENAI_BASE_URL = process.env.OPENAI_BASE_URL || "https://api.openai.com/v1";
const OPENAI_IMAGE_MODEL = process.env.OPENAI_IMAGE_MODEL || "gpt-image-2-2026-04-21";
const OPENAI_TIMEOUT_MS = parseInt(process.env.OPENAI_TIMEOUT_MS || "180000", 10);

// Local-file reads are off by default — when the server is deployed to a shared host
// (Cloud Run, etc.) we don't want tool callers to exfiltrate arbitrary files. Set
// ALLOW_LOCAL_FILES=true on a self-hosted local server to enable file:// / path inputs.
const ALLOW_LOCAL_FILES = process.env.ALLOW_LOCAL_FILES === "true";

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
if (!OPENAI_API_KEY) {
  console.warn("WARNING: OPENAI_API_KEY not set — gpt_image_* tools will error if called.");
}

const ASPECT_RATIOS = ["1:1","16:9","9:16","4:5","5:4","3:4","4:3","21:9","2:3","3:2","1:4","4:1","1:8","8:1"];
const IMAGE_SIZES = ["512","1K","2K","4K"];

const GPT_IMAGE_SIZES = ["1024x1024", "1536x1024", "1024x1536", "auto"];
const GPT_IMAGE_QUALITIES = ["low", "medium", "high", "auto"];
const GPT_IMAGE_BACKGROUNDS = ["transparent", "opaque", "auto"];
const GPT_IMAGE_FORMATS = ["png", "jpeg", "webp"];

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

const EXT_TO_MIME = {
  ".png": "image/png",
  ".jpg": "image/jpeg",
  ".jpeg": "image/jpeg",
  ".webp": "image/webp",
  ".gif": "image/gif",
};

async function readLocalImage(filePath) {
  if (!ALLOW_LOCAL_FILES) {
    throw new Error("Local file paths are disabled. Set ALLOW_LOCAL_FILES=true on the server or pass an HTTPS URL instead.");
  }
  const ext = path.extname(filePath).toLowerCase();
  const mimeType = EXT_TO_MIME[ext];
  if (!mimeType) {
    throw new Error(`Unsupported image extension '${ext}'. Allowed: ${Object.keys(EXT_TO_MIME).join(", ")}.`);
  }
  let buf;
  try {
    buf = await fs.readFile(filePath);
  } catch (err) {
    throw new Error(`Could not read local image at ${filePath}: ${err.message}`);
  }
  return { base64: buf.toString("base64"), mimeType };
}

async function fetchImageAsBase64(input) {
  if (/^https?:\/\//.test(input)) {
    const res = await fetch(input);
    if (!res.ok) throw new Error(`Failed to fetch image: HTTP ${res.status}`);
    const buf = Buffer.from(await res.arrayBuffer());
    const mimeType = (res.headers.get("content-type") || "image/jpeg").split(";")[0];
    return { base64: buf.toString("base64"), mimeType };
  }
  if (input.startsWith("file://")) {
    return readLocalImage(new URL(input).pathname);
  }
  if (path.isAbsolute(input) || input.startsWith("./") || input.startsWith("../") || /^[A-Za-z]:[\\/]/.test(input)) {
    return readLocalImage(input);
  }
  throw new Error("Image input must be an HTTPS URL, a file:// URL, or an absolute local path.");
}

// ---- OpenAI Image (gpt-image-1) helpers ----
function buildOpenAIImageBody(prompt, opts) {
  const body = { model: OPENAI_IMAGE_MODEL, prompt, n: 1 };
  if (opts.size) body.size = opts.size;
  if (opts.quality) body.quality = opts.quality;
  if (opts.output_format) body.output_format = opts.output_format;
  if (opts.background) body.background = opts.background;
  return body;
}

async function postOpenAIJson(path, body) {
  if (!OPENAI_API_KEY) {
    throw new Error("OPENAI_API_KEY environment variable is required for gpt_image_* tools.");
  }
  const controller = new AbortController();
  const timeoutId = setTimeout(() => controller.abort(), OPENAI_TIMEOUT_MS);
  let res;
  try {
    res = await fetch(`${OPENAI_BASE_URL}${path}`, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        Authorization: `Bearer ${OPENAI_API_KEY}`,
      },
      body: JSON.stringify(body),
      signal: controller.signal,
    });
  } catch (error) {
    clearTimeout(timeoutId);
    if (error.name === "AbortError") {
      throw new Error(`OpenAI API timed out after ${OPENAI_TIMEOUT_MS}ms. Raise OPENAI_TIMEOUT_MS for longer renders.`);
    }
    throw new Error(`Network error calling OpenAI API: ${error.message}`);
  }
  clearTimeout(timeoutId);
  if (!res.ok) {
    throw new Error(`OpenAI API ${res.status}: ${await res.text()}`);
  }
  return res.json();
}

async function postOpenAIForm(path, form) {
  if (!OPENAI_API_KEY) {
    throw new Error("OPENAI_API_KEY environment variable is required for gpt_image_* tools.");
  }
  const controller = new AbortController();
  const timeoutId = setTimeout(() => controller.abort(), OPENAI_TIMEOUT_MS);
  let res;
  try {
    res = await fetch(`${OPENAI_BASE_URL}${path}`, {
      method: "POST",
      headers: { Authorization: `Bearer ${OPENAI_API_KEY}` },
      body: form,
      signal: controller.signal,
    });
  } catch (error) {
    clearTimeout(timeoutId);
    if (error.name === "AbortError") {
      throw new Error(`OpenAI API timed out after ${OPENAI_TIMEOUT_MS}ms. Raise OPENAI_TIMEOUT_MS for longer renders.`);
    }
    throw new Error(`Network error calling OpenAI API: ${error.message}`);
  }
  clearTimeout(timeoutId);
  if (!res.ok) {
    throw new Error(`OpenAI API ${res.status}: ${await res.text()}`);
  }
  return res.json();
}

function extractOpenAIImage(data, fallbackFormat) {
  const b64 = data?.data?.[0]?.b64_json;
  if (!b64) {
    throw new Error(`No image in OpenAI response: ${JSON.stringify(data).slice(0, 300)}`);
  }
  const fmt = (fallbackFormat || "png").toLowerCase();
  const mimeType = fmt === "jpeg" || fmt === "jpg" ? "image/jpeg" : `image/${fmt}`;
  return { base64: b64, mimeType };
}

async function callGptImageGenerate(prompt, opts) {
  const body = buildOpenAIImageBody(prompt, opts);
  const data = await postOpenAIJson("/images/generations", body);
  return extractOpenAIImage(data, opts.output_format);
}

async function callGptImageEdit(prompt, imageUrls, opts) {
  const form = new FormData();
  form.append("model", OPENAI_IMAGE_MODEL);
  form.append("prompt", prompt);
  form.append("n", "1");
  if (opts.size) form.append("size", opts.size);
  if (opts.quality) form.append("quality", opts.quality);
  if (opts.output_format) form.append("output_format", opts.output_format);
  if (opts.background) form.append("background", opts.background);

  for (const url of imageUrls) {
    const { base64, mimeType } = await fetchImageAsBase64(url);
    const ext = mimeType.includes("png") ? "png" : mimeType.includes("webp") ? "webp" : "jpg";
    const blob = new Blob([Buffer.from(base64, "base64")], { type: mimeType });
    form.append("image", blob, `source-${crypto.randomUUID()}.${ext}`);
  }

  if (opts.mask_url) {
    const { base64, mimeType } = await fetchImageAsBase64(opts.mask_url);
    const blob = new Blob([Buffer.from(base64, "base64")], { type: mimeType });
    form.append("mask", blob, "mask.png");
  }

  const data = await postOpenAIForm("/images/edits", form);
  return extractOpenAIImage(data, opts.output_format);
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

// ---- MCP server factory (one per request, stateless) ----
function buildServer() {
  const server = new Server(
    { name: "nanobanana", version: "2.1.0" },
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
        description: "Edit an existing image with a text instruction (image-to-image). For retouching, background changes, adding/removing elements while preserving the subject. Accepts an HTTPS URL, a file:// URL, or an absolute local path (local paths only when the server has ALLOW_LOCAL_FILES=true).",
        inputSchema: {
          type: "object",
          properties: {
            imageUrl: { type: "string", description: "HTTPS URL, file:// URL, or absolute local path of source image." },
            instruction: { type: "string", description: "What to change. Be specific and explicitly preserve elements that should stay unchanged." },
            aspectRatio: { type: "string", enum: ASPECT_RATIOS, description: "Output aspect ratio. Defaults to match input." },
            imageSize: { type: "string", enum: IMAGE_SIZES, description: "Output resolution. Default 1K." },
          },
          required: ["imageUrl", "instruction"],
        },
      },
      {
        name: "gpt_image_generate",
        description: "Generate an image from a text prompt using OpenAI's gpt-image-2 (the same model that powers ChatGPT image generation). Stronger than Gemini for text inside images, complex compositions, and photoreal product/lifestyle shots. Costs per image (low ~$0.006, medium ~$0.05, high ~$0.21). Requires OPENAI_API_KEY.",
        inputSchema: {
          type: "object",
          properties: {
            prompt: { type: "string", description: "Detailed description. gpt-image-1 follows complex prompts well; include style, composition, lighting, mood." },
            size: { type: "string", enum: GPT_IMAGE_SIZES, description: "1024x1024 square, 1536x1024 landscape, 1024x1536 portrait, or 'auto'. Default 'auto'." },
            quality: { type: "string", enum: GPT_IMAGE_QUALITIES, description: "low ($0.01), medium ($0.04), high ($0.17), auto. Default 'auto'." },
            output_format: { type: "string", enum: GPT_IMAGE_FORMATS, description: "png (default), jpeg, or webp. Use png/webp for transparency." },
            background: { type: "string", enum: GPT_IMAGE_BACKGROUNDS, description: "transparent (png/webp only), opaque, or auto. Default 'auto'." },
          },
          required: ["prompt"],
        },
      },
      {
        name: "gpt_image_edit",
        description: "Edit one or more existing images with a text instruction using OpenAI's gpt-image-2. Supports multi-image composition (pass multiple sources to combine elements). Each source can be an HTTPS URL, a file:// URL, or an absolute local path (local paths require ALLOW_LOCAL_FILES=true on the server). Costs per call. Requires OPENAI_API_KEY.",
        inputSchema: {
          type: "object",
          properties: {
            imageUrls: { type: "array", items: { type: "string" }, description: "One or more source images (HTTPS URL, file:// URL, or absolute local path). Multiple sources are combined into a single edited output." },
            instruction: { type: "string", description: "What to change. Be explicit about what to preserve and what to alter." },
            mask_url: { type: "string", description: "Optional PNG mask (transparent = editable region). HTTPS URL, file:// URL, or absolute local path. Only used with a single source image." },
            size: { type: "string", enum: GPT_IMAGE_SIZES, description: "Output size. Default 'auto' (matches input)." },
            quality: { type: "string", enum: GPT_IMAGE_QUALITIES, description: "Render quality / cost tier. Default 'auto'." },
            output_format: { type: "string", enum: GPT_IMAGE_FORMATS, description: "png (default), jpeg, or webp." },
            background: { type: "string", enum: GPT_IMAGE_BACKGROUNDS, description: "transparent / opaque / auto." },
          },
          required: ["imageUrls", "instruction"],
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

      if (name === "gpt_image_generate" || name === "gpt_image_edit") {
        const opts = {
          size: args.size,
          quality: args.quality,
          output_format: args.output_format,
          background: args.background,
        };
        const result = name === "gpt_image_generate"
          ? await callGptImageGenerate(args.prompt, opts)
          : await callGptImageEdit(args.instruction, args.imageUrls, { ...opts, mask_url: args.mask_url });
        return {
          content: [{ type: "image", data: result.base64, mimeType: result.mimeType }],
        };
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
  console.log(`OpenAI image model: ${OPENAI_IMAGE_MODEL}`);
  console.log(`Local file inputs: ${ALLOW_LOCAL_FILES ? "ALLOWED" : "blocked (set ALLOW_LOCAL_FILES=true to enable)"}`);
  console.log(`Auth: ${MCP_AUTH_TOKEN ? "Bearer token required" : "UNAUTHENTICATED"}`);
});
