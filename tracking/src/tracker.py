from src.constants import *
from src.gaze_estimator import GazeEstimator
from src.gaze_mapper import GazeMapper

import os
from datetime import timedelta
import ffmpeg
import logging
import datetime
from pathlib import Path
from typing import Optional, List, Any, Dict, Tuple
import numpy as np
import cv2
import torch

from src.constants import IntervalDescription
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

    def process_camera_frame(self, frame: np.ndarray, gaze_info: Tuple[np.ndarray], draw_bbox: bool = False) -> np.ndarray:
        gaze_vecs, pupils, offsets, eye_bboxes = gaze_info

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
            _, frame = cam.read()

            new_frame = self.process_camera_frame(frame)

            out.write(new_frame)

            cv2.imshow('Camera', new_frame)

            if cv2.waitKey(1) == ord('q'):
                break

        cam.release()
        out.release()
        cv2.destroyAllWindows()

    def process_screen_frame(self, screen_frame: np.ndarray, gaze_info: Tuple[np.ndarray]) -> np.ndarray:
        gaze_vecs, _, _, _ = gaze_info

        main_vec = gaze_vecs[0]
        proj_p = self.gaze_mapper.project(main_vec).cpu().numpy()

        x, y, _ = proj_p
        x = int(x)
        y = int(y)
        res = self.draw_points(screen_frame, [(x, y)])
        return res

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
    
    @staticmethod
    def convert_codec(input_path: Path, output_path: Path) -> None:
        try:
            # docs: https://kkroening.github.io/ffmpeg-python/
            (
                ffmpeg
                .input(str(input_path))
                .output(
                    str(output_path),
                    vcodec="libx264",
                    pix_fmt='yuv420p',
                    movflags='+faststart',
                    an=None # disable audio
                )
                .run(overwrite_output=True, capture_stdout=True, capture_stderr=True)
            )
        except ffmpeg.Error as e:
            print(e.stderr.decode("utf-8", errors="replace") if e.stderr else str(e))
            raise

    _LAST_PROCESS_ID = 0

    @staticmethod
    def gen_unique_process_id():
        Tracker._LAST_PROCESS_ID += 1
        return Tracker._LAST_PROCESS_ID

    def process_video(
            self,
            screen_video: Video,
            camera_video: Video,
            out_dir: Optional[Path] = None
        ) -> List[Dict[str, Any]]:
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

        logger = logging.getLogger(f"process_video {Tracker.gen_unique_process_id()}")
        logger.info("Started processing videos:")
        logger.info(f"Screen: {screen_video.info}")
        logger.info(f"Camera: {camera_video.info}")

        if out_dir is None:
            return

        out_dir = out_dir.resolve()
        out_dir.mkdir(parents=True, exist_ok=True)
        
        '''
        Принцип обработки видео:
        1. Получаем на вход видео и обрабатываем их, сохраняем результат обработки (видео) в _raw.mp4 часть
        2. Преобразуем _raw.mp4 часть в .mp4 часть для корректного отображения в WEB-е перекодировкой в формат AVC (через ffmpeg-python)
        3. Удаляем _raw.mp4 
        '''
        camera_out_raw, screen_out_raw = out_dir / "camera_raw.mp4", out_dir / "screen_raw.mp4"
        camera_out, screen_out = out_dir / "camera.mp4", out_dir / "screen.mp4"

        camera_writer = cv2.VideoWriter(
            str(camera_out_raw),
            cv2.VideoWriter_fourcc(*"mp4v"),
            camera_video.fps,
            (camera_video.width, camera_video.height)
        )
        screen_writer = cv2.VideoWriter(
            str(screen_out_raw),
            cv2.VideoWriter_fourcc(*"mp4v"),
            screen_video.fps,
            (screen_video.width, screen_video.height)
        )

        intervals: List[Dict[str, Any]] = []
        
        logger.info("Processing frames...")
        try:
            frame_duration = 1.0 / screen_video.fps
            suspicious_interval_duration = 0.0
            suspicious_reasons: set = set()
            total_time = datetime.timedelta(seconds=camera_video.duration_sec)
            total_time = total_time // 1000000 * 1000000                        # remove microseconds
            last_log_time = datetime.datetime.now()

            frames_cnt = min(len(camera_video), len(screen_video))
            for frame_id, (camera_frame, screen_frame) in enumerate(zip(camera_video, screen_video)):
                gaze_vecs, pupils, offsets, eye_bboxes = self.gaze_estimator.estimate(camera_frame)
                current_time = frame_id / screen_video.fps
                
                if not gaze_vecs:
                    suspicious_interval_duration += frame_duration
                    suspicious_reasons.add(IntervalDescription.NO_GAZE)
                    continue
                elif len(gaze_vecs) > 1:
                    suspicious_interval_duration += frame_duration
                    suspicious_reasons.add(IntervalDescription.MULTIPLE_GAZES)
                    continue
                elif any(np.isnan(self.gaze_mapper.project(gaze_vecs[0]).cpu().numpy())):
                    suspicious_interval_duration += frame_duration
                    suspicious_reasons.add(IntervalDescription.OFF_SCREEN)
                    continue
                
                if suspicious_interval_duration > 1e-6 and suspicious_reasons:
                    interval_start = current_time - suspicious_interval_duration
                    time_str = str(timedelta(seconds=int(interval_start)))
                    
                    intervals.append({
                        "time": time_str,
                        "duration": suspicious_interval_duration,
                        "description": ", ".join(sorted([r for r in suspicious_reasons]))
                    })
                    
                    suspicious_interval_duration = 0.0
                    suspicious_reasons.clear()

                gaze_info = (gaze_vecs, pupils, offsets, eye_bboxes)
                processed_camera = self.process_camera_frame(camera_frame, gaze_info, draw_bbox=True)
                processed_screen = self.process_screen_frame(screen_frame, gaze_info)
                camera_writer.write(processed_camera)
                screen_writer.write(processed_screen)
                
                if frame_id % ((frames_cnt + 9) // 10) == 0:
                    log_time = datetime.datetime.now()
                    progress = frame_id / frames_cnt
                    
                    processed_time = datetime.timedelta(seconds=int(progress*camera_video.duration_sec))
                    
                    one_sec = datetime.timedelta(seconds=1)
                    fps = int(frames_cnt / 10 / ((log_time - last_log_time) / one_sec + 0.001))

                    logger.info(f"Progress: {frame_id} / {frames_cnt} frames | "
                                f"{processed_time} / {total_time} | "
                                f"{int(progress * 100)}% | "
                                f"{fps} fps")
                    last_log_time = log_time
        except Exception as e:
            logger.error("Failed to process frames.")
            raise e
        finally:
            camera_writer.release()
            screen_writer.release()
            
        if suspicious_interval_duration > 1e-6 and suspicious_reasons:
            interval_start = len(screen_video) / screen_video.fps - suspicious_interval_duration
            time_str = str(timedelta(seconds=int(interval_start)))
            intervals.append({
                "time": time_str,
                "duration": suspicious_interval_duration,
                "description": ", ".join(sorted([r.name for r in suspicious_reasons]))
            })
            
        logger.info("Frames were processed sucessfully. Re-encoding output videos...")
        try:
            self.convert_codec(input_path=camera_out_raw, output_path=camera_out)
            self.convert_codec(input_path=screen_out_raw, output_path=screen_out)
        except Exception as e:
            logger.info("Failed to re-encode output videos.")
            raise e
        finally:
            camera_out_raw.unlink(missing_ok=True)
            screen_out_raw.unlink(missing_ok=True)
        
        logger.info("Output videos were re-encoded successfully. process_video is done.")
        return intervals

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
        logging.info(f"Received job with payload: {payload}")
        recording_id = str(payload["recording_id"])

        path_screen = payload.get("path_screen")
        path_webcam = payload.get("path_webcam")
        if not path_screen or not path_webcam:
            raise KeyError("payload must contain both 'path_screen' and 'path_webcam'")

        screen_video_path = os.path.join("/data", path_screen)
        webcam_video_path = os.path.join("/data", path_webcam)

        out_dir = (self._data_dir / "results" / recording_id).resolve()
        out_dir.relative_to(self._data_dir)
        out_dir.mkdir(parents=True, exist_ok=True)

        screen_video = Video(screen_video_path)
        webcam_video = Video(webcam_video_path)

        try:
            with torch.no_grad():
                intervals: List[Dict[str, Any]] = self.process_video(screen_video, webcam_video, out_dir)
        finally:
            screen_video.close()
            webcam_video.close()

        result = \
        {
            "recording_id": recording_id,
            "intervals": intervals,
            "path_processed_webcam": self._to_relative_path(out_dir / "camera.mp4"),
            "path_processed_screen": self._to_relative_path(out_dir / "screen.mp4"),
        }

        return result
