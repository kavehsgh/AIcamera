import json


class ConfigHandler:
    def __init__(self, config_path):
        with open(config_path, "r") as file:
            self.config = json.load(file)

    def get(self, key, default=None):
        return self.config.get(key, default)
