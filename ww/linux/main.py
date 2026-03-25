import sys


def _pop_subcmd():
    if len(sys.argv) > 1:
        return sys.argv.pop(1)
    return ""


def _print_help():
    print("Usage: ww linux <command> [options]")
    print("\nCommands:")
    print("  gpu          Show GPU and CUDA details")
    print("  system       Comprehensive system overview")
    print("  disk         Show disk usage")
    print("  battery      Show battery status")
    print("  proxy-setup  Interactively configure APT proxy")
    print("  wol          Send a Wake-on-LAN packet")
    print("  terminal     Open a fullscreen terminal")


def main():
    subcmd = _pop_subcmd()
    if subcmd in ("--help", "-h", "help", ""):
        _print_help()
        return

    if subcmd == "gpu":
        from ww.linux.gpu import run

        run()
    elif subcmd == "system":
        from ww.linux.system import run

        run()
    elif subcmd == "disk":
        from ww.linux.disk import run

        run()
    elif subcmd == "battery":
        from ww.linux.battery import run

        run()
    elif subcmd == "proxy-setup":
        from ww.linux.setup import run_proxy_setup

        run_proxy_setup()
    elif subcmd == "wol":
        from ww.linux.net import run_wol

        run_wol()
    elif subcmd == "terminal":
        from ww.linux.terminal import run

        run()
    else:
        print(f"Unknown linux command: {subcmd}")
        sys.exit(1)
