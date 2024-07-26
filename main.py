import logging
from gps_handler import GPSHandler
from camera_handler import CameraHandler
from config_handler import ConfigHandler

# Set up logging
logging.basicConfig(level=logging.INFO)

config = ConfigHandler("config.json")

gps_handler = GPSHandler(config)
camera_handler = CameraHandler(config, gps_handler)

# Start the handlers
gps_handler.start()
camera_handler.start()
