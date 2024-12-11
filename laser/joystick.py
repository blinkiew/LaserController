# turn your laser into joystick using these methods.

import vgamepad as vg
from vgamepad import XUSB_BUTTON
import numpy as np


LSTICK: str = 'left'
RSTICK: str = 'right'

def calc_norm_vector_between(a, b):
    shift = b - a
    distance = np.linalg.norm(shift)

    # check for NaN
    if np.isnan(distance):
        return 0, 0

    normalized = shift / distance
    return normalized


def create_gamepad():
    gamepad = vg.VX360Gamepad()
    gamepad.update()

    return gamepad


class StickController:
    def __init__(self, gamepad: vg.VX360Gamepad, control_stick: str):
        self.gamepad = gamepad

        self.center_pos: np.ndarray | None = None
        self.deadzone: float = 15
        self.radius: float = 70
        self.stick_vector = None

        self.sticks = {
            'left': self.gamepad.left_joystick_float,
            'right': self.gamepad.right_joystick_float,
        }
        self.stick = self.sticks[control_stick]

    def process_laser_movement(self, laser_position):
        if laser_position is not None:
            laser_position = np.array(laser_position)
            # set center position. move it after joystick if laser went out of radius.
            if self.center_pos is not None:
                self.center_pos = self.move_center(self.center_pos, laser_position)
            else:
                self.center_pos = laser_position

            # calc vector
            distance = np.linalg.norm(laser_position - self.center_pos)

            if distance > self.deadzone:
                self.stick_vector = calc_norm_vector_between(self.center_pos, laser_position)
                self.move_stick()
        else:
            self.center_pos = None
            self.stick_vector = None
            self.reset_stick()

    def move_center(self, center_pos: np.ndarray, laser_pos: np.ndarray):
        shift_vector = laser_pos - center_pos
        distance = np.linalg.norm(shift_vector)
        if np.isnan(distance):
            return np.zeros_like(center_pos)

        mask = distance > self.radius
        center_shift = np.where(mask, (distance - self.radius) * shift_vector / distance, np.zeros_like(center_pos))


        return center_pos + center_shift

    def move_stick(self):
        self.stick(x_value_float=self.stick_vector[0], y_value_float=self.stick_vector[1] * -1)
        self.gamepad.update()

    def reset_stick(self):
        self.stick(x_value_float=0.0, y_value_float=0.0)
        self.gamepad.update()


class ButtonController:
    def __init__(self, gamepad: vg.VX360Gamepad, control_button: XUSB_BUTTON):
        self.gamepad = gamepad
        self.button = control_button

    def process_laser_movement(self, laser_position):
        if laser_position is not None:
            self.press_button()
        else:
            self.release_button()

    def press_button(self):
        self.gamepad.press_button(button=self.button)
        self.gamepad.update()

    def release_button(self):
        self.gamepad.release_button(button=self.button)
        self.gamepad.update()
