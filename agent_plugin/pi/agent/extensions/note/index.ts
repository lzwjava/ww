/**
 * note extension — enqueue assistant responses to the ww note queue
 * (~/.config/ww/note_queue.json) for external consumption.
 *
 * The queue format is a plain JSON array matching ww's note_queue.py format,
 * so the `ww note watch` daemon can auto-process entries.
 *
 * Usage:
 *   /note                          # enqueue last assistant response
 *   /note 3                        # enqueue 3rd assistant response
 *   /note --title "Custom Title"   # supply a title hint
 *   /note --private                # save to private-notes dir, skip git push
 *   /note -p                       # short flag (same as --private)
 *   /note -p --title "T"           # combine flags
 */

import type { ExtensionAPI } from "@earendil-works/pi-coding-agent";
import { createHash } from "node:crypto";
import { existsSync, mkdirSync, readFileSync, writeFileSync } from "node:fs";
import { homedir } from "node:os";
import { join } from "node:path";

// ---------------------------------------------------------------------------
// Types — matches ww's note_queue.py format
// ---------------------------------------------------------------------------

interface WwQueueEntry {
	id: string;
	content: string;
	content_hash: string;
	queued_at: string;
	status: "pending" | "done" | "failed";
	type: "note" | "log" | "html";
	note_path: string | null;
	title?: string;
	private?: boolean;
}

type WwQueue = WwQueueEntry[];

// ---------------------------------------------------------------------------
// Constants
// ---------------------------------------------------------------------------

const QUEUE_DIR = join(homedir(), ".config", "ww");
const QUEUE_FILE = join(QUEUE_DIR, "note_queue.json");

// ---------------------------------------------------------------------------
// Helpers
// ---------------------------------------------------------------------------

/** SHA-256 hex digest, first 12 chars (matches ww's content_hash). */
function contentHash(text: string): string {
	return createHash("sha256").update(text).digest("hex").slice(0, 12);
}

/** Strip thinking / reasoning / scratchpad tags from text. */
function stripReasoningTags(text: string): string {
	return text.replace(
		/<(?:thinking|reasoning|scratchpad)>[\s\S]*?<\/(?:thinking|reasoning|scratchpad)>/gi,
		"",
	).trim();
}

/** Extract plain text from content content blocks or a string. */
function extractText(content: unknown): string {
	if (!content) return "";

	if (typeof content === "string") return content;

	if (Array.isArray(content)) {
		const parts: string[] = [];
		for (const block of content) {
			if (block && typeof block === "object" && "type" in block) {
				if (block.type === "text" && typeof block.text === "string") {
					parts.push(block.text);
				}
			}
		}
		return parts.join("\n");
	}

	return "";
}

/** Read the queue file (plain JSON array), or return an empty array. */
function readQueue(): WwQueue {
	if (!existsSync(QUEUE_FILE)) {
		return [];
	}
	try {
		const raw = readFileSync(QUEUE_FILE, "utf-8");
		const parsed = JSON.parse(raw);
		return Array.isArray(parsed) ? parsed : [];
	} catch {
		return [];
	}
}

/** Append an entry to the queue file, creating dir/file as needed. */
function enqueue(text: string, title?: string, isPrivate?: boolean): WwQueueEntry {
	if (!existsSync(QUEUE_DIR)) {
		mkdirSync(QUEUE_DIR, { recursive: true });
	}

	const queue = readQueue();
	const hash = contentHash(text);

	// Dedup: skip if same hash + pending status already exists
	for (const entry of queue) {
		if (entry.content_hash === hash && entry.status === "pending") {
			throw new Error(
				`Duplicate content already queued (id=${entry.id}, queued at ${entry.queued_at})`,
			);
		}
	}

	const now = new Date().toISOString().replace(/\.\d+Z$/, "Z"); // seconds precision
	const entry: WwQueueEntry = {
		id: hash,
		content: text,
		content_hash: hash,
		queued_at: now,
		status: "pending",
		type: "note",
		note_path: null,
	};
	if (title) entry.title = title;
	if (isPrivate) entry.private = true;

	queue.push(entry);
	writeFileSync(QUEUE_FILE, JSON.stringify(queue, null, 2) + "\n", "utf-8");

	return entry;
}

// ---------------------------------------------------------------------------
// Command handler
// ---------------------------------------------------------------------------

function handleNote(rawArgs: string, ctx: any): string | undefined {
	// Parse args: [number] [--title <title>] [--private]
	const args = rawArgs.trim();
	let number: number | undefined;
	let title: string | undefined;
	let isPrivate = false;

	// Simple manual parse (no shlex dependency needed)
	const tokens: string[] = [];
	let current = "";
	let inQuote: string | null = null;
	for (const ch of args) {
		if (inQuote) {
			if (ch === inQuote) {
				inQuote = null;
			} else {
				current += ch;
			}
		} else if (ch === "'" || ch === '"') {
			inQuote = ch;
		} else if (ch === " ") {
			if (current) {
				tokens.push(current);
				current = "";
			}
		} else {
			current += ch;
		}
	}
	if (current) tokens.push(current);

	for (let i = 0; i < tokens.length; i++) {
		if (tokens[i] === "--title" && i + 1 < tokens.length) {
			title = tokens[i + 1];
			i++;
		} else if (tokens[i] === "--private" || tokens[i] === "-p") {
			isPrivate = true;
		} else if (number === undefined && /^\d+$/.test(tokens[i])) {
			number = parseInt(tokens[i], 10);
		}
	}

	// Collect assistant messages from the session
	const entries = ctx.sessionManager.getEntries();
	const assistantEntries = entries.filter(
		(e: any) => e.type === "message" && e.message?.role === "assistant",
	);

	if (assistantEntries.length === 0) {
		return "No assistant responses to save.";
	}

	let idx: number;
	if (number !== undefined) {
		idx = number - 1;
		if (idx < 0 || idx >= assistantEntries.length) {
			return `Invalid response number. Use 1-${assistantEntries.length}.`;
		}
	} else {
		// Find last non-empty assistant response
		idx = assistantEntries.length - 1;
		while (idx >= 0) {
			const text = extractText(assistantEntries[idx].message.content);
			if (text.trim()) break;
			idx--;
		}
		if (idx < 0) {
			return "No content to save in assistant responses.";
		}
	}

	const rawText = extractText(assistantEntries[idx].message.content);
	if (!rawText.trim()) {
		return "No content to save in that assistant response.";
	}

	const cleaned = stripReasoningTags(rawText);
	if (!cleaned) {
		return "No content to save (only reasoning tags found).";
	}

	try {
		const entry = enqueue(cleaned, title, isPrivate);
		const label = isPrivate ? " (private)" : "";
		return (
			`Enqueued${label} (id=${entry.id}, ${cleaned.length} chars). ` +
			`Queue: ${QUEUE_FILE}\n` +
			`External watcher (if running) will process it automatically.`
		);
	} catch (e: any) {
		return e.message;
	}
}

// ---------------------------------------------------------------------------
// Extension entry point
// ---------------------------------------------------------------------------

export default function (pi: ExtensionAPI) {
	pi.registerCommand("note", {
		description:
			"Enqueue the last assistant response to ~/.config/ww/note_queue.json " +
			"for external processing.",
		handler: (args, ctx) => {
			const result = handleNote(args, ctx);
			if (result) {
				ctx.ui.notify(result, "info");
			}
		},
	});
}
