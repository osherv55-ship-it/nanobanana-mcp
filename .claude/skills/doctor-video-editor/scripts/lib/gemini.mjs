// Gemini API helpers: Files API upload, generateContent, JSON-extracting prompt.
// Uses raw fetch to match server.js style — no SDK dependency.

import fs from "node:fs";
import path from "node:path";

const API_BASE = "https://generativelanguage.googleapis.com/v1beta";
const UPLOAD_BASE = "https://generativelanguage.googleapis.com/upload/v1beta/files";

export const DEFAULT_MODEL =
  process.env.GEMINI_VIDEO_MODEL || "gemini-2.5-flash";

const INLINE_LIMIT_BYTES = 18 * 1024 * 1024; // stay under 20MB request cap

function apiKey() {
  const k = process.env.GEMINI_API_KEY;
  if (!k) throw new Error("GEMINI_API_KEY is not set");
  return k;
}

export async function uploadFile(localPath, mimeType) {
  const stat = fs.statSync(localPath);
  const displayName = path.basename(localPath);

  // Step 1: start a resumable upload, get the upload URL.
  const startRes = await fetch(`${UPLOAD_BASE}?key=${apiKey()}`, {
    method: "POST",
    headers: {
      "X-Goog-Upload-Protocol": "resumable",
      "X-Goog-Upload-Command": "start",
      "X-Goog-Upload-Header-Content-Length": String(stat.size),
      "X-Goog-Upload-Header-Content-Type": mimeType,
      "Content-Type": "application/json",
    },
    body: JSON.stringify({ file: { display_name: displayName } }),
  });
  if (!startRes.ok) {
    throw new Error(
      `Files API start failed ${startRes.status}: ${await startRes.text()}`,
    );
  }
  const uploadUrl = startRes.headers.get("x-goog-upload-url");
  if (!uploadUrl) throw new Error("Files API did not return upload URL");

  // Step 2: upload the bytes and finalize.
  const body = fs.readFileSync(localPath);
  const uploadRes = await fetch(uploadUrl, {
    method: "POST",
    headers: {
      "Content-Length": String(stat.size),
      "X-Goog-Upload-Offset": "0",
      "X-Goog-Upload-Command": "upload, finalize",
    },
    body,
  });
  if (!uploadRes.ok) {
    throw new Error(
      `Files API upload failed ${uploadRes.status}: ${await uploadRes.text()}`,
    );
  }
  const json = await uploadRes.json();
  const file = json.file;
  if (!file?.uri) throw new Error("Files API response missing file.uri");

  // Wait for the file to become ACTIVE — video processing takes a moment.
  return await waitForFileActive(file.name);
}

async function waitForFileActive(fileName, timeoutMs = 5 * 60 * 1000) {
  const start = Date.now();
  while (true) {
    const res = await fetch(`${API_BASE}/${fileName}?key=${apiKey()}`);
    if (!res.ok) {
      throw new Error(
        `Files.get failed ${res.status}: ${await res.text()}`,
      );
    }
    const f = await res.json();
    if (f.state === "ACTIVE") return f;
    if (f.state === "FAILED") {
      throw new Error(`File processing FAILED: ${JSON.stringify(f.error)}`);
    }
    if (Date.now() - start > timeoutMs) {
      throw new Error(`Timed out waiting for file ${fileName} to become ACTIVE`);
    }
    await new Promise((r) => setTimeout(r, 3000));
  }
}

export async function buildMediaPart(localPath, mimeType) {
  const stat = fs.statSync(localPath);
  if (stat.size <= INLINE_LIMIT_BYTES) {
    const data = fs.readFileSync(localPath).toString("base64");
    return { inlineData: { mimeType, data } };
  }
  process.stderr.write(
    `[gemini] file ${path.basename(localPath)} is ${(stat.size / 1024 / 1024).toFixed(1)} MB — uploading via Files API...\n`,
  );
  const file = await uploadFile(localPath, mimeType);
  return { fileData: { fileUri: file.uri, mimeType: file.mimeType || mimeType } };
}

export async function generateJson({
  model = DEFAULT_MODEL,
  parts,
  systemInstruction,
  temperature = 0.2,
  maxOutputTokens = 32768,
}) {
  const body = {
    contents: [{ role: "user", parts }],
    generationConfig: {
      responseMimeType: "application/json",
      temperature,
      maxOutputTokens,
    },
  };
  if (systemInstruction) {
    body.systemInstruction = { parts: [{ text: systemInstruction }] };
  }

  const res = await fetch(
    `${API_BASE}/models/${model}:generateContent?key=${apiKey()}`,
    {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(body),
    },
  );
  if (!res.ok) {
    throw new Error(`Gemini ${model} ${res.status}: ${await res.text()}`);
  }
  const json = await res.json();
  const text = json.candidates?.[0]?.content?.parts
    ?.map((p) => p.text || "")
    .join("")
    .trim();
  if (!text) {
    throw new Error(
      `Gemini returned no text. Full response: ${JSON.stringify(json).slice(0, 500)}`,
    );
  }
  try {
    return JSON.parse(text);
  } catch (e) {
    throw new Error(
      `Gemini returned non-JSON despite responseMimeType=application/json. First 500 chars: ${text.slice(0, 500)}`,
    );
  }
}
