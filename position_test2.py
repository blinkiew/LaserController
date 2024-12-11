# test the accuracy of lasers

import laser
from laser import joystick
from laser import frame_tools as fx
import cv2 as cv

def initialize_zones(zones_classes, zones_preferences):
    for zone_class, zone_info in zip(zones_classes, zones_preferences):
        zone_class.threshold = zone_info["threshold"]
        zone_class.markers = zone_info["markers"]

def main():
    gamepad = joystick.create_gamepad()
    zone1 = laser.Zone(joystick_controller = joystick.StickController(gamepad, joystick.LSTICK))
    zone2 = laser.Zone(joystick_controller = joystick.ButtonController(gamepad, joystick.XUSB_BUTTON.XUSB_GAMEPAD_X),
                       is_button=True)
    zones = [zone1, zone2]

    settings_path = "settings.json"
    saver = laser.PreferencesManager(settings_path)
    zones_settings = saver.read_zones()
    initialize_zones(zones, zones_settings)

    camera = laser.OpenCamera(0)
    debug_window = laser.DebugWindow(zones=zones)

    while True:
        frame = camera.read_frame()
        if frame is None:
            continue

        # Process zones
        for zone in zones:
            zone.update(frame)

        # Update debug window
        debug_window.set_frame(frame)
        debug_window.draw_markers()
        debug_window.draw_lasers()
        debug_window.draw_sticks()
        debug_window.display_frame()

        # Process input
        was_changes, do_exit = debug_window.update_inputs()

        # Save zones and check exit condition
        if was_changes or do_exit:
            saver.save_zones(zones)

        if do_exit:
            break

    print("Laser detector closed successfully")

if __name__ == "__main__":
    main()
