#!/usr/bin/env python3
"""Query the result of a previously submitted GCP Speech-to-Text job."""

import json
import os
import sys
import tempfile

from google.cloud import storage

from ww.gcp_speech.transcribe import PROJECT_ID, BUCKET_NAME, _extract_transcript

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


def _print_help():
    print("Usage: ww gcp-speech result <job-id> [--wait]")
    print()
    print("Query the result of a previously submitted transcription job.")
    print()
    print("Arguments:")
    print("  <job-id>      The job ID returned by `ww gcp-speech transcribe`")
    print("  --wait        Wait for the job to complete and download the transcript")
    print()
    print("Examples:")
    print("  ww gcp-speech transcribe ~/Downloads/recording.mp3")
    print("  ww gcp-speech result <job-id>")
    print("  ww gcp-speech result <job-id> --wait")


def main():
    args = sys.argv[1:]
    if not args or args[0] in ("--help", "-h"):
        _print_help()
        return

    job_id = None
    wait = False
    i = 0
    while i < len(args):
        if args[i] == "--wait":
            wait = True
            i += 1
        else:
            job_id = args[i]
            i += 1

    if not job_id:
        print("Error: No job ID provided.")
        sys.exit(1)

    jobs = _load_jobs()
    job = jobs.get(job_id)
    if not job:
        print(f"Error: Unknown job ID: {job_id}")
        print()
        print("Run `ww gcp-speech transcribe` to submit a new job.")
        sys.exit(1)

    gcs_output_prefix = job["gcs_output_prefix"]
    gcs_output_folder = f"gs://{BUCKET_NAME}/{gcs_output_prefix}"
    operation_name = job.get("operation_name", "unknown")
    audio_file = job.get("audio_file", "unknown")
    language_code = job.get("lang", "en-US")

    print(f"Job ID:   {job_id}")
    print(f"File:     {audio_file}")
    print(f"Language: {language_code}")
    print(f"Operation: {operation_name}")
    print(f"Output:   {gcs_output_folder}/")
    print()

    storage_client = storage.Client()
    bucket = storage_client.bucket(BUCKET_NAME)
    blobs = list(bucket.list_blobs(prefix=gcs_output_prefix))
    json_blobs = [b for b in blobs if b.name.endswith(".json")]

    if not json_blobs:
        print("Results not available yet. The job is still processing.")
        console_url = (
            f"https://console.cloud.google.com/storage/browser/{BUCKET_NAME}/{gcs_output_prefix}"
            f"?project={PROJECT_ID}"
        )
        print(f"Console: {console_url}")
        if not wait:
            print()
            print("Re-run with --wait to poll until complete:")
            print(f"  ww gcp-speech result {job_id} --wait")
            return
        print()
        print("Waiting for transcription to complete...")
        import time

        while True:
            blobs = list(bucket.list_blobs(prefix=gcs_output_prefix))
            json_blobs = [b for b in blobs if b.name.endswith(".json")]
            if json_blobs:
                break
            time.sleep(10)
        print("Recognition complete.")
        print()

    output_dir = tempfile.mkdtemp(prefix="ww_gcp_result_")
    downloaded = []
    for blob in json_blobs:
        local_path = os.path.join(output_dir, os.path.basename(blob.name))
        blob.download_to_filename(local_path)
        downloaded.append(local_path)

    if not downloaded:
        print("Error: No transcription results found in GCS output.")
        sys.exit(1)

    # Print all transcripts
    for json_path in downloaded:
        transcript = _extract_transcript(json_path)
        if transcript:
            print("=" * 60)
            print("TRANSCRIPT")
            print("=" * 60)
            print(transcript)
            print()

    # Save transcript to a markdown file alongside the audio
    basename = os.path.splitext(os.path.basename(audio_file))[0]
    output_path = os.path.join(
        os.path.dirname(os.path.abspath(audio_file)), f"{basename}.md"
    )
    # Combine all transcripts into one
    all_transcripts = []
    for json_path in downloaded:
        t = _extract_transcript(json_path)
        if t:
            all_transcripts.append(t)
    combined = "\n\n".join(all_transcripts)

    if combined:
        with open(output_path, "w", encoding="utf-8") as f:
            f.write(f"# Transcript: {os.path.basename(audio_file)}\n\n")
            f.write(f"**Source:** `{audio_file}`\n")
            f.write(f"**Language:** {language_code}\n\n")
            f.write("---\n\n")
            f.write(combined)
            f.write("\n")
        print(f"Transcript saved: {output_path}")
