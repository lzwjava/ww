import requests
import argparse


def request_url_with_proxy(url, proxy):
    try:
        response = requests.get(url, proxies=proxy, timeout=10)
        response.raise_for_status()
        return response
    except requests.RequestException as e:
        print(f"An error occurred: {e}")
        return None


def main():
    parser = argparse.ArgumentParser(description="Make an HTTP GET request via proxy.")
    parser.add_argument("url", help="URL to fetch")
    parser.add_argument("--proxy", help="Proxy URL (e.g. http://127.0.0.1:7890)")
    args = parser.parse_args()

    proxy = {"http": args.proxy, "https": args.proxy} if args.proxy else {}
    response = request_url_with_proxy(args.url, proxy)

    if response:
        print(f"Status Code: {response.status_code}")
        print(f"Content: {response.text[:100]}...")
