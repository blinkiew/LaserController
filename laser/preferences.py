import json
import os
import warnings
from typing import Sequence, Dict, Any

from laser.zone import Zone


class PreferencesManager:
    def __init__(self, preferences_path: str):
        self.path = preferences_path

    def save_zones(self, zones: Sequence[Zone]):
        """
        Saves zone classes.
        :param zones: One or more Zone objects to save.
        """

        if not zones:
            warnings.warn("No zones to save.", UserWarning)
            return

        # make a file structure
        zones_dict = {
            "zones": {
                f"zone_{i}": {
                    "threshold": zone.threshold,
                    "markers": zone.markers
                } for i, zone in enumerate(zones, start=1)
            }
        }

        try:
            with open(self.path, 'w', encoding='utf-8') as file:
                json.dump(zones_dict, file, ensure_ascii=False, indent=4)
        except (IOError, TypeError) as e:
            warnings.warn(f"Failed to save zones: {str(e)}", UserWarning)

    def read_zones(self):
        """
        Reads zones from a JSON file, using default settings if the file does not exist.
        :return: A list of zones, each represented as a dictionary.
        """

        read_from = self.path
        if not os.path.exists(read_from):
            current_dir = os.path.dirname(os.path.abspath(__file__))
            json_path = os.path.join(current_dir, "default_zones_settings.json")

            if os.path.exists(json_path):
                warnings.warn(f"No settings file at provided directory: {os.path.abspath(self.path)}. "
                              f"Using the defaults. A new settings file will be created there.", UserWarning)
                read_from = json_path
            else:
                raise FileNotFoundError(f"Neither provided path nor default path contains settings file.")

        with open(read_from, 'r', encoding='utf-8') as file:
            loaded_zones = json.load(file).get("zones", {})
            return [{**value, "id": key} for key, value in loaded_zones.items()]
