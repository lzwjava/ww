import getpass
import subprocess


def run_proxy_setup():
    """Interactively configure APT proxy settings."""
    # Get proxy details from user
    proxy_host = input("Enter proxy host (e.g., 127.0.0.1): ").strip()
    proxy_port = input("Enter proxy port (e.g., 7890): ").strip()

    # Optional authentication
    use_auth = input("Use authentication? (y/n): ").strip().lower()
    if use_auth == "y":
        username = input("Enter username: ").strip()
        password = getpass.getpass("Enter password: ").strip()
        auth_part = f"{username}:{password}@"
    else:
        auth_part = ""

    # Build proxy URL
    proxy_url = f"http://{auth_part}{proxy_host}:{proxy_port}"

    # Config content
    config_content = f"""Acquire::http::Proxy "{proxy_url}";
Acquire::https::Proxy "{proxy_url}";
Acquire::ftp::Proxy "{proxy_url}";  # Optional for FTP
"""

    # Write to file using sudo tee (echo content | sudo tee file)
    cmd = f"echo '{config_content}' | sudo tee /etc/apt/apt.conf.d/10proxy > /dev/null"
    try:
        subprocess.run(cmd, shell=True, check=True, capture_output=True, text=True)
        print("APT proxy config created successfully at /etc/apt/apt.conf.d/10proxy")
        print("Run 'sudo apt update' to test.")
    except subprocess.CalledProcessError as e:
        print(f"Error creating config: {e}")


def run_linux_setup():
    """General Linux setup tasks (ported from setup.py)."""
    print("Running Linux setup tasks...")
    # Ported from setup.py comments
    cmd = "sudo apt install -y npm"
    try:
        subprocess.run(cmd, shell=True, check=True)
        print("npm installed successfully.")
    except subprocess.CalledProcessError as e:
        print(f"Error installing npm: {e}")
