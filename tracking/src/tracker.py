from src.constants import *
from src.gaze_estimator import *
from src.gaze_mapper import *

import json
import os
from pathlib import Path
from typing import Any, Optional

from src.constants import JOB_STATUS_DONE, JOB_STATUS_FAILED, JOB_STATUS_IN_PROGRESS
from src.video import Video



class Tracker:
    def __init__(self, precision_mode: int=0, threshold: float=0.5) -> None:        
        self._data_dir = Path(os.environ.get("DATA_DIR", "/data")).resolve()
        self.gaze_estimator = GazeEstimator(precision_mode, threshold)
        self.gaze_mapper    = GazeMapper()
    
    @staticmethod
    def draw_landmarks(self, face_image: np.ndarray, points: List) -> np.ndarray:
        for p in points:
            cv2.circle(face_image, p, 2, (255, 0, 0), 2)
        return face_image
    
    def process_camera_frame(self, frame: np.ndarray, draw_bbox: bool = False) -> Tuple[np.ndarray, List[np.ndarray]]:
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
                self.draw_landmarks(res, [(left_pupil[0] + x_offset, left_pupil[1] + y_offset),
                                            (right_pupil[0] + x_offset, right_pupil[1] + y_offset)])

            l = 25 # temporal for test only
            rx, ry = right_pupil
            lx, ly = left_pupil
            
            sx, sy = int((rx+lx)/2), int((ry+ly)/2)
            
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
        
        out = cv2.VideoWriter('output.mp4', cv2.VideoWriter_fourcc(*'mp4v'), 20.0, (frame_width, frame_height))
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
        pass
    
    def process_video(self, video) -> None:
        pass
    
    def _resolve_path(self, relative_path: str) -> Path:
        """
        Преобразует относительный путь внутри DATA_DIR в абсолютный путь.

        Args:
            relative_path: относительный путь к входному файлу из payload.inputs,
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

    def process_video(self, video: Video, out_dir: Optional[Path] = None) -> dict[str, str]:
        """
        Обрабатывает одно видео и сохраняет результаты в out_dir.

        Args:
            video: объект видео для обработки.
            out_dir: директория, в которую нужно сохранить результаты.

        Returns:
            Словарь с относительными путями до артефактов внутри DATA_DIR.
        """
        if out_dir is None:
            return {}

        out_dir = out_dir.resolve()
        out_dir.mkdir(parents=True, exist_ok=True)

        info_path = out_dir / "video_info.json"
        info_path.write_text(json.dumps(video.info, ensure_ascii=False, indent=2), encoding="utf-8")

        traj_path = out_dir / "trajectory.json"
        if not traj_path.exists():
            traj_path.write_text("{}", encoding="utf-8")

        return {
            "video_info": self._to_relative_path(info_path),
            "trajectory": self._to_relative_path(traj_path),
        }

    def process_job(self, payload: dict[str, Any]) -> dict[str, Any]:
        """
        Обрабатывает задание на трекинг.

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
                        "duration": 3.5,
                        "description": "описание"
                    }
                ]
            }
        """
        recording_id = str(payload["recording_id"])

        screen_video_path = payload.get("path_screen")
        webcam_video_path = payload.get("path_webcam")

        if not screen_video_path or not webcam_video_path:
            raise KeyError("payload must contain both 'path_screen' and 'path_webcam'")

        out_dir = (self._data_dir / "results" / recording_id).resolve()
        out_dir.relative_to(self._data_dir)
        out_dir.mkdir(parents=True, exist_ok=True)

        for input_name, input_path in {
            "screen_video": screen_video_path,
            "webcam_video": webcam_video_path,
        }.items():
            video_path = self._resolve_path(str(input_path))
            source_out_dir = out_dir / input_name

            with Video(video_path) as v:
                self.process_video(v, out_dir=source_out_dir)

        intervals: list[dict[str, Any]] = []

        return {
            "recording_id": recording_id,
            "intervals": intervals,
        }
