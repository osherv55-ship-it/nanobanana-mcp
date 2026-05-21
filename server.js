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

if (!GEMINI_API_KEY) {
  console.error("FATAL: GEMINI_API_KEY environment variable is not set.");
  process.exit(1);
}
if (!MCP_AUTH_TOKEN) {
  console.warn("WARNING: MCP_AUTH_TOKEN not set — server is unauthenticated.");
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
    ],
  }));

  server.setRequestHandler(CallToolRequestSchema, async (request) => {
    const { name, arguments: args } = request.params;
    try {
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
