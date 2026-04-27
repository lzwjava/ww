import re
import subprocess
import time


CHECK_INTERVAL = 10
NOT_CHARGING_CONFIRM_TICKS = 3  # require 3 consecutive checks (~30s) before alerting


def _pmset_output():
    result = subprocess.run(["pmset", "-g", "batt"], capture_output=True, text=True)
    return result.stdout


def _parse_status(pmset_output):
    lines = pmset_output.strip().splitlines()
    power_source = "Unknown"
    charging_state = "unknown"
    percent = -1

    for line in lines:
        if "AC Power" in line:
            power_source = "AC Power"
        elif "Battery Power" in line:
            power_source = "Battery Power"

        if "not charging" in line.lower():
            charging_state = "not charging"
        elif "discharging" in line.lower():
            charging_state = "discharging"
        elif "charging" in line.lower():
            charging_state = "charging"
        elif "finishing charge" in line.lower():
            charging_state = "charging"

        match = re.search(r"(\d+)%", line)
        if match:
            percent = int(match.group(1))

    return {
        "power_source": power_source,
        "charging_state": charging_state,
        "percent": percent,
    }


def _notify(title, message):
    script = f'display notification "{message}" with title "{title}" sound name "Basso"'
    subprocess.run(["osascript", "-e", script])


def _alert_state(status):
    if (
        status["power_source"] == "AC Power"
        and status["charging_state"] == "not charging"
    ):
        return "not_charging"
    elif status["power_source"] == "AC Power":
        return "charging"
    else:
        return "battery"


def main():
    print(f"Charge watcher started. Checking every {CHECK_INTERVAL}s. Ctrl+C to stop.")
    last_alerted_state = None
    not_charging_ticks = 0

    while True:
        try:
            status = _parse_status(_pmset_output())
            state = _alert_state(status)
            pct = status["percent"]

            print(
                f"[{time.strftime('%H:%M:%S')}] {status['power_source']} | "
                f"{pct}% | {status['charging_state']}"
            )

            if state == "not_charging":
                not_charging_ticks = not_charging_ticks + 1
                if (
                    not_charging_ticks >= NOT_CHARGING_CONFIRM_TICKS
                    and last_alerted_state != "not_charging"
                ):
                    _notify(
                        "Charger connected but NOT charging",
                        f"Battery at {pct}%. Check your power socket.",
                    )
                    last_alerted_state = "not_charging"
            else:
                if state == "charging" and last_alerted_state == "not_charging":
                    _notify("Charging resumed", f"Battery at {pct}%.")
                not_charging_ticks = 0
                last_alerted_state = state

            time.sleep(CHECK_INTERVAL)

        except KeyboardInterrupt:
            print("\nStopped.")
            return
