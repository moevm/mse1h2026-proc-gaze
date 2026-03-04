from src.tracker import Tracker
from src.video import Video
import cv2

video = Video("0")
print(video.info)

tracker = Tracker()
tracker.process_webcam()