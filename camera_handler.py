import cv2
import depthai as dai
import threading
import numpy as np
from datetime import datetime
import logging
from detection_pipeline import setup_detection_pipeline
from data_storage import DataStorage
from time import monotonic
from picamera2 import Picamera2
from gps_handler import GPSHandler
from config_handler import ConfigHandler

config = ConfigHandler("config.json")


class CameraHandler:
    def __init__(self, config=config, gps_handler=GPSHandler()):
        self.car_detected = False
        self.label_map = config.get("label_map")
        self.min_bbox_size = config.get("min_bbox_size")
        self.camera_detection_rate = config.get("camera_detection_rate")
        self.stability_frames = config.get("stability_frames")
        self.video_path = config.get("video_path")
        self.model_path = config.get("model_path")
        self.dataset_path = config.get("dataset_path")
        self.logger = logging.getLogger(__name__)

        # Initialize DataStorage with GPSHandler
        self.data_storage = DataStorage(
            self.label_map,
            self.min_bbox_size,
            self.camera_detection_rate,
            self.stability_frames,
            gps_handler
        )
        self.data_storage.create_directories()
        self.picam2 = Picamera2()
        capture_config = self.picam2.create_still_configuration()
        self.picam2.configure(
            self.picam2.create_preview_configuration(main={"size": (1280, 720)})
        )
        self.picam2.start()

    def camera_operations(self):
        pipeline = dai.Pipeline()
        pipeline, xin_frame, nn_out = setup_detection_pipeline(
            pipeline, self.model_path, self.label_map
        )

        with dai.Device(pipeline) as device:
            dataset_file, dataset = self.data_storage.initialize_dataset(
                self.dataset_path
            )

            q_in = device.getInputQueue(name="inFrame")
            q_det = device.getOutputQueue(name="nn", maxSize=4, blocking=False)

            frame = None
            detections = []

            def to_planar(arr: np.ndarray, shape: tuple) -> np.ndarray:
                return cv2.resize(arr, shape).transpose(2, 0, 1).flatten()

            while True:
                frame = self.picam2.capture_array()

                img = dai.ImgFrame()
                img.setData(to_planar(frame, (300, 300)))
                img.setTimestamp(monotonic())
                img.setWidth(300)
                img.setHeight(300)
                q_in.send(img)

                in_det = q_det.tryGet()

                if in_det is not None:
                    detections = in_det.detections
                    if frame is not None:
                        self.data_storage.store_data(
                            frame,
                            detections,
                            dataset,
                            datetime.now().strftime("%Y-%m-%d_%I:%M:%S%p_%A"),
                            {"car"},
                        )
                # time.sleep(camera_detection_rate)

    def start(self):
        threading.Thread(target=self.camera_operations).start()
