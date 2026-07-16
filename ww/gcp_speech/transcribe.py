#!/usr/bin/env python3
"""Transcribe a local audio file via Google Cloud Speech-to-Text v2 Batch API."""

import json
import os
import sys
import tempfile

from google.cloud import storage
from google.cloud.speech_v2 import SpeechClient
from google.cloud.speech_v2.types import cloud_speech

PROJECT_ID = "graphite-ally-445108-k3"
BUCKET_NAME = "test2x"
MAX_AUDIO_LENGTH_SECS = 20 * 60 * 60


def _detect_language(filename):
    """Detect language from filename suffix."""
    base = os.path.splitext(filename)[0]
    if base.endswith("-zh") or base.endswith("-cn"):
        return "cmn-Hans-CN"
    return "en-US"


def _upload_to_gcs(local_path, gcs_path):
    """Upload a local file to GCS if it doesn't already exist."""
    storage_client = storage.Client()
    bucket = storage_client.bucket(BUCKET_NAME)
    blob = bucket.blob(gcs_path)
    if blob.exists():
        print(f"Already exists in GCS: gs://{BUCKET_NAME}/{gcs_path}")
        return True
    print(f"Uploading to gs://{BUCKET_NAME}/{gcs_path} ...")
    blob.upload_from_filename(local_path)
    print("Upload complete.")
    return True


def _run_batch_recognize(audio_gcs_uri, output_gcs_folder, language_code):
    """Run Google Cloud Speech-to-Text v2 batch recognize."""
    client = SpeechClient()

    config = cloud_speech.RecognitionConfig(
        auto_decoding_config=cloud_speech.AutoDetectDecodingConfig(),
        features=cloud_speech.RecognitionFeatures(
            enable_word_confidence=True,
            enable_word_time_offsets=True,
        ),
        language_codes=[language_code],
    )
    config.model = "long"

    output_config = cloud_speech.RecognitionOutputConfig(
        gcs_output_config=cloud_speech.GcsOutputConfig(uri=output_gcs_folder),
    )

    files = [cloud_speech.BatchRecognizeFileMetadata(uri=audio_gcs_uri)]

    request = cloud_speech.BatchRecognizeRequest(
        recognizer=f"projects/{PROJECT_ID}/locations/global/recognizers/_",
        config=config,
        files=files,
        recognition_output_config=output_config,
    )

    print("Waiting for Speech-to-Text to complete (this may take a while)...")
    operation = client.batch_recognize(request=request)
    response = operation.result(timeout=3 * MAX_AUDIO_LENGTH_SECS)
    print("Recognition complete.")


def _download_results(output_gcs_folder, output_dir):
    """Download transcription JSON results from GCS to local directory."""
    storage_client = storage.Client()
    prefix = output_gcs_folder.replace(f"gs://{BUCKET_NAME}/", "")
    blobs = list(storage_client.list_blobs(BUCKET_NAME, prefix=prefix))
    downloaded = []
    for blob in blobs:
        if blob.name.endswith(".json"):
            local_path = os.path.join(output_dir, os.path.basename(blob.name))
            blob.download_to_filename(local_path)
            downloaded.append(local_path)
            print(f"Downloaded: {local_path}")
    return downloaded


def _extract_transcript(json_path):
    """Extract transcript text from Google Cloud STT JSON."""
    with open(json_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    results = data.get("results", [])
    parts = []
    for result in results:
        for alt in result.get("alternatives", []):
            transcript = alt.get("transcript", "")
            if transcript:
                parts.append(transcript)

    return " ".join(parts)


def main():
    if len(sys.argv) < 2 or sys.argv[1] in ("--help", "-h"):
        print("Usage: ww gcp-speech transcribe <audio_file> [--lang LANG]")
        print()
        print("Transcribe a local audio file via Google Cloud Speech-to-Text.")
        print()
        print("Arguments:")
        print("  <audio_file>   Path to audio file (mp3, m4a, wav, ogg, mp4, etc.)")
        print("  --lang LANG    Language code (default: auto-detect from filename)")
        print("                 e.g. en-US, cmn-Hans-CN, ja-JP")
        print()
        print("Examples:")
        print("  ww gcp-speech transcribe ~/Downloads/recording.mp3")
        print("  ww gcp-speech transcribe ~/Downloads/recording-zh.mp3 --lang cmn-Hans-CN")
        return

    # Parse args
    args = sys.argv[1:]
    audio_file = None
    lang = None
    i = 0
    while i < len(args):
        if args[i] == "--lang" and i + 1 < len(args):
            lang = args[i + 1]
            i += 2
        else:
            audio_file = args[i]
            i += 1

    if not audio_file:
        print("Error: No audio file provided.")
        sys.exit(1)

    if not os.path.isfile(audio_file):
        print(f"Error: File not found: {audio_file}")
        sys.exit(1)

    filename = os.path.basename(audio_file)
    basename = os.path.splitext(filename)[0]

    if lang:
        language_code = lang
    else:
        language_code = _detect_language(filename)

    print(f"File: {audio_file}")
    print(f"Language: {language_code}")

    # GCS paths
    gcs_audio_path = f"audio-files/{filename}"
    gcs_audio_uri = f"gs://{BUCKET_NAME}/{gcs_audio_path}"
    gcs_output_folder = f"gs://{BUCKET_NAME}/transcripts/{basename}"

    # Upload to GCS
    _upload_to_gcs(audio_file, gcs_audio_path)

    # Run batch recognize
    _run_batch_recognize(gcs_audio_uri, gcs_output_folder, language_code)

    # Download results
    output_dir = tempfile.mkdtemp(prefix="ww_gcp_transcribe_")
    result_files = _download_results(gcs_output_folder, output_dir)

    if not result_files:
        print("Error: No transcription results found in GCS output.")
        sys.exit(1)

    # Extract transcript
    transcript = _extract_transcript(result_files[0])

    # Print transcript
    print()
    print("=" * 60)
    print("TRANSCRIPT")
    print("=" * 60)
    print(transcript)
    print()
    print("=" * 60)

    # Save to file alongside audio
    output_path = os.path.join(os.path.dirname(audio_file), f"{basename}.md")
    with open(output_path, "w", encoding="utf-8") as f:
        f.write(f"# Transcript: {filename}\n\n")
        f.write(f"**Source:** `{audio_file}`\n")
        f.write(f"**Language:** {language_code}\n\n")
        f.write("---\n\n")
        f.write(transcript)
        f.write("\n")
    print(f"Transcript saved: {output_path}")


if __name__ == "__main__":
    main()