# use to test two zones for each laser.

import laser

def main():
    # create multiple zones
    zones = [laser.Zone(markers_poses=[[50, 50], [150, 50], [50, 150], [150, 150]]),
             laser.Zone(markers_poses=[[250, 50], [350, 50], [250, 150], [350, 150]])]

    camera = laser.OpenCamera(0)
    debug_window = laser.DebugWindow(zones=zones)

    while True:
        frame = camera.read_frame()
        if frame is None:
            continue

        # Update all zones
        for zone in zones:
            zone.update(frame)

        # Update debug window
        debug_window.set_frame(frame)

        debug_window.draw_markers()
        debug_window.draw_lasers()

        debug_window.display_frame()

        # Process input
        _, do_exit = debug_window.update_inputs()
        if do_exit:
            break

    print("Laser detector closed successfully")

if __name__ == "__main__":
    print("You can change zones area by clicking right mouse button on them, and pressing 1-4 numbers on keyboard")
    main()
