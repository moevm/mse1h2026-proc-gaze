from src.utils import *
from src.gaze_estimator import *
from src.gaze_mapper import *

class Tracker:
    def __init__(self, precision_mode: int=0, threshold: float=0.5) -> None:        
        self.gaze_estimator = GazeEstimator(precision_mode, threshold)
        self.gaze_mapper    = GazeMapper()
    
    def __draw_landmarks(self, face_image: np.ndarray, points: List) -> np.ndarray:
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
                self.__draw_landmarks(res, [(left_pupil[0] + x_offset, left_pupil[1] + y_offset),
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
        
        fourcc = cv2.VideoWriter_fourcc(*'mp4v')
        out = cv2.VideoWriter('output.mp4', fourcc, 20.0, (frame_width, frame_height))
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
