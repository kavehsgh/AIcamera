import serial
import pynmea2
from geopy.distance import geodesic
from datetime import datetime
import time
import requests
import threading
import math
import logging
from config_handler import ConfigHandler

config = ConfigHandler("config.json")


class GPSHandler:
    def __init__(self, config=config):
        self.serial_port = config.get("serial_port", "/dev/ttyACM0")
        self.backend_url = config.get("backend_url")
        self.gps_publish_rate = config.get("gps_publish_rate", 10.0)
        self.last_location = None
        self.last_time = None  # Ensure reset location and time
        self.last_gps_publish_time = None
        self.logger = logging.getLogger(__name__)
        self.car_detected = False
        self.latest_gps_data = None

    def calculate_initial_compass_bearing(self, point_a, point_b):
        """
        Calculates the bearing between two points.
        The formula used to calculate the initial bearing is:
            θ = atan2(sin(Δlong).cos(lat2),
                    cos(lat1).sin(lat2) − sin(lat1).cos(lat2).cos(Δlong))

        Parameters:
        point_a : tuple : (latitude, longitude) of the first point
        point_b : tuple : (latitude, longitude) of the second point

        Returns:
        bearing : float : initial compass bearing in degrees
        """
        if point_a == point_b:
            return 0.0

        lat1 = math.radians(point_a[0])
        lat2 = math.radians(point_b[0])
        diff_long = math.radians(point_b[1] - point_a[1])

        x = math.sin(diff_long) * math.cos(lat2)
        y = math.cos(lat1) * math.sin(lat2) - (
            math.sin(lat1) * math.cos(lat2) * math.cos(diff_long)
        )

        initial_bearing = math.atan2(x, y)
        # Convert radians to degrees
        initial_bearing = math.degrees(initial_bearing)
        # Normalize the bearing
        compass_bearing = (initial_bearing + 360) % 360

        return compass_bearing

    def publish_gps_data(self, msg, velocity, heading):
        data = {
            "camera_name": "100",
            "foxtow_id": "PETRO",
            "date": f'{datetime.now().date().strftime("%Y/%m/%d")}',
            "time": int(datetime.now().timestamp()),
            "lat": msg.latitude,
            "lon": msg.longitude,
            "heading": heading,
            "velocity": velocity,
            "car_detected": self.car_detected,
        }
        self.logger.info(f"Publishing GPS data: {data}")
        x = requests.post(self.backend_url, json=data, verify=False)
        self.logger.info(f"Response: {x.text}")
        self.last_gps_publish_time = time.time()

    def read_gps_data(self):
        # Set serial port name and timeout time
        ser = serial.Serial(self.serial_port, timeout=1)
        self.logger.info("GPS reading loop started.")
        while True:
            # Read data and parse data message
            data = ser.readline()
            if data.startswith(b"$GNGGA"):
                msg = pynmea2.parse(data.decode("utf-8"))
                # Assign current location and time
                current_location = (msg.latitude, msg.longitude)
                current_time = datetime.now()

                # If location and time exist, calculate velocity and heading
                if self.last_location and self.last_time:
                    distance = geodesic(self.last_location, current_location).meters
                    time_difference = (current_time - self.last_time).total_seconds()
                    velocity = (
                        distance / time_difference if time_difference > 0 else 0.0
                    )
                    heading = self.calculate_initial_compass_bearing(
                        self.last_location, current_location
                    )

                    if self.last_gps_publish_time:
                        elapsed_time = time.time() - self.last_gps_publish_time
                        if elapsed_time > self.gps_publish_rate:
                            self.publish_gps_data(msg, velocity, heading)
                    else:
                        self.publish_gps_data(msg, velocity, heading)

                # Store the latest GPS data
                self.latest_gps_data = {"lat": msg.latitude, "lon": msg.longitude}

                self.last_location = current_location
                self.last_time = current_time

    def get_latest_gps_data(self):
        return self.latest_gps_data

    def start(self):
        threading.Thread(target=self.read_gps_data).start()
