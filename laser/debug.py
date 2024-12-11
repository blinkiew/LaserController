# create debug window to see what's happening with your camera and laser.

import math
from typing import Tuple, Any, List, Sequence

import numpy as np
import cv2 as cv
from cv2 import Mat, UMat
from numpy import ndarray

from laser.zone import Zone
from laser.joystick import StickController


def rearrange_markers(markers, reshape=False):
    new_markers = markers.copy()
    new_markers[0], new_markers[1] = new_markers[1], new_markers[0]

    if reshape:
        return np.array(new_markers, np.int32).reshape(-1, 1, 2)
    return np.array(new_markers, np.int32)


def auto_resize_frame(frame: np.ndarray, min_width: int = 300) -> tuple[ndarray, int] | tuple[
    Mat | ndarray | UMat, int]:
    frame_size = np.shape(frame)
    if frame_size[1] >= min_width:
        return frame, 1

    # calc a final width
    width_multiplier = math.ceil(min_width/frame_size[1])
    frame = cv.resize(frame, np.multiply([frame_size[1], frame_size[0]], width_multiplier),
                      interpolation=cv.INTER_LINEAR)
    return frame, width_multiplier


# make an empty frame
empty_frame = np.full((500, 500, 3), (255, 255, 255), dtype=np.uint8)
cv.putText(empty_frame, "Frame is None", (10, 32), cv.FONT_HERSHEY_SIMPLEX, 1, (255, 255, 255), 2)


class DebugWindow:
    def __init__(self, zones: List[Zone], window_name:str='Laser Debug'):
        """
        Create a window for debugging input data or visualizing lasers.
        Left-click to open zone in separate window and see additional info (unwrapped frame, joystick info, etc.)
        Right-click to edit borders of zone using number keys of your keyboard
        :param zones: List of Zone() classes, which are used to get info from. Pass at least one class item.
        :param window_name: Set custom name for your window if needed
        """

        # zones & graphics
        self.frame: np.ndarray | None = None
        self.zones: List[Zone] = zones
        self.opened_zones: ZoneDebugWindow | [] = []
        self.resize_multiplier: int = 1

        # window
        self.win_name: str = window_name
        cv.namedWindow(self.win_name, cv.WINDOW_AUTOSIZE)
        cv.setMouseCallback(self.win_name, self._on_mouse)

        # input data
        self.mouse_x: int = 0
        self.mouse_y: int = 0

        self.left_button: bool = False
        self.right_button: bool = False

        self.key_pressed = None
        self.selected_zone: None | Zone = None

    # input methods
    def _on_mouse(self, event, x, y, flags, userdata):
        self.mouse_x = x
        self.mouse_y = y
        self.left_button = event == cv.EVENT_LBUTTONDOWN
        self.right_button = event == cv.EVENT_RBUTTONDOWN

    def get_key_pressed(self):
        __key_pressed = cv.waitKey(1)
        if __key_pressed is None: return
        if __key_pressed not in range(0x110000): return

        return __key_pressed

    def update_inputs(self):
        """
        Updates inputs in debug window and all zone windows.
        :return: was_changes: true if zone markers were modified.
        do_exit: true if esc key was pressed
        """
        was_changes = False

        self.key_pressed = self.get_key_pressed()

        # zone clicks
        zone_was_selected = False
        for i, zone in enumerate(self.zones):
            markers = rearrange_markers(zone.markers, True)
            mouse_in = cv.pointPolygonTest(markers, (self.mouse_x, self.mouse_y), False) >= 0

            if mouse_in:
                if self.left_button and not any(zone_class.order == i for zone_class in self.opened_zones):
                    # user left-clicked zone (open window)
                    self.opened_zones.append(ZoneDebugWindow(i, zone))
                if self.right_button:
                    # user right-clicked zone (change border mode)
                    self.selected_zone = zone
                    zone_was_selected = True
            else:
                if self.right_button and not zone_was_selected:
                    self.selected_zone = None

        # move markers
        try:
            num = int(chr(self.key_pressed))
            if num in range(1, 5):
                self.selected_zone.markers[num-1] = [self.mouse_x, self.mouse_y]
                was_changes = True
        except (TypeError, ValueError):
            pass

        # update zone windows inputs
        for zone_window in self.opened_zones:
            do_exit = zone_window.update_inputs()
            if do_exit:
                self.opened_zones.pop(self.opened_zones.index(zone_window))

        # esc key
        if self.key_pressed == 27:  # esc key to exit
            return was_changes, True
        return was_changes, False

    # graphical methods
    def set_frame(self, frame: np.ndarray):
        """
        Sets current frame to buffer to use other draw methods on it.
        :param frame: Frame which must be set
        """""
        self.frame, self.resize_multiplier = auto_resize_frame(frame)
        for zone_window in self.opened_zones:
            zone_window.set_frame()

    def draw_markers(self, line_thickness:int=2, dot_size:int=8, color:Sequence[float]=(255, 255, 255)):
        """
        Draws zones borders
        :param line_thickness: Thickness of lines connecting dots
        :param dot_size: Size of dots
        :param color: Color of the border
        """

        if self.frame is None:  # raise an error if no frame provided
            raise ValueError("No frame given")

        markers_pull = [rearrange_markers(zone1.markers, True) for zone1 in self.zones]
        cv.polylines(self.frame, markers_pull, True, color, line_thickness)

        for markers in markers_pull:
            for pos in markers:
                cv.circle(self.frame, pos.reshape(-1), dot_size, color, -1)

        # outline selected zone and draw numbers on it's circles
        if self.selected_zone is not None:
            cv.polylines(self.frame, [rearrange_markers(self.selected_zone.markers)], True, color, line_thickness*2)
            for i, marker in enumerate(self.selected_zone.markers, start=1):
                cv.circle(self.frame, marker, dot_size*2, color, -1)

                font = cv.FONT_HERSHEY_SIMPLEX
                scale = 0.1 + dot_size/8
                thickness = round(dot_size/2)

                text_size, _ = cv.getTextSize(str(i), font, scale, thickness)
                text_origin = (round(marker[0] - text_size[0] / 2), round(marker[1] + text_size[1] / 2))
                cv.putText(self.frame, str(i), text_origin, font, scale, tuple(255 - c for c in color), thickness)

    def draw_lasers(self, size:int=5, color:Sequence[float]=(0, 0, 255)):
        """
        Draws lasers positions relative to original camera view
        :param size:
        :param color:
        """

        laser_poses = [zone.absolute_laser for zone in self.zones if zone.absolute_laser is not None]

        for pos in laser_poses:
            pos = np.array([round(cord) for cord in pos])
            cv.circle(self.frame, pos, size, color, -1)

        [zone_window.draw_laser() for zone_window in self.opened_zones]
        for zone_window in self.opened_zones:
            zone_window.draw_laser()

    def draw_sticks(self, color:Sequence[float]=(255, 255, 255)):
        """
        Draws virtual joystick info, including radius, deadzone, and direction vector.
        :param color: Color of elements
        """

        for zone_window in self.opened_zones:
            zone_window.draw_stick(color=color)

    def display_frame(self):
        """
        Display frame buffer to a window
        """

        cv.imshow(self.win_name, self.frame)
        for zone_window in self.opened_zones:
            zone_window.display_frame()


class ZoneDebugWindow:
    def __init__(self, zone_index: int, zone_class: Zone):
        # zones & graphics
        self.zone = zone_class
        self.frame = None
        self.resize_multiplier: int = 1

        # window
        self.order = zone_index
        self.win_name = f"Zone {self.order}"
        cv.namedWindow(self.win_name, cv.WINDOW_AUTOSIZE)
        cv.setMouseCallback(self.win_name, self._on_mouse)
        cv.createTrackbar(self.win_name, self.win_name, zone_class.threshold, 255, self._on_threshold_change)

        # input data
        self.mouse_x = 0
        self.mouse_y = 0
        self.left_button = False
        self.right_button = False
        self.pressed_key = None

    def _on_mouse(self, event, x, y, flags, userdata):
        self.mouse_x = x
        self.mouse_y = y
        self.left_button = event == cv.EVENT_LBUTTONDOWN
        self.right_button = event == cv.EVENT_RBUTTONDOWN

    def _on_threshold_change(self, value: int):
        self.zone.threshold = value

    def get_key_pressed(self):
        __key_pressed = cv.waitKey(1)
        if __key_pressed is None: return
        if __key_pressed not in range(0x110000): return

        return __key_pressed

    def update_inputs(self):
        self.pressed_key = self.get_key_pressed()

        if self.right_button:  # close this zone
            cv.destroyWindow(self.win_name)
            return True
        return False

    # graphical methods
    def set_frame(self):
        unwrapped_frame = self.zone.unwrapped_frame
        if unwrapped_frame is None:
            self.frame = empty_frame
            return
        self.frame, self.resize_multiplier = auto_resize_frame(unwrapped_frame)

    def draw_laser(self, size:int=3, color:Sequence[float]=(0, 0, 255)):
        if self.zone.laser_position is not None:
            laser_pos = self.resize_multiplier * np.round(np.array(self.zone.laser_position)).astype(int)
            cv.circle(self.frame, laser_pos, size, color, -1)

    def draw_stick(self, color:Sequence[float]=(255, 255, 255), radius_thickness:int=2):
        if self.zone.joystick_class is not None and type(self.zone.joystick_class) == StickController:
            stick_class = self.zone.joystick_class

            # draw joystick radius
            if stick_class.center_pos is not None:
                center = self.resize_multiplier * np.array([round(n) for n in stick_class.center_pos])
                cv.circle(self.frame, center, round(stick_class.radius*self.resize_multiplier), color, radius_thickness)

                # draw dead zone
                if stick_class.deadzone > 0:
                    cv.circle(self.frame, center, round(stick_class.deadzone * self.resize_multiplier), color,
                              radius_thickness)

                # draw direction
                las_pos = laser_pos = self.resize_multiplier * np.round(np.array(self.zone.laser_position)).astype(int)
                cv.line(self.frame, center, las_pos, color, radius_thickness)

    def display_frame(self):
        cv.imshow(self.win_name, self.frame)

