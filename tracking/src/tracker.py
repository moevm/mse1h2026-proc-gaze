from constants import *
from gaze_estimator import *
from gaze_mapper import *

import json
import os
from pathlib import Path
from typing import Any, Optional

from constants import JOB_STATUS_DONE, JOB_STATUS_FAILED, JOB_STATUS_IN_PROGRESS
from video import Video


class Tracker:
    def __init__(self, precision_mode: int=0, threshold: float=0.5) -> None:        
        self._data_dir = Path(os.environ.get("DATA_DIR", "../preprocessed")).resolve()
        self.gaze_estimator = GazeEstimator(precision_mode, threshold)
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
        
        print(f"DEBUG: proj_p raw = {proj_p}")
        
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

    def process_video(self, screen_video: Video, camera_video: Video, out_dir: Optional[Path] = None) -> dict[str, str]:
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
        
        camera_writer = cv2.VideoWriter(f"{out_dir}/camera.mp4", cv2.VideoWriter_fourcc(*"mp4v"), camera_video.fps, (camera_video._width, camera_video._height))
        screen_writer = cv2.VideoWriter(f"{out_dir}/screen.mp4", cv2.VideoWriter_fourcc(*"mp4v"), 30.0, (screen_video._width, screen_video._height))
        
        for camera_frame, screen_frame in zip(camera_video, screen_video):
            processed_camera_frame = self.process_camera_frame(camera_frame, True)
            processed_screen_frame = self.process_screen_frame(screen_frame, camera_frame)
            camera_writer.write(processed_camera_frame)
            screen_writer.write(processed_screen_frame)
        camera_writer.release()
        screen_writer.release()

        info_path = out_dir / "video_info.json"
        info_path.write_text(json.dumps(camera_video.info, ensure_ascii=False, indent=2), encoding="utf-8")

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
                "job_id": "123",
                "inputs": {
                    "screen_video": "uploads/screen.mp4",
                    "webcam_video": "uploads/webcam.mp4"
                }
            }

        Перед началом обработки в results/<job_id>/status.json записывается
        промежуточный статус IN_PROGRESS. После успешного завершения статус
        обновляется на DONE, а при ошибке — на FAILED.

        Формат результата:
            {
                "job_id": "123",
                "status": "DONE",
                "outputs": {
                    "screen_video": {
                        "video_info": "results/123/screen_video/video_info.json",
                        "trajectory": "results/123/screen_video/trajectory.json"
                    },
                    "webcam_video": {
                        "video_info": "results/123/webcam_video/video_info.json",
                        "trajectory": "results/123/webcam_video/trajectory.json"
                    }
                }
            }
        """
        job_id = str(payload["job_id"])
        inputs = payload.get("inputs") or {}

        screen_video_path = inputs.get("screen_video")
        webcam_video_path = inputs.get("webcam_video")

        if not screen_video_path or not webcam_video_path:
            raise KeyError("payload.inputs must contain both 'screen_video' and 'webcam_video'")

        out_dir = (self._data_dir / "results" / job_id).resolve()
        out_dir.relative_to(self._data_dir)
        out_dir.mkdir(parents=True, exist_ok=True)

        status_path = out_dir / "status.json"
        status_path.write_text(
            json.dumps(
                {
                    "job_id": job_id,
                    "status": JOB_STATUS_IN_PROGRESS,
                },
                ensure_ascii=False,
                indent=2,
            ),
            encoding="utf-8",
        )

        outputs: dict[str, Any] = {}

        try:
            for input_name, input_path in {
                "screen_video": screen_video_path,
                "webcam_video": webcam_video_path,
            }.items():
                video_path = self._resolve_path(str(input_path))
                source_out_dir = out_dir / input_name

                with Video(video_path) as v:
                    outputs[input_name] = self.process_video(v, out_dir=source_out_dir)

            result = {"job_id": job_id, "status": JOB_STATUS_DONE, "outputs": outputs}

            status_path.write_text(
                json.dumps(result, ensure_ascii=False, indent=2),
                encoding="utf-8",
            )

            return result

        except Exception:
            status_path.write_text(
                json.dumps(
                    {
                        "job_id": job_id,
                        "status": JOB_STATUS_FAILED,
                    },
                    ensure_ascii=False,
                    indent=2,
                ),
                encoding="utf-8",
            )
            raise

if __name__ == "__main__":
    tracker = Tracker()
    tracker.gaze_mapper = torch.load("../models/other/mapper.pth", map_location=device, weights_only=False)
    tracker.gaze_mapper.eval()
    print(tracker.gaze_mapper.translation_vec)
    
    screen_video = Video("/home/berlet/screen.mp4")
    cam_video = Video("/home/berlet/webcam.mp4")
    with torch.no_grad():
        tracker.process_video(screen_video, cam_video, Path("../preprocessed"))
    