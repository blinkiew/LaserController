# test left stick of vgamepad

import laser
from laser import joystick

def main():
    zone_markers = [[50, 50], [150, 50], [50, 150], [150, 150]]
    gamepad = joystick.create_gamepad()
    test_zone = laser.Zone(markers_poses=zone_markers,
                           joystick_controller = joystick.StickController(gamepad, laser.LSTICK))

    camera = laser.OpenCamera(0)
    debug_window = laser.DebugWindow(zones=[test_zone])

    while True:
        frame = camera.read_frame()
        if frame is None:
            continue

        # Update zones
        test_zone.update(frame)

        # Update debug window
        debug_window.set_frame(frame)

        debug_window.draw_markers()
        debug_window.draw_lasers()
        debug_window.draw_sticks()  # draws stick's info

        debug_window.display_frame()

        # Process input
        _, do_exit = debug_window.update_inputs()
        if do_exit:
            break

    print("Laser detector closed successfully")

if __name__ == "__main__":
    print("You can check virtual gamepad stick on https://hardwaretester.com/gamepad")
    main()
