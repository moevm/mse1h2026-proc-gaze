from src.tracker import Tracker
from src.video import Video

video = Video("0")
print(video.info)

tracker = Tracker()
tracker.process_video(video)