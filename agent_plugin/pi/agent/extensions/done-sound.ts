/**
 * Pi "Done" Sound Extension
 *
 * Plays a sound when the Pi agent finishes all work and is waiting for input.
 *
 * Listens to the `agent_settled` event, which fires once when Pi will not
 * continue running automatically (i.e. after retries, auto-compaction, and
 * queued follow-up/steering messages are all drained). This is the right hook
 * for a "turn is truly done, hand back to the user" notification.
 *
 * Defaults:
 *   - Sound file: /usr/share/sounds/freedesktop/stereo/complete.oga
 *   - Player: auto-detected (pw-play, paplay, aplay, ffplay, ogg123, ...)
 *
 * Override via environment variables (set in your shell or settings.json):
 *   PI_DONE_SOUND_FILE  - path to a sound file (.oga/.ogg/.wav/.mp3/...)
 *   PI_DONE_SOUND_CMD    - full command (space-separated) to play the sound,
 *                          e.g. "aplay /custom/done.wav". Overrides file auto-detect.
 *
 * Commands:
 *   /done-sound         - play the sound once (test it)
 *   /done-sound on|off  - enable/disable for this process
 *   /done-sound status  - show current status
 */

import type { ExtensionAPI } from "@earendil-works/pi-coding-agent";
import { execFile, type ExecFileException } from "node:child_process";
import { existsSync } from "node:fs";

const isMacOS = process.platform === "darwin";

// Platform-specific default sound files.
const DEFAULT_SOUND_FILE_LINUX = "/usr/share/sounds/freedesktop/stereo/complete.oga";
const DEFAULT_SOUND_FILE_MACOS = "/System/Library/Sounds/Glass.aiff";
const DEFAULT_SOUND_FILE = isMacOS ? DEFAULT_SOUND_FILE_MACOS : DEFAULT_SOUND_FILE_LINUX;

// Player candidates in priority order. Each entry maps a found binary to the
// argument list used to play a file path. The file path is appended.
// macOS-native `afplay` is listed first on macOS so we use the built-in
// player rather than homebrew fallbacks.
const PLAYER_CANDIDATES: Array<{ bin: string; args: string[] }> = [
	...(isMacOS ? [{ bin: "afplay", args: [] }] : []), // macOS built-in
	{ bin: "pw-play", args: [] }, // PipeWire
	{ bin: "paplay", args: [] }, // PulseAudio
	{ bin: "ogg123", args: ["-q"] }, // vorbis-tools
	{ bin: "aplay", args: ["-q"] }, // ALSA (wav only, but harmless to try)
	{ bin: "ffplay", args: ["-nodisp", "-autoexit", "-loglevel", "quiet"] }, // ffmpeg
	{ bin: "mpv", args: ["--no-video", "--really-quiet"] }, // mpv
	{ bin: "vlc", args: ["--play-and-exit", "--intf", "dummy", "--no-loop"] }, // vlc
];

function which(bin: string): string | null {
	const { PATH } = process.env;
	if (!PATH) return null;
	for (const dir of PATH.split(":")) {
		if (!dir) continue;
		const full = `${dir}/${bin}`;
		try {
			// Fast existence check without spawning; ignore errors.
			// eslint-disable-next-line @typescript-eslint/no-require-imports
			const fs = require("node:fs");
			if (fs.existsSync(full)) return full;
		} catch {
			// ignore
		}
	}
	return null;
}

function detectPlayer(): { bin: string; args: string[] } | null {
	for (const candidate of PLAYER_CANDIDATES) {
		if (which(candidate.bin)) return candidate;
	}
	return null;
}

function resolveSoundFile(): string {
	const override = process.env.PI_DONE_SOUND_FILE;
	if (override && existsSync(override)) return override;

	// Fallback chain across common sound themes (Linux + macOS).
	const candidates = isMacOS
		? [
				DEFAULT_SOUND_FILE,
				"/System/Library/Sounds/Hero.aiff",
				"/System/Library/Sounds/Ping.aiff",
				"/System/Library/Sounds/Submarine.aiff",
				"/System/Library/Sounds/Tink.aiff",
		]
		: [
				DEFAULT_SOUND_FILE,
				"/usr/share/sounds/Yaru/stereo/complete.oga",
				"/usr/share/sounds/freedesktop/stereo/bell.oga",
				"/usr/share/sounds/freedesktop/stereo/message.oga",
				"/usr/share/sounds/sound-icons/prompt.wav",
		];
	for (const c of candidates) {
		if (existsSync(c)) return c;
	}
	return DEFAULT_SOUND_FILE;
}

function spawnSilent(cmd: string, args: string[]): void {
	const child = execFile(
		cmd,
		args,
		{ timeout: 5000 },
		(err: ExecFileException | null) => {
			// Swallow errors: sound is best-effort. We do not want to surface
			// failures to the agent or the user as errors.
			if (err) {
				// Debug only:
				// console.error(`[done-sound] ${cmd} failed:`, err.message);
			}
		},
	);
	// Detach so the child does not keep the process alive / block anything.
	child.unref();
}

function playSound(player: { bin: string; args: string[] }, file: string): void {
	spawnSilent(player.bin, [...player.args, file]);
}

function playCustomCommand(command: string): void {
	// Split on whitespace (no shell to avoid injection surprises).
	const parts = command.trim().split(/\s+/).filter(Boolean);
	if (parts.length === 0) return;
	const [cmd, ...args] = parts;
	spawnSilent(cmd, args);
}

export default function (pi: ExtensionAPI) {
	let enabled = (process.env.PI_DONE_SOUND_ENABLED ?? "1") !== "0";

	// Resolve player + file lazily on first use so a missing player at startup
	// doesn't break the whole extension.
	let cachedPlayer: { bin: string; args: string[] } | null | undefined;
	const cachedFile = resolveSoundFile();

	function getPlayer(): { bin: string; args: string[] } | null {
		if (cachedPlayer === undefined) cachedPlayer = detectPlayer();
		return cachedPlayer;
	}

	function trigger(): void {
		if (!enabled) return;

		if (process.env.PI_DONE_SOUND_CMD) {
			playCustomCommand(process.env.PI_DONE_SOUND_CMD);
			return;
		}

		const player = getPlayer();
		if (!player) {
			// No player available; silently skip.
			return;
		}
		playSound(player, cachedFile);
	}

	// The main hook: fire when the agent has truly settled.
	pi.on("agent_settled", async (_event, ctx) => {
		// Skip in non-interactive print mode where "done" isn't meaningful
		// to a human waiting at the keyboard.
		if (ctx.mode === "print") return;
		trigger();
	});

	// Register a command to test / toggle.
	pi.registerCommand("done-sound", {
		description: "Play the done sound, or toggle it on/off (`/done-sound on|off|status`)",
		handler: async (args, ctx) => {
			const arg = (args ?? "").trim().toLowerCase();
			if (arg === "off" || arg === "disable") {
				enabled = false;
				ctx.ui.notify("Done sound: disabled", "info");
			} else if (arg === "on" || arg === "enable") {
				enabled = true;
				ctx.ui.notify("Done sound: enabled", "info");
			} else if (arg === "status") {
				const player = getPlayer();
				const via = process.env.PI_DONE_SOUND_CMD
					? `custom command: ${process.env.PI_DONE_SOUND_CMD}`
					: player
						? `player: ${player.bin}`
						: "no player found";
				ctx.ui.notify(
					`Done sound: ${enabled ? "enabled" : "disabled"} | file: ${cachedFile} | ${via}`,
					"info",
				);
			} else {
				// No arg: play a test sound.
				trigger();
			}
		},
	});
}
