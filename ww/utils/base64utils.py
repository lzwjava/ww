import base64
import argparse


def main():
    parser = argparse.ArgumentParser(description="Encode or decode a Base64 string.")
    parser.add_argument("text", help="String to encode")
    args = parser.parse_args()

    sample_bytes = args.text.encode("utf-8")
    encoded_bytes = base64.b64encode(sample_bytes)
    encoded_string = encoded_bytes.decode("utf-8")
    print("Encoded string:", encoded_string)

    decoded_bytes = base64.b64decode(encoded_bytes)
    decoded_string = decoded_bytes.decode("utf-8")
    print("Decoded string:", decoded_string)
