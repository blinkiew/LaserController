# test the accuracy of lasers

import laser

def main():
    zone_markers = [[50,50],[150,50],[50,150],[150,150]]
    test_zone = laser.Zone(markers_poses=zone_markers)

    camera = laser.OpenCamera(0)
    debug_window = laser.DebugWindow(zones=[test_zone])

    while True:
        frame = camera.read_frame()
        if frame is None:
            continue

        # Process zone
        test_zone.update(frame)

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
    print("Make sure to left-click on the zone to lower brightness threshold. right-click to change zone borders")
    main()
