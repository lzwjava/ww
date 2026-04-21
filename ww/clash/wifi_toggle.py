import subprocess


def turn_off_wifi():
    """Turns off Wi-Fi on macOS."""
    command = ["networksetup", "-setairportpower", "Wi-Fi", "off"]

    try:
        # run the command, capture output and check for errors
        result = subprocess.run(command, capture_output=True, text=True, check=True)
        print("Wi-Fi successfully turned off.")
        # print("STDOUT:", result.stdout) # Uncomment to see command output
        # print("STDERR:", result.stderr) # Uncomment to see error messages
    except subprocess.CalledProcessError as e:
        print(f"Error turning off Wi-Fi: {e}")
        print(f"Command: {' '.join(e.cmd)}")
        print(f"STDOUT: {e.stdout}")
        print(f"STDERR: {e.stderr}")
    except FileNotFoundError:
        print("Error: 'networksetup' command not found. Make sure it's in your PATH.")
    except Exception as e:
        print(f"An unexpected error occurred: {e}")


def turn_on_wifi():
    """Turns on Wi-Fi on macOS."""
    command = ["sudo", "networksetup", "-setairportpower", "Wi-Fi", "on"]

    try:
        result = subprocess.run(command, capture_output=True, text=True, check=True)
        print("Wi-Fi successfully turned on.")
    except subprocess.CalledProcessError as e:
        print(f"Error turning on Wi-Fi: {e}")
        print(f"Command: {' '.join(e.cmd)}")
        print(f"STDOUT: {e.stdout}")
        print(f"STDERR: {e.stderr}")
    except FileNotFoundError:
        print("Error: 'networksetup' command not found. Make sure it's in your PATH.")
    except Exception as e:
        print(f"An unexpected error occurred: {e}")


def main():
    import argparse

    parser = argparse.ArgumentParser(description="Toggle Wi-Fi on macOS")
    parser.add_argument("action", choices=["on", "off"], help="Turn Wi-Fi on or off")
    args = parser.parse_args()

    if args.action == "on":
        turn_on_wifi()
    else:
        turn_off_wifi()


if __name__ == "__main__":
    main()
