# set a playzone for your camera and divide it into sub-zones.
from typing import List

from laser.frame_tools import unwrap, unwrapped_to_original
from laser.joystick import StickController, ButtonController
import numpy as np


def detect_laser_pos(frame: np.ndarray, threshold, round_position:bool=False, coefficient_func=lambda x: x):
    filtered = np.argwhere(frame >= threshold)
    if filtered.size == 0:
        return None

    # make laser_poses list [x, y, coefficient]
    laser_poses = [(pos[1], pos[0], coefficient_func(frame[pos[0], pos[1]])) for pos in filtered]
    coefficients = np.sum([k for (_, _, k) in laser_poses])

    x_mean = np.sum([x * k for (x, _, k) in laser_poses]) / coefficients
    y_mean = np.sum([y * k for (_, y, k) in laser_poses]) / coefficients

    if round_position:
        return int(x_mean + 0.5), int(y_mean + 0.5)
    return x_mean, y_mean


class Zone:
    def __init__(self, markers_poses:List[List[int]]=None, threshold=255, is_button=False,
                 joystick_controller: StickController | ButtonController | None = None, coeff_func=lambda x: x):
        """
        Make a playable zone for your laser
        """

        # input settings
        self.markers = markers_poses
        self.laser_position = None
        self.is_button = is_button

        # detection settings
        self.threshold = threshold
        self.coefficient_lambda = coeff_func

        # debug displaying
        self.unwrapped_frame = None
        self.absolute_laser = None

        # joystick
        self.joystick_class = joystick_controller

    def update(self, frame):
        """
        Detects laser position, updates absolute position
        :param frame:
        :return: Returns laser position|boolean and unwrapped frame
        """

        # unwrap frame
        # TODO: add a camera undistortion later
        unwrapped, matrix = unwrap(frame, self.markers)

        # detect laser
        self.laser_position = detect_laser_pos(unwrapped, self.threshold, coefficient_func=self.coefficient_lambda)
        self.absolute_laser = unwrapped_to_original(self.laser_position, matrix)

        # process joystick
        if self.joystick_class is not None:
            self.joystick_class.process_laser_movement(self.laser_position)

        self.unwrapped_frame = unwrapped
        if self.is_button:
            return self.laser_position is not None
        return self.laser_position
