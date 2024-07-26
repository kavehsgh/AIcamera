import cv2
import csv
import numpy as np
from pathlib import Path
import time
import logging
from gps_handler import GPSHandler


class DataStorage:
    def __init__(
        self,
        label_map,
        min_bbox_size,
        camera_detection_rate,
        stability_frames,
        gps_handler,
    ):
        self.label_map = label_map
        self.min_bbox_size = min_bbox_size
        self.camera_detection_rate = camera_detection_rate
        self.stability_frames = stability_frames
        self.last_detection_saved_time = None
        self.car_detected = False
        self.logger = logging.getLogger(__name__)
        self.detection_buffer = []
        self.gps_handler = GPSHandler()

    def frame_norm(self, frame, bbox):
        norm_vals = np.full(len(bbox), frame.shape[0])
        norm_vals[::2] = frame.shape[1]
        return (np.clip(np.array(bbox), 0, 1) * norm_vals).astype(int)

    def calculate_roi(
        self,
        frame,
        left_percent=0.2,
        right_percent=0.2,
        top_percent=0.2,
        bottom_percent=0.0,
    ):
        height, width, _ = frame.shape
        left = int(width * left_percent)
        right = width - int(width * right_percent)
        top = int(height * top_percent)
        bottom = height - int(height * bottom_percent)
        return (left, top, right, bottom)

    def roi_intersects(self, roi, bbox, threshold=0.7):
        # ROI and bounding box coordinates
        (x1, y1, x2, y2) = roi
        (bx1, by1, bx2, by2) = bbox

        # Calculate the coordinates of the intersection
        ix1 = max(x1, bx1)
        iy1 = max(y1, by1)
        ix2 = min(x2, bx2)
        iy2 = min(y2, by2)

        # Calculate the width and height of the intersection
        iw = max(0, ix2 - ix1)
        ih = max(0, iy2 - iy1)

        # Calculate the area of the intersection and the bounding box
        intersection_area = iw * ih
        bbox_area = (bx2 - bx1) * (by2 - by1)

        # Calculate the overlap ratio
        overlap_ratio = intersection_area / bbox_area

        # Return whether the overlap ratio is above the threshold
        return overlap_ratio >= threshold

    def store_data(self, frame, detections, dataset, timestamp, whitelisted_objects):
        height, width, _ = frame.shape
        roi = self.calculate_roi(frame)
        current_frame_detections = (
            False  # Flag to track detections in the current frame
        )

        for detection in detections:
            if self.label_map[detection.label] not in whitelisted_objects:
                # print(f"{self.label_map[detection.label]} not whitelisted")
                continue

            bbox = self.frame_norm(
                frame,
                (detection.xmin, detection.ymin, detection.xmax, detection.ymax),
            )

            bbox_width = bbox[2] - bbox[0]
            bbox_height = bbox[3] - bbox[1]
            self.logger.info(f"bb size : {bbox_height} x {bbox_width}")

            if bbox_width < self.min_bbox_size or bbox_height < self.min_bbox_size:
                self.logger.info(f"{detection.label} not large enough")
                continue

            if not self.roi_intersects(roi, bbox):
                self.logger.info(f"{detection.label} not sufficiently in ROI")
                continue

            current_frame_detections = True

            frame_time = time.time()
            if self.last_detection_saved_time:
                elapsed_time = frame_time - self.last_detection_saved_time
                if elapsed_time < self.camera_detection_rate:
                    self.logger.info("Recently saved detection. skipping")
                    continue

            debug_frame = frame.copy()
            det_frame = debug_frame[bbox[1] : bbox[3], bbox[0] : bbox[2]]
            cropped_path = f"/home/pi/tow-pro-vision/data/{self.label_map[detection.label]}/{timestamp}_cropped.jpg"

            cv2.imwrite(cropped_path, cv2.cvtColor(det_frame, cv2.COLOR_RGB2BGR))
            cv2.rectangle(
                debug_frame, (bbox[0], bbox[1]), (bbox[2], bbox[3]), (255, 0, 0), 2
            )
            cv2.putText(
                debug_frame,
                f"{self.label_map[detection.label]} {bbox_width}x{bbox_height}",
                (bbox[0] + 10, bbox[1] + 20),
                cv2.FONT_HERSHEY_TRIPLEX,
                0.5,
                255,
            )
            overlay_path = f"/home/pi/tow-pro-vision/data/{self.label_map[detection.label]}/{timestamp}_overlay.jpg"
            cv2.imwrite(overlay_path, cv2.cvtColor(debug_frame, cv2.COLOR_RGB2BGR))

            # Get the latest GPS data
            gps_data = self.gps_handler.get_latest_gps_data()
            lat = gps_data["lat"] if gps_data else None
            lon = gps_data["lon"] if gps_data else None

            data = {
                "timestamp": timestamp,
                "label": self.label_map[detection.label],
                "left": bbox[0],
                "top": bbox[1],
                "right": bbox[2],
                "bottom": bbox[3],
                "raw_frame": f"data/raw/{timestamp}.jpg",
                "overlay_frame": overlay_path,
                "cropped_frame": cropped_path,
                "lat": lat,
                "lon": lon,
            }
            dataset.writerow(data)
            cv2.imwrite(
                f"/home/pi/tow-pro-vision/data/raw/{timestamp}.jpg",
                cv2.cvtColor(frame, cv2.COLOR_RGB2BGR),
            )
            self.last_detection_saved_time = frame_time
            # add_gps_data_to_image(raw_frame_path, gps_data)

        # Update detection buffer for stability check
        self.detection_buffer.append(current_frame_detections)
        if len(self.detection_buffer) > self.stability_frames:
            self.detection_buffer.pop(0)

        # Check for stability
        if sum(self.detection_buffer) == self.stability_frames:
            self.car_detected = True
            self.logger.info("Car detected on the truck consistently.")
        else:
            self.car_detected = False
            self.logger.info("No stable detection of car on the truck.")

    def create_directories(self):
        for text in self.label_map:
            Path(f"/home/pi/tow-pro-vision/data/{text}").mkdir(
                parents=True, exist_ok=True
            )
        Path("/home/pi/tow-pro-vision/data/raw").mkdir(parents=True, exist_ok=True)

    def initialize_dataset(self, dataset_path):
        dataset_file = open(dataset_path, "a")
        dataset = csv.DictWriter(
            dataset_file,
            [
                "lat",
                "lon",
                "timestamp",
                "label",
                "left",
                "top",
                "right",
                "bottom",
                "raw_frame",
                "overlay_frame",
                "cropped_frame",
            ],
        )
        dataset.writeheader()
        return dataset_file, dataset
