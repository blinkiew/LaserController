# исправление искажения видео, регулировка по 4 точкам, яркость, резкость, контрастность

import numpy as np
import cv2 as cv


class OpenCamera:
    def __init__(self, camera_path=0):
        self.cap = cv.VideoCapture(camera_path)

    def read_frame(self):
        ret, frame = self.cap.read()
        if ret is False:
            return None

        return frame

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.cap.release()
