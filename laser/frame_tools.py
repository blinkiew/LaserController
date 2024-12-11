import numpy as np
import cv2 as cv


def _get_zone_size(zone_points):
    zone_points = np.float32(zone_points)

    # width
    width_top = np.linalg.norm(zone_points[1] - zone_points[0])
    width_bottom = np.linalg.norm(zone_points[2] - zone_points[3])
    max_width = int(max(width_top, width_bottom))

    # height
    height_left = np.linalg.norm(zone_points[0] - zone_points[2])
    height_right = np.linalg.norm(zone_points[1] - zone_points[3])
    max_height = int(max(height_left, height_right))

    return max_width, max_height


def unwrap(frame, markers_poses):
    # get points
    zone_points = np.float32(markers_poses)
    zone_size = _get_zone_size(markers_poses)
    target_points = np.float32([[0, 0], [zone_size[0] - 1, 0],
                                [0, zone_size[1] - 1], [zone_size[0] - 1, zone_size[1] - 1]])

    # unwrap
    matrix = cv.getPerspectiveTransform(zone_points, target_points)
    unwrapped = cv.warpPerspective(frame, matrix, zone_size)
    return unwrapped, matrix


def unwrapped_to_original(point, matrix):
    if point is None:
        return None

    point_on_warped_homogenous = np.array([point[0], point[1], 1])
    original_point = np.dot(np.linalg.inv(matrix), point_on_warped_homogenous)
    original_point /= original_point[2]  # convert back from homogeneous coordinates
    return np.round(original_point[:2])


def extract_channels(frame: np.ndarray):
    """
    Extracts channels from frame in RGB format.
    :param frame: Frame to extract channels from
    :return: r, g, b channels
    """
    b, g, r = cv.split(frame)
    return r, g, b


def brightness(frame: np.ndarray, value: int):
    """
    Adjusts the brightness of frame
    :param frame: Source frame
    :param value: Brightness value
    :return: Adjusted frame
    """
    hsv = cv.cvtColor(frame, cv.COLOR_BGR2HSV)
    h, s, v = cv.split(hsv)

    lim = 255 - value
    v[v > lim] = 255
    v[v <= lim] += value

    final_hsv = cv.merge((h, s, v))
    out = cv.cvtColor(final_hsv, cv.COLOR_HSV2BGR)
    return out


def gamma(frame: np.ndarray, value: float):
    """
    Adjusts the gamma of frame
    :param frame: Source frame
    :param value: Gamma value
    :return: Gamma-corrected frame
    """
    inv_gamma = 1.0 / value
    table = np.array([((i / 255.0) ** inv_gamma) * 255
                      for i in np.arange(0, 256)]).astype("uint8")
    # apply gamma correction using the lookup table
    return cv.LUT(frame, table)


def denoise(frame: np.ndarray):
    """
    Denoises an image. Really slow.
    :param frame: Source frame
    :return:
    """
    return cv.fastNlMeansDenoisingColored(frame,None,10,10,7,21)
