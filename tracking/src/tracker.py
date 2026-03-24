from .constants import *
from .gaze_estimator import GazeEstimator
from .gaze_mapper import GazeMapper

import os
from pathlib import Path
from typing import Optional, List, Any, Dict
import numpy as np
import cv2
import torch

from src.constants import JOB_STATUS_DONE, JOB_STATUS_FAILED, JOB_STATUS_IN_PROGRESS, DEFAULT_SCREEN_FPS
from src.video import Video

device = torch.device("cuda" if torch.cuda.is_available() else "cpu")

class Tracker:
    def __init__(self, precision_mode: int=0, threshold: float=0.5, use_torch_gaze: bool=False) -> None:        
        self._data_dir = Path(os.environ.get("DATA_DIR", "../preprocessed")).resolve()
        self.gaze_estimator: GazeEstimator = GazeEstimator(precision_mode, threshold, use_torch_gaze)
        self.gaze_mapper: GazeMapper = GazeMapper()

    @staticmethod
    def draw_points(image: np.ndarray, points: List) -> np.ndarray:
        for p in points:
            cv2.circle(image, p, 2, (0, 0, 255), 2)
        return image

    def process_camera_frame(self, frame: np.ndarray, draw_bbox: bool = False) -> np.ndarray:
        gaze_vecs, pupils, offsets, eye_bboxes = self.gaze_estimator.estimate(frame)

        res = np.copy(frame)
        for gaze_vec, pupil, offset, bbox in zip(gaze_vecs, pupils, offsets, eye_bboxes):
            left_pupil, right_pupil = pupil
            x_offset, y_offset = offset

            if draw_bbox:
                left_bbox, right_bbox = bbox
                x1, y1, x2, y2 = left_bbox
                cv2.rectangle(res, (x1 + x_offset, y1 + y_offset), (x2 + x_offset, y2 + y_offset), (255, 0, 0), 2)
                x1, y1, x2, y2 = right_bbox
                cv2.rectangle(res, (x1 + x_offset, y1 + y_offset), (x2 + x_offset, y2 + y_offset), (255, 0, 0), 2)
                self.draw_points(res, [(left_pupil[0] + x_offset, left_pupil[1] + y_offset), (right_pupil[0] + x_offset, right_pupil[1] + y_offset)])

            l = 25
            rx, ry = right_pupil
            lx, ly = left_pupil

            sx, sy = int((rx + lx) / 2), int((ry + ly) / 2)

            vx, vy = gaze_vec[:2]

            ex, ey = sx + vx * l, sy + vy * l

            global_start = (int(sx + x_offset), int(sy + y_offset))
            global_end = (int(ex + x_offset), int(ey + y_offset))

            cv2.arrowedLine(res, global_start, global_end, (255, 0, 0), 2)

        return res

    def process_webcam(self) -> None:
        cam = cv2.VideoCapture(0)
        frame_width = int(cam.get(cv2.CAP_PROP_FRAME_WIDTH))
        frame_height = int(cam.get(cv2.CAP_PROP_FRAME_HEIGHT))

        out = cv2.VideoWriter('output.mp4', cv2.VideoWriter_fourcc(*'mp4v'), cam.get(cv2.CAP_PROP_FPS), (frame_width, frame_height))
        while True:
            ret, frame = cam.read()

            new_frame = self.process_camera_frame(frame)

            out.write(new_frame)

            cv2.imshow('Camera', new_frame)

            if cv2.waitKey(1) == ord('q'):
                break

        cam.release()
        out.release()
        cv2.destroyAllWindows()

    def process_screen_frame(self, screen_frame: np.ndarray, camera_frame: np.ndarray) -> np.ndarray:
        vec, _, _, _ = self.gaze_estimator.estimate(camera_frame)
        main_vec = vec[0]

        proj_p = self.gaze_mapper.project(main_vec).cpu().numpy()

        x, y, _ = proj_p
        if not all(np.isnan(proj_p)):
            x = int(x)
            y = int(y)
            res = self.draw_points(screen_frame, [(x, y)])
            return res
        else:
            print("detected suspicious frame")
            return screen_frame

    def _resolve_path(self, relative_path: str) -> Path:
        """
        Преобразует относительный путь внутри DATA_DIR в абсолютный путь.

        Args:
            relative_path: относительный путь к входному файлу из payload,
                например ``videos/screen.mp4``.

        Returns:
            Абсолютный путь к файлу, расположенному внутри директории DATA_DIR.
        """
        p = Path(str(relative_path))
        if p.is_absolute() or ".." in p.parts:
            raise ValueError(f"Invalid path: {relative_path}")
        abs_path = (self._data_dir / p).resolve()
        abs_path.relative_to(self._data_dir)
        return abs_path

    def _to_relative_path(self, path: Path) -> str:
        return path.resolve().relative_to(self._data_dir).as_posix()

    def process_video(
            self,
            screen_video: Video,
            camera_video: Video,
            out_dir: Optional[Path] = None
        ) -> None:
        """
        Обрабатывает пару видео (экран + вебкамера) и сохраняет результаты в out_dir.

        Args:
            screen_video: объект Video для записи экрана.
            camera_video: объект Video для потока с вебкамеры.
            out_dir: директория для сохранения результатов.

        Сохраняет:
            - camera.mp4: обработанное видео с вебкамеры (bbox глаз, вектор взгляда).
            - screen.mp4: обработанное видео экрана (точка проекции взгляда).
        """
        if out_dir is None:
            return

        out_dir = out_dir.resolve()
        out_dir.mkdir(parents=True, exist_ok=True)

        camera_writer = cv2.VideoWriter(
            str(out_dir / "camera.mp4"),
            cv2.VideoWriter_fourcc(*"mp4v"),
            camera_video.fps,
            (camera_video._width, camera_video._height)
        )
        screen_writer = cv2.VideoWriter(
            str(out_dir / "screen.mp4"),
            cv2.VideoWriter_fourcc(*"mp4v"),
            DEFAULT_SCREEN_FPS,
            (screen_video._width, screen_video._height)
        )

        try:
            for camera_frame, screen_frame in zip(camera_video, screen_video):
                processed_camera = self.process_camera_frame(camera_frame, draw_bbox=True)
                processed_screen = self.process_screen_frame(screen_frame, camera_frame)

                camera_writer.write(processed_camera)
                screen_writer.write(processed_screen)
        finally:
            camera_writer.release()
            screen_writer.release()

    def process_job(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        """
        Обрабатывает задание на трекинг из payload.

        Ожидаемый формат payload:
            {
                "recording_id": "uuid",
                "path_webcam": "path/to/webcam.mp4",
                "path_screen": "path/to/screen.mp4"
            }

        Формат результата:
            {
                "recording_id": "uuid",
                "intervals": [
                    {
                        "time": "00:00:05",
                        "duration": 3,
                        "description": "описание"
                    }
                ],
                "path_processed_webcam": "results/uuid/camera.mp4",
                "path_processed_screen": "results/uuid/screen.mp4"
            }
        """
        recording_id = str(payload["recording_id"])

        screen_video_path = os.path.join("/data", payload.get("path_screen"))
        webcam_video_path = os.path.join("/data", payload.get("path_webcam"))

        if not screen_video_path or not webcam_video_path:
            raise KeyError("payload must contain both 'path_screen' and 'path_webcam'")

        out_dir = (self._data_dir / "results" / recording_id).resolve()
        out_dir.relative_to(self._data_dir)
        out_dir.mkdir(parents=True, exist_ok=True)

        screen_video = Video(screen_video_path)
        webcam_video = Video(webcam_video_path)

        self.process_video(screen_video, webcam_video, out_dir)

        screen_video.close()
        webcam_video.close()

        intervals: list[dict[str, Any]] = []

        result = {
            "recording_id": recording_id,
            "intervals": intervals,
            "path_processed_webcam": self._to_relative_path(out_dir / "camera.mp4"),
            "path_processed_screen": self._to_relative_path(out_dir / "screen.mp4"),
        }

        return result
