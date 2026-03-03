from src.tracker import Tracker
from src.video import Video
import cv2

video = Video("0")
print(video.info)

image = cv2.imread("/home/berlet/code/mse1h2026-proc-gaze/tracking/research/images/mark.jpg")
tracker = Tracker()
tracker.process_video(image)