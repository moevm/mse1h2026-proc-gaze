from src.gaze_smoother import AdaptiveGazeKalmanSmoother, BaseGazeSmoother
from src.gaze_estimator import GazeEstimator
from src.gaze_mapper import GazeDataset, GazeMapper, calibrate

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
from torch.utils.data import DataLoader, random_split

from src.constants import IntervalDescription
from src.video import Video

device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
logger = logging.getLogger(__name__)

class Tracker:
    def __init__(self, precision_mode: int=0, threshold: float=0.5, use_torch_gaze: bool=False) -> None:        
        self._data_dir = Path(os.environ.get("DATA_DIR", "../preprocessed")).resolve()
        self.gaze_estimator: GazeEstimator = GazeEstimator(precision_mode, threshold, use_torch_gaze)
        self.gaze_mapper: GazeMapper = GazeMapper()
        self.gaze_smoother: BaseGazeSmoother = AdaptiveGazeKalmanSmoother(measurement_var=0.1, process_var=100.0, saccade_factor=8.0)

    @staticmethod
    def draw_points(image: np.ndarray, points: List) -> np.ndarray:
        for p in points:
            cv2.circle(image, p, 2, (0, 0, 255), 2)
        return image

    def process_camera_frame(self, frame: np.ndarray, gaze_info: Tuple[np.ndarray], draw_bbox: bool = False) -> np.ndarray:
        if not gaze_info:
            return frame
        
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

            arrow_len = 25
            rx, ry = right_pupil
            lx, ly = left_pupil

            sx, sy = int((rx + lx) / 2), int((ry + ly) / 2)

            vx, vy = gaze_vec[:2]

            ex, ey = sx + vx * arrow_len, sy + vy * arrow_len

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
        if not gaze_info:
            return screen_frame
        
        gaze_vecs, _, _, _ = gaze_info

        if len(gaze_vecs) == 0:
            return screen_frame
    
        main_vec = gaze_vecs[0]
        proj_p = self._project_to_numpy(main_vec)[:2]
        
        if np.all(np.isfinite(proj_p)):
            smoothed_p = self.gaze_smoother.update(proj_p)
            
            x, y = smoothed_p
            x = int(x)
            y = int(y)
            res = self.draw_points(screen_frame, [(x, y)])
            return res
        else:
            logger.debug("Detected suspicious frame: projected gaze point is not finite")
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

    def _apply_calibration_result(self, result: List[float]) -> torch.Tensor:
        if len(result) != 3:
            raise ValueError(f"Calibration result must contain exactly 3 values, got {len(result)}")

        previous = self.gaze_mapper.translation_vec.detach().clone()
        translation = torch.tensor(result, device=device, dtype=torch.float32)
        with torch.no_grad():
            self.gaze_mapper.translation_vec.copy_(translation)
        return previous

    def _project_to_numpy(self, gaze_vec: np.ndarray) -> np.ndarray:
        return self.gaze_mapper.project(gaze_vec).detach().cpu().numpy()

    @staticmethod
    def _append_suspicious_interval(
        intervals: List[Dict[str, Any]],
        start_sec: float,
        duration_sec: float,
        reasons: set[IntervalDescription],
    ) -> None:
        if duration_sec <= 1e-6 or not reasons:
            return

        intervals.append({
            "time": str(timedelta(seconds=int(start_sec))),
            "duration": duration_sec,
            "description": ", ".join(
                reason.value for reason in sorted(reasons, key=lambda reason: reason.value)
            ),
        })

    def process_calibration(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        logger.info(f"Received calibration job with payload: {payload}")

        student_id = str(payload["student_id"])
        calibration_data = payload["calibration_data"]
        clicks = calibration_data.get("clicks") or []
        if not clicks:
            raise ValueError("calibration_data.clicks must not be empty")

        webcam_path = self._resolve_path(payload["webcam_path"])
        decoded_webcam_path = webcam_path.with_name(f"{webcam_path.stem}_decoded.mp4")
        self.convert_codec(webcam_path, decoded_webcam_path)

        webcam_video = Video(decoded_webcam_path)

        try:
            data = []
            for click in clicks:
                frame = webcam_video.frame_at_sec(float(click["time"]))
                gaze_vecs, _, _, _ = self.gaze_estimator.estimate(frame)
                if len(gaze_vecs) == 0:
                    raise ValueError("Gaze estimation failed. Frame does not contain detectable gaze vectors.")

                point = np.array([int(click["x"]), int(click["y"]), 0.0], dtype=np.float32)
                data.append((gaze_vecs[0], point))
        finally:
            webcam_video.close()
            decoded_webcam_path.unlink(missing_ok=True)

        if not data:
            raise ValueError("No usable gaze vectors were found for calibration")

        mapper = GazeMapper()
        dataset = GazeDataset(data)
        if len(dataset) == 1:
            train = val = dataset
        else:
            generator = torch.Generator().manual_seed(0)
            val_size = max(1, round(len(dataset) * 0.1))
            train_size = len(dataset) - val_size
            train, val = random_split(dataset, [train_size, val_size], generator)

        train_loader = DataLoader(train, batch_size=1, shuffle=True, num_workers=0)
        val_loader = DataLoader(val, batch_size=1, shuffle=True, num_workers=0)

        mapper = calibrate(15, mapper, train_loader, val_loader, verbose=False)
        result = [float(v) for v in mapper.translation_vec.detach().cpu().tolist()]

        return {
            "student_id": student_id,
            "result": result,
        }
    
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
            stderr = e.stderr.decode("utf-8", errors="replace") if e.stderr else str(e)
            logger.error("ffmpeg failed to convert %s -> %s: %s", input_path, output_path, stderr)
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

        process_logger = logging.getLogger(f"process_video {Tracker.gen_unique_process_id()}")
        process_logger.info("Started processing videos:")
        process_logger.info(f"Screen: {screen_video.info}")
        process_logger.info(f"Camera: {camera_video.info}")

        if out_dir is None:
            return []

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
        
        process_logger.info("Processing frames...")
        try:
            frame_duration = 1.0 / screen_video.fps
            suspicious_interval_duration = 0.0
            suspicious_reasons: set[IntervalDescription] = set()
            total_time = datetime.timedelta(seconds=camera_video.duration_sec or 0.0)
            total_time = total_time // 1000000 * 1000000                        # remove microseconds
            last_log_time = datetime.datetime.now()

            frames_cnt = min(len(camera_video), len(screen_video))
            for frame_id, (camera_frame, screen_frame) in enumerate(zip(camera_video, screen_video)):
                gaze_vecs, pupils, offsets, eye_bboxes = self.gaze_estimator.estimate(camera_frame)
                gaze_info = None
                
                current_time = frame_id / screen_video.fps
                
                if not gaze_vecs:
                    suspicious_interval_duration += frame_duration
                    suspicious_reasons.add(IntervalDescription.NO_GAZE)

                elif len(gaze_vecs) > 1:
                    suspicious_interval_duration += frame_duration
                    suspicious_reasons.add(IntervalDescription.MULTIPLE_GAZES)
                    
                elif np.any(~np.isfinite(self._project_to_numpy(gaze_vecs[0]))):
                    suspicious_interval_duration += frame_duration
                    suspicious_reasons.add(IntervalDescription.OFF_SCREEN)
                    
                else:
                    gaze_info = (gaze_vecs, pupils, offsets, eye_bboxes)
                    
                    self._append_suspicious_interval(
                        intervals,
                        current_time - suspicious_interval_duration,
                        suspicious_interval_duration,
                        suspicious_reasons,
                    )
                    suspicious_interval_duration = 0.0
                    suspicious_reasons.clear()

                processed_camera = self.process_camera_frame(camera_frame, gaze_info, draw_bbox=True)
                processed_screen = self.process_screen_frame(screen_frame, gaze_info)
                camera_writer.write(processed_camera)
                screen_writer.write(processed_screen)
                
                if frame_id % ((frames_cnt + 9) // 10) == 0:
                    log_time = datetime.datetime.now()
                    progress = frame_id / frames_cnt
                    
                    processed_time = datetime.timedelta(seconds=int(progress * (camera_video.duration_sec or 0.0)))
                    
                    one_sec = datetime.timedelta(seconds=1)
                    fps = int(frames_cnt / 10 / ((log_time - last_log_time) / one_sec + 0.001))

                    process_logger.info(f"Progress: {frame_id} / {frames_cnt} frames | "
                                        f"{processed_time} / {total_time} | "
                                        f"{int(progress * 100)}% | "
                                        f"{fps} fps")
                    last_log_time = log_time
        except Exception:
            process_logger.exception("Failed to process frames.")
            raise
        finally:
            camera_writer.release()
            screen_writer.release()
            
        self._append_suspicious_interval(
            intervals,
            len(screen_video) / screen_video.fps - suspicious_interval_duration,
            suspicious_interval_duration,
            suspicious_reasons,
        )
            
        process_logger.info("Frames were processed successfully. Re-encoding output videos...")
        try:
            self.convert_codec(input_path=camera_out_raw, output_path=camera_out)
            self.convert_codec(input_path=screen_out_raw, output_path=screen_out)
        except Exception:
            process_logger.exception("Failed to re-encode output videos.")
            raise
        finally:
            camera_out_raw.unlink(missing_ok=True)
            screen_out_raw.unlink(missing_ok=True)
        
        process_logger.info("Output videos were re-encoded successfully. process_video is done.")
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
        logger.info(f"Received job with payload: {payload}")
        recording_id = str(payload["recording_id"])

        path_screen = payload.get("path_screen")
        path_webcam = payload.get("path_webcam")
        if not path_screen or not path_webcam:
            raise KeyError("payload must contain both 'path_screen' and 'path_webcam'")

        screen_video_path = self._resolve_path(path_screen)
        webcam_video_path = self._resolve_path(path_webcam)

        out_dir = (self._data_dir / "results" / recording_id).resolve()
        out_dir.relative_to(self._data_dir)
        out_dir.mkdir(parents=True, exist_ok=True)

        screen_video = Video(screen_video_path)
        webcam_video = Video(webcam_video_path)

        previous_translation = None
        calibration_result = payload.get("calibration_result")
        if calibration_result:
            result_values = (
                calibration_result.get("result")
                if isinstance(calibration_result, dict)
                else getattr(calibration_result, "result", None)
            )
            if result_values:
                previous_translation = self._apply_calibration_result(result_values)

        try:
            with torch.no_grad():
                intervals: List[Dict[str, Any]] = self.process_video(screen_video, webcam_video, out_dir)
        finally:
            if previous_translation is not None:
                with torch.no_grad():
                    self.gaze_mapper.translation_vec.copy_(previous_translation)
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
