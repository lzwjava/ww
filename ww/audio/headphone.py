"""Headphone test command.

Usage: ww headphone

Lists currently connected audio output/input devices,
plays a short test tone, then records audio from the microphone
and plays it back to verify headphone/mic functionality.
"""

import argparse
import math
import struct

import pyaudio

# Audio settings
CHUNK = 1024
FORMAT = pyaudio.paInt16
CHANNELS = 1
RATE = 44100
RECORD_SECONDS = 4  # record duration for "speak something"
TEST_TONE_SECONDS = 1.5  # short test tone
TEST_TONE_FREQ = 440.0  # A4 note


def list_devices():
    """List all connected audio devices, highlighting headphones."""
    p = pyaudio.PyAudio()
    device_count = p.get_device_count()
    print(f"\n=== Audio Devices ({device_count} found) ===\n")

    default_output_idx = None
    default_input_idx = None
    try:
        default_output_idx = p.get_default_output_device_info()["index"]
    except Exception:
        pass
    try:
        default_input_idx = p.get_default_input_device_info()["index"]
    except Exception:
        pass

    headphones_found = []
    speakers_found = []
    microphones_found = []

    for i in range(device_count):
        info = p.get_device_info_by_index(i)
        name = info["name"]
        max_inputs = int(info["maxInputChannels"])
        max_outputs = int(info["maxOutputChannels"])
        is_default_output = i == default_output_idx
        is_default_input = i == default_input_idx

        prefix = "  "
        if is_default_output and is_default_input:
            prefix = "★ "  # Default both
        elif is_default_output:
            prefix = "▶ "  # Default output
        elif is_default_input:
            prefix = "🎤 "  # Default input

        direction = []
        if max_outputs > 0:
            direction.append(f"Output ({max_outputs} ch)")
        if max_inputs > 0:
            direction.append(f"Input ({max_inputs} ch)")
        direction_str = ", ".join(direction) if direction else "No active channels"

        print(f"  {prefix}[{i}] {name}")
        print(f"       Type: {direction_str}")
        if is_default_output:
            print("       → Default Output Device")
        if is_default_input:
            print("       → Default Input Device")
        print()

        # Categorize
        is_headphone = "headphone" in name.lower() or "耳机" in name.lower()
        is_speaker = "speaker" in name.lower() or "扬声器" in name.lower()
        is_microphone = (
            "microphone" in name.lower()
            or "麦克风" in name.lower()
            or "mic" in name.lower()
        )

        if max_outputs > 0:
            if is_headphone or "headphone" in name.lower():
                headphones_found.append((i, name, is_default_output))
            elif is_speaker or "speaker" in name.lower():
                speakers_found.append((i, name, is_default_output))
            else:
                if max_inputs > 0:
                    microphones_found.append((i, name, is_default_input))
                else:
                    headphones_found.append((i, name, is_default_output))

        if max_inputs > 0 and max_outputs == 0:
            microphones_found.append((i, name, is_default_input))

    p.terminate()

    # Summary
    print("=== Summary ===\n")
    for idx, name, is_def in headphones_found:
        tag = " (default)" if is_def else ""
        print(f"  🎧  Headphone: [{idx}] {name}{tag}")
    for idx, name, is_def in speakers_found:
        tag = " (default)" if is_def else ""
        print(f"  🔊  Speaker: [{idx}] {name}{tag}")
    for idx, name, is_def in microphones_found:
        tag = " (default)" if is_def else ""
        print(f"  🎤  Microphone: [{idx}] {name}{tag}")

    return len(headphones_found), default_output_idx


def generate_test_tone(
    frequency=TEST_TONE_FREQ,
    duration=TEST_TONE_SECONDS,
    sample_rate=RATE,
    volume=0.5,
):
    """Generate a sine wave test tone."""
    num_samples = int(sample_rate * duration)
    samples = []
    for i in range(num_samples):
        sample_val = int(
            volume * 32767 * math.sin(2 * math.pi * frequency * i / sample_rate)
        )
        packed = struct.pack("<h", sample_val)
        samples.append(packed)
    return b"".join(samples)


def play_test_tone(output_device_index=None):
    """Play a short test tone to verify audio output."""
    print(f"\n=== Playing Test Tone ({TEST_TONE_FREQ}Hz, {TEST_TONE_SECONDS}s) ===\n")

    p = pyaudio.PyAudio()

    try:
        tone_data = generate_test_tone()

        stream_kwargs = {
            "format": FORMAT,
            "channels": 1,
            "rate": RATE,
            "output": True,
            "frames_per_buffer": CHUNK,
        }
        if output_device_index is not None:
            stream_kwargs["output_device_index"] = output_device_index

        stream = p.open(**stream_kwargs)
        print("  🔈 Playing tone... (you should hear a beep)")

        # Write in chunks
        for i in range(0, len(tone_data), CHUNK * 2):
            chunk = tone_data[i : i + CHUNK * 2]
            if chunk:
                stream.write(chunk)

        stream.stop_stream()
        stream.close()
        print("  ✅ Playback complete")
    except Exception as e:
        print(f"  ❌ Failed to play audio: {e}")
    finally:
        p.terminate()


def record_and_playback(output_device_index=None, input_device_index=None):
    """Record audio from microphone, then play it back."""
    print(f"\n=== Recording ({RECORD_SECONDS}s) ===")
    print("  🎤 Speak something now...\n")

    p = pyaudio.PyAudio()

    try:
        input_kwargs = {
            "format": FORMAT,
            "channels": CHANNELS,
            "rate": RATE,
            "input": True,
            "frames_per_buffer": CHUNK,
        }
        if input_device_index is not None:
            input_kwargs["input_device_index"] = input_device_index

        stream = p.open(**input_kwargs)
        frames = []

        for _ in range(0, int(RATE / CHUNK * RECORD_SECONDS)):
            data = stream.read(CHUNK, exception_on_overflow=False)
            frames.append(data)

        stream.stop_stream()
        stream.close()
        print("  ✅ Recording finished!\n")

        # Play back what was recorded
        print("=== Playback ===")
        print("  🔈 Playing back your recording...\n")

        output_kwargs = {
            "format": FORMAT,
            "channels": CHANNELS,
            "rate": RATE,
            "output": True,
            "frames_per_buffer": CHUNK,
        }
        if output_device_index is not None:
            output_kwargs["output_device_index"] = output_device_index

        stream = p.open(**output_kwargs)
        for frame in frames:
            stream.write(frame)

        stream.stop_stream()
        stream.close()
        print("  ✅ Playback complete")
        print("\n  ✨ If you heard your own voice, your headphone & mic are working!")

    except Exception as e:
        print(f"  ❌ Audio error: {e}")
    finally:
        p.terminate()


def main():
    """Entry point for ww headphone."""
    parser = argparse.ArgumentParser(
        description=(
            "Test headphone/audio devices: list devices,"
            " play test tone, record and playback."
        )
    )
    parser.add_argument(
        "--list-only",
        action="store_true",
        help="Only list audio devices, skip test tone and recording",
    )
    parser.add_argument(
        "--output-device",
        type=int,
        default=None,
        help="Output device index to use (default: system default)",
    )
    parser.add_argument(
        "--input-device",
        type=int,
        default=None,
        help="Input device index to use (default: system default)",
    )
    args = parser.parse_args()

    print("🔊 WW Headphone Test")
    print("=" * 50)

    # Step 1: List devices
    list_devices()

    if args.list_only:
        return

    # Step 2: Play a short test tone
    play_test_tone(output_device_index=args.output_device)

    # Step 3: Record and playback
    record_and_playback(
        output_device_index=args.output_device,
        input_device_index=args.input_device,
    )

    print("\n" + "=" * 50)
    print("✅ Headphone test completed!")
    print("=" * 50)


if __name__ == "__main__":
    main()
