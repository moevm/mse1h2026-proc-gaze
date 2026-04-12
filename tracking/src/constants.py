from enum import Enum

PTH2MODELS = "/intel/intel"

PRECISIONS = ["FP32", "FP16-INT8", "FP16"]

MODELS = \
{
    "face_detection":         ["face-detection-0200"],
    "pupils_detection":       ["landmarks-regression-retail-0009"],
    "eyes_contour_detection": ["facial-landmarks-98-detection-0001"],
    "head_pose_estimation":   ["head-pose-estimation-adas-0001"],
    "gaze_vector_estimation": ["gaze-estimation-adas-0002"]
}

# hand-picked indices for OpenVINO model (no docs exists)
EYE_INDICES = list(range(60, 76)) + [33]
RIGHT_EYE_INDICES = [0, 1, 2, 3, 4, 5, 6, 7, 16]
LEFT_EYE_INDICES  = [8, 9, 10, 11, 12, 13, 14, 15]

class IntervalDescription(str, Enum):
    NO_GAZE        = "No gaze found on camera frame"
    MULTIPLE_GAZES = "Multiple gazes found on camera frame"
    OFF_SCREEN     = "Projected point went off-screen"

DEFAULT_FPS = 30.0