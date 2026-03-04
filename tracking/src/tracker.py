import numpy as np
import openvino as ov
import cv2
import os
import matplotlib.pyplot as plt

from typing import List, Tuple

from src.utils import *

core = ov.Core()

class Tracker:
    def __init__(self, precision_mode: int=0, threshold: float=0.5) -> None:        
        self.__precision = PRECISIONS[precision_mode]
        self._face_detection_threshold = threshold
        
        self._face_detection_model           = self.__load_model(MODELS["face_detection"][0])
        self._eyes_countours_detection_model = self.__load_model(MODELS["eyes_contour_detection"][0])
        self._pupils_detection_model         = self.__load_model(MODELS["pupils_detection"][0])
        self._head_pose_estimation_model     = self.__load_model(MODELS["head_pose_estimation"][0])
        self._gaze_vector_estimation_model   = self.__load_model(MODELS["gaze_vector_estimation"][0])
        
    def __load_model(self, model_name: str) -> ov.CompiledModel:
        full_pth = os.path.join(PTH2MODELS, model_name, self.__precision, model_name + ".xml")
        
        model = core.read_model(full_pth)
        model = core.compile_model(model, "CPU")
        
        return model
    
    def __preprocess_image(self, image: np.ndarray, shape: Tuple[int, int]) -> np.ndarray:
        h, w = shape
        
        resized_image = cv2.resize(image, (w, h))
        rgb_image = cv2.cvtColor(resized_image, cv2.COLOR_BGR2RGB)
        preprocessed = np.transpose(rgb_image, (2, 0, 1)) # C W H
        preprocessed = np.expand_dims(preprocessed, axis=0) # N C W H

        return preprocessed
        
    def __detect_faces(self, image: np.ndarray, shape: Tuple[int, int]) -> List:
        h, w = shape
        model_hw = self._face_detection_model.input(0).shape[2:4]
        
        preprocessed_image = self.__preprocess_image(image, model_hw)
        
        output = self._face_detection_model(preprocessed_image)
        output = output[self._face_detection_model.output(0)].squeeze()
        
        faces_data = []
        for _, _, confidence, x_min, y_min, x_max, y_max in output:
            
            if confidence < self._face_detection_threshold:
                break
            
            x_min, y_min = int(x_min * w), int(y_min * h)
            x_max, y_max = int(x_max * w), int(y_max * h)
            
            cropped = np.copy(image[y_min:y_max, x_min:x_max])
            faces_data.append((cropped, x_min, y_min))
        
        return faces_data

    def __detect_eyes_contours(self, face_image: np.ndarray, shape: Tuple[int, int]) -> Tuple:
        h, w = shape
        
        model_hw = self._eyes_countours_detection_model.input(0).shape[2:4]
        preprocessed_image = self.__preprocess_image(face_image, model_hw)
        
        output = self._eyes_countours_detection_model(preprocessed_image)
        output = output[self._eyes_countours_detection_model.output(0)].squeeze()
        
        landmarks = self.__extract_landmarks(output)
        
        heatmap_size = output[0].shape[0]
        
        eyes_points = np.array([(int(x * w / heatmap_size), int(y * h / heatmap_size)) for x, y in landmarks[EYE_INDICES]])

        return eyes_points[LEFT_EYE_INDICES], eyes_points[RIGHT_EYE_INDICES]
        
    def __extract_landmarks(self, heatmaps: np.ndarray) -> np.ndarray:
        landmarks = []
        
        for i in range(len(heatmaps)):
                heatmap = heatmaps[i]
                
                max_idx = np.unravel_index(np.argmax(heatmap), heatmap.shape)
                max_val = heatmap[max_idx]
                
                if max_val < 0:
                    landmarks.append(None)
                    continue
                    
                h_idx, w_idx = max_idx
                
                x = w_idx
                y = h_idx
                
                landmarks.append((x, y))
                
        return np.array(landmarks)
    
    def __detect_pupils(self, face_image: np.ndarray, shape: Tuple[int, int]) -> Tuple:
        h, w = shape
        
        model_hw = self._pupils_detection_model.input(0).shape[2:4]
        preprocessed_image = self.__preprocess_image(face_image, model_hw)
        
        output = self._pupils_detection_model(preprocessed_image)
        output = output[self._pupils_detection_model.output(0)].squeeze()
        
        left_pupil  = (int(output[0] * w), 
                       int(output[1] * h))
        
        right_pupil = (int(output[2] * w), 
                       int(output[3] * h))
        
        return left_pupil, right_pupil

    def __get_eye_bbox(self, contour: np.ndarray, pupil: np.ndarray, image_shape: np.ndarray|Tuple, padding: float=1.0) -> np.ndarray:
        min_x, max_x = np.min(contour[:, 0]), np.max(contour[:, 0])
        min_y, max_y = np.min(contour[:, 1]), np.max(contour[:, 1])
        
        width = max_x - min_x
        height = max_y - min_y
        size = max(width, height) * padding
        
        half_size = size / 2.0
        x1 = int(pupil[0] - half_size)
        y1 = int(pupil[1] - half_size)
        x2 = int(pupil[0] + half_size)
        y2 = int(pupil[1] + half_size)
        
        x1 = max(0, x1)
        y1 = max(0, y1)
        x2 = min(image_shape[0], x2)
        y2 = min(image_shape[1], y2)
        
        return np.array([x1, y1, x2, y2])
    
    def __detect_eyes(self, face_image: np.ndarray, shape: Tuple[int, int]) -> Tuple:
        left_pupil, right_pupil     = self.__detect_pupils(face_image, shape)
        left_contour, right_contour = self.__detect_eyes_contours(face_image, shape)
        
        x1, y1, x2, y2 = self.__get_eye_bbox(left_contour, left_pupil, shape)
        left_eye = face_image[y1:y2, x1:x2]
                
        x1, y1, x2, y2 = self.__get_eye_bbox(right_contour, right_pupil, shape)
        right_eye = face_image[y1:y2, x1:x2]
        
        return left_eye, right_eye, left_pupil, right_pupil
        
    def __estimate_head_pose(self, face_image: np.ndarray) -> np.ndarray:
        model_hw = self._head_pose_estimation_model.input(0).shape[2:4]
        preprocessed_image = self.__preprocess_image(face_image, model_hw)
        
        output = np.array([v.squeeze().item() for v in self._head_pose_estimation_model(preprocessed_image).values()])
        
        return np.expand_dims(output, axis=0)
    
    def __estimate_gaze_vec(self, eyes: Tuple, angles: np.ndarray) -> np.ndarray:
        left_eye, right_eye = eyes
        
        model_hw = self._gaze_vector_estimation_model.input(0).shape[2:4]
        
        preprocessed_left  = self.__preprocess_image(left_eye, model_hw)
        preprocessed_right = self.__preprocess_image(right_eye, model_hw)
        
        output = self._gaze_vector_estimation_model((preprocessed_left, preprocessed_right, angles))
        output = output[self._gaze_vector_estimation_model.output(0)].squeeze()
        
        l = np.linalg.norm(output)
        if l != 0:
            output = output / l
        
        return output
    
    def __draw_landmarks(self, face_image: np.ndarray, points: List) -> np.ndarray:
        for p in points:
            cv2.circle(face_image, p, 2, (255, 0, 0), 2)
        return face_image
    
    def process_frame(self, frame: np.ndarray) -> np.ndarray:
        vid_h, vid_w = frame.shape[:2] # opencv image shape h w c
        faces = self.__detect_faces(frame, (vid_h, vid_w))
        
        res = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        for face, x_offset, y_offset in faces:
            h, w = face.shape[:2]
            left_eye, right_eye, left_pupil, right_pupil = self.__detect_eyes(face, (h, w))
            
            angles = self.__estimate_head_pose(face)
            
            gaze_vec = self.__estimate_gaze_vec((left_eye, right_eye), angles)
            
            l = 25

            rx, ry = right_pupil
            lx, ly = left_pupil
            
            sx, sy = int((rx+lx)/2), int((ry+ly)/2)
            
            vx, vy = gaze_vec[:2]
            
            ex, ey = sx + vx * l, sy + vy * l
            
            global_start = (int(sx + x_offset), int(sy + y_offset))
            global_end = (int(ex + x_offset), int(ey + y_offset))
            
            cv2.arrowedLine(res, global_start, global_end, (255, 0, 0), 2)
            
        return res
    
    def process_video(self, video) -> None:
        pass
