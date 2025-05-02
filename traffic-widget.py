import datetime
import json
import os
import subprocess

import requests
from dotenv import load_dotenv


class TomTomAPI:
    """Encapsulates interactions with the TomTom Routing API."""

    BASE_URL = "https://api.tomtom.com/routing/1/calculateRoute"

    def __init__(self, api_key: str):
        """Initialize the TomTomAPI with the API key."""
        self.api_key = api_key

    def get_travel_time(
        self, start_lat: float, start_lon: float, end_lat: float, end_lon: float
    ) -> int | None:
        """Calculate the travel time between two points.

        Args:
            start_lat (float): Latitude of the starting point.
            start_lon (float): Longitude of the starting point.
            end_lat (float): Latitude of the destination point.
            end_lon (float): Longitude of the destination point.

        Returns:
            int: The travel time in seconds, or None if an error occurs.
        """
        start_point = f"{start_lat},{start_lon}"
        end_point = f"{end_lat},{end_lon}"
        url = f"{self.BASE_URL}/{start_point}:{end_point}/json?key={self.api_key}"

        try:
            response = requests.get(url)
            response.raise_for_status()
            data = response.json()
            travel_time_seconds = data["routes"][0]["summary"]["travelTimeInSeconds"]
            return travel_time_seconds

        except requests.exceptions.RequestException as e:
            print(f"TomTom API Error: {e}")
            return None
        except (json.JSONDecodeError, KeyError) as e:
            print(f"TomTom API Error: Invalid response format or missing data: {e}")
            return None


class WindowsNotifier:
    """Handles displaying Windows toast notifications."""

    def __init__(self, powershell_path: str, powershell_script: str):
        """Initialize the WindowsNotifier with the paths to PowerShell."""
        self.powershell_path = powershell_path
        self.powershell_script = powershell_script

    def show_notification(self, title: str, message: str):
        """Show a Windows toast notification.

        Args:
            title (str): The title of the notification.
            message (str): The body of the notification.
        """
        try:
            subprocess.run(
                [
                    self.powershell_path,
                    "-ExecutionPolicy",
                    "Bypass",
                    "-File",
                    self.powershell_script,
                    "-Title",
                    title,
                    "-Message",
                    message,
                ],
                check=True,
                capture_output=True,
                text=True,
            )
        except subprocess.CalledProcessError as e:
            print(f"Error showing notification: {e}")
            print(f"PowerShell Output:\n{e.stderr}")
        except FileNotFoundError:
            print(f"Error: PowerShell executable or script not found. Check the paths.")


def format_travel_time(label: str, travel_time: int | None) -> str:
    """Format the travel time into a readable string.

    Args:
        label (str): The label for the travel time (e.g., "Home", "Rowing").
        travel_time (int | None): The travel time in seconds, or None if an error occurred.

    Returns:
        str: The formatted travel time string.
    """
    now = datetime.datetime.now()
    arrival_time = (
        now + datetime.timedelta(seconds=travel_time) if travel_time else None
    )
    if travel_time is not None:
        return f"{label}: {travel_time / 60:.1f} minutes (arrive at {arrival_time.strftime('%H:%M')})"
    else:
        return f"{label}: ERROR minutes."


if __name__ == "__main__":
    load_dotenv()
    api_key = os.environ["API_KEY"]
    work_lat = float(os.environ["WORK_LATITUDE"])
    work_lon = float(os.environ["WORK_LONGITUDE"])
    home_lat = float(os.environ["HOME_LATITUDE"])
    home_lon = float(os.environ["HOME_LONGITUDE"])
    powershell_path = os.environ.get("POWERSHELL_PATH")
    powershell_script = os.environ.get("POWERSHELL_SCRIPT")
    if not powershell_script:
        print("Error: POWERSHELL_SCRIPT environment variable not set.")
        exit(1)

    tomtom_api = TomTomAPI(api_key)
    notifier = WindowsNotifier(powershell_path, powershell_script)

    home_travel_time = tomtom_api.get_travel_time(
        work_lat, work_lon, home_lat, home_lon
    )

    message_lines = [
        format_travel_time("Home", home_travel_time),
    ]
    notification_message = "\n".join(message_lines)

    notifier.show_notification("Driving times:", notification_message)
