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


def _submit_job(audio_gcs_uri, output_gcs_folder, language_code):
    """Submit a batch recognize job and return the operation name."""
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

    operation = client.batch_recognize(request=request)
    return operation.operation.name


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


JOBS_FILE = os.path.expanduser("~/.config/ww/gcp_jobs.json")


def _load_jobs():
    if not os.path.isfile(JOBS_FILE):
        return {}
    with open(JOBS_FILE, "r") as f:
        return json.load(f)


def _save_jobs(jobs):
    os.makedirs(os.path.dirname(JOBS_FILE), exist_ok=True)
    with open(JOBS_FILE, "w") as f:
        json.dump(jobs, f, indent=2)


def _save_job_info(operation_name, gcs_output_prefix, audio_file, language_code):
    """Save job info to local registry keyed by basename."""
    import time

    basename = os.path.splitext(os.path.basename(audio_file))[0]
    jobs = _load_jobs()
    jobs[basename] = {
        "operation_name": operation_name,
        "gcs_output_prefix": gcs_output_prefix,
        "audio_file": audio_file,
        "lang": language_code,
        "timestamp": time.time(),
    }
    _save_jobs(jobs)


def _print_help():
    print("Usage: ww gcp-speech transcribe <audio_file> [options]")
    print()
    print("Transcribe a local audio file via Google Cloud Speech-to-Text.")
    print()
    print("Arguments:")
    print("  <audio_file>   Path to audio file (mp3, m4a, wav, ogg, mp4, etc.)")
    print("  --lang LANG    Language code (default: auto-detect from filename)")
    print("                 e.g. en-US, cmn-Hans-CN, ja-JP")
    print("  --wait         Wait for transcription to complete and download results")
    print("                 (default: async — submit job, print console link, exit)")
    print()
    print("Examples:")
    print("  ww gcp-speech transcribe ~/Downloads/recording.mp3")
    print("  ww gcp-speech transcribe ~/Downloads/recording-zh.mp3 --lang cmn-Hans-CN")
    print("  ww gcp-speech transcribe ~/Downloads/long.mp3 --wait")


def main():
    args = sys.argv[1:]
    if not args or args[0] in ("--help", "-h"):
        _print_help()
        return

    audio_file = None
    lang = None
    wait = False
    i = 0
    while i < len(args):
        if args[i] == "--lang" and i + 1 < len(args):
            lang = args[i + 1]
            i += 2
        elif args[i] == "--wait":
            wait = True
            i += 1
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

    language_code = lang or _detect_language(filename)

    print(f"File: {audio_file}")
    print(f"Language: {language_code}")

    # GCS paths
    gcs_audio_path = f"audio-files/{filename}"
    gcs_audio_uri = f"gs://{BUCKET_NAME}/{gcs_audio_path}"
    gcs_output_prefix = f"transcripts/{basename}"
    gcs_output_folder = f"gs://{BUCKET_NAME}/{gcs_output_prefix}"

    # Upload to GCS
    _upload_to_gcs(audio_file, gcs_audio_path)

    # Submit job
    operation_name = _submit_job(gcs_audio_uri, gcs_output_folder, language_code)

    # Console link
    console_url = (
        f"https://console.cloud.google.com/storage/browser/{BUCKET_NAME}/{gcs_output_prefix}"
        f"?project={PROJECT_ID}"
    )
    print()
    print("=" * 60)
    print("JOB SUBMITTED")
    print("=" * 60)
    print(f"Job ID:    {basename}")
    print(f"Operation: {operation_name}")
    print(f"Output:    gs://{BUCKET_NAME}/{gcs_output_prefix}/")
    print(f"Console:   {console_url}")
    print()

    # Save to local jobs registry so `ww gcp-speech result <id>` can find it
    _save_job_info(operation_name, gcs_output_prefix, audio_file, language_code)
    print()

    print("Once complete, use:")
    print(f"  ww gcp-speech result {basename} --wait")
    print("=" * 60)

    if not wait:
        return

    # --wait mode: block until done, download, print transcript
    # Poll GCS for results instead of waiting on the operation
    print()
    print("Waiting for transcription to complete...")
    storage_client = storage.Client()
    bucket = storage_client.bucket(BUCKET_NAME)
    import time

    while True:
        blobs = list(bucket.list_blobs(prefix=gcs_output_prefix))
        json_blobs = [b for b in blobs if b.name.endswith(".json")]
        if json_blobs:
            break
        time.sleep(10)

    print("Recognition complete.")

    output_dir = tempfile.mkdtemp(prefix="ww_gcp_transcribe_")
    result_files = _download_results(gcs_output_folder, output_dir)

    if not result_files:
        print("Error: No transcription results found in GCS output.")
        sys.exit(1)

    transcript = _extract_transcript(result_files[0])

    print()
    print("=" * 60)
    print("TRANSCRIPT")
    print("=" * 60)
    print(transcript)
    print()
    print("=" * 60)

    output_path = os.path.join(
        os.path.dirname(os.path.abspath(audio_file)), f"{basename}.md"
    )
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
