# Design: `ww gen-image`

**Date:** 2026-05-05
**Status:** Approved

## Overview

A new top-level `ww gen-image` command that reads a text prompt from the macOS clipboard and generates an image using Google's Imagen 3 API, saving the result as a PNG file.

## Architecture

Single flat command group `gen-image` in `main.py`, implemented in `ww/image/gen_image.py`.

```
main()
  ├── parse args (--output, --model)
  ├── read_clipboard() → pbpaste → prompt text
  ├── generate_image(prompt, model) → PNG bytes
  └── save_image(bytes, output_path) → prints saved path
```

## Components

### `ww/image/gen_image.py`

- `read_clipboard() -> str` — uses `pyperclip.paste()`, returns stripped text; exits 1 if empty
- `generate_image(prompt: str, model: str) -> bytes` — calls Google Generative AI SDK (`google-genai`), returns raw PNG bytes
- `save_image(data: bytes, path: str) -> None` — writes bytes to file, prints path
- `main()` — argparse entry point

### `main.py`

Add `elif group == "gen-image"` dispatch block and one help line.

### `pyproject.toml`

Add `google-genai>=1.0.0` to dependencies.

## CLI Interface

```
ww gen-image                                   # saves ./gen-image-<timestamp>.png
ww gen-image --output ~/Desktop/result.png     # custom output path
ww gen-image --model imagen-3.0-generate-002   # explicit model (this is the default)
```

## Configuration

- `GEMINI_API_KEY` in `.env` — required; error message on missing
- Default model: `imagen-3.0-generate-002`
- Default output: `./gen-image-<timestamp>.png` (timestamp = `YYYYMMDD-HHMMSS`)

## Error Handling

| Condition | Behavior |
|-----------|----------|
| Empty clipboard | Print error, exit 1 |
| `GEMINI_API_KEY` not set | Print error, exit 1 |
| API failure | Print error message from SDK, exit 1 |
| Output path unwritable | Catch `OSError`, print clean error message, exit 1 |

## Dependencies

- `google-genai>=1.0.0` (new)
- `python-dotenv` (already present — loads `.env`)
