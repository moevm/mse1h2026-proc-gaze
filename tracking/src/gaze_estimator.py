import numpy as np
import openvino as ov
import cv2
import os
import torch
from src.resnet import resnet34
from torchvision.transforms import transforms as T

from typing import List, Tuple, Union
from src.constants import *

core = ov.Core()
device = torch.device("cuda" if torch.cuda.is_available() else "cpu")

ModelType = Union[ov.CompiledModel, torch.nn.Module]

class GazeEstimator:
    def __init__(self, precision_mode: int=0, threshold: float=0.5, use_torch_gaze: bool=False) -> None:        
        self.__precision = PRECISIONS[precision_mode]
        self.__face_detection_threshold = threshold
        self.__use_torch_gaze = use_torch_gaze
        
        self._face_detection_model           = self.__load_model("face_detection")
        self._eyes_countours_detection_model = self.__load_model("eyes_contour_detection")
        self._pupils_detection_model         = self.__load_model("pupils_detection")
        self._head_pose_estimation_model     = self.__load_model("head_pose_estimation")
        self._gaze_vector_estimation_model   = self.__load_model("gaze_vector_estimation")
        
        self.transforms = T.Compose([
            T.ToPILImage(),                     
            T.Resize((448, 448)),
            T.ToTensor(),                
            T.Normalize(
                mean=[0.485, 0.456, 0.406],
                std=[0.229, 0.224, 0.225]
            ),
            ])
        
    def __load_model(self, model_key: str) -> ModelType:
        model_info = MODELS[model_key]
        
        if model_key == "gaze_vector_estimation" and self.__use_torch_gaze:
            full_pth = os.path.join(PTH2MODELS, "resnet", model_info[1] + ".pt")
            if not os.path.exists(full_pth):
                raise FileNotFoundError(f"Torch model not found: {full_pth}")
        
            model = resnet34(pretrained=False, num_classes=90).to(device)
            state_dict = torch.load(full_pth, map_location=device, weights_only=True)
            model.load_state_dict(state_dict)
            model.eval()
            return model
        
        full_pth = os.path.join(PTH2MODELS, "intel", model_info[0], self.__precision, model_info[0] + ".xml")
        
        if not os.path.exists(full_pth):
            raise FileNotFoundError(f"OpenVINO model not found: {full_pth}")
            
        model = core.read_model(full_pth)
        model = core.compile_model(model, "CPU")
        return model
    
    @staticmethod
    def preprocess_image(image: np.ndarray, shape: Tuple[int, int]) -> np.ndarray:
        h, w = shape
        
        resized_image = cv2.resize(image, (w, h))
        rgb_image = resized_image[..., ::-1] # cv2.cvtColor(resized_image, cv2.COLOR_BGR2RGB) same?
        preprocessed = np.transpose(rgb_image, (2, 0, 1)) # C W H
        preprocessed = np.expand_dims(preprocessed, axis=0) # N C W H

        return preprocessed
        
    def __detect_faces(self, image: np.ndarray, shape: Tuple[int, int]) -> List:
        h, w = shape
        model_hw = self._face_detection_model.input(0).shape[2:4]
        
        preprocessed_image = self.preprocess_image(image, model_hw)
        
        output = self._face_detection_model(preprocessed_image)
        output = output[self._face_detection_model.output(0)].squeeze()
        
        faces_data = []
        for _, _, confidence, x_min, y_min, x_max, y_max in output:
            
            if confidence < self.__face_detection_threshold:
                break
            
            x_min, y_min = int(x_min * w), int(y_min * h)
            x_max, y_max = int(x_max * w), int(y_max * h)
            
            cropped = np.copy(image[y_min:y_max, x_min:x_max])
            faces_data.append((cropped, x_min, y_min))
        
        return faces_data

    def __detect_eyes_contours(self, face_image: np.ndarray, shape: Tuple[int, int]) -> Tuple:
        h, w = shape
        
        model_hw = self._eyes_countours_detection_model.input(0).shape[2:4]
        preprocessed_image = self.preprocess_image(face_image, model_hw)
        
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
        preprocessed_image = self.preprocess_image(face_image, model_hw)
        
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
        
        x1, y1, x2, y2 = self.__get_eye_bbox(left_contour, left_pupil, shape, 1.5)
        left_bbox = (x1, y1, x2, y2)
        left_eye = face_image[y1:y2, x1:x2]
                
        x1, y1, x2, y2 = self.__get_eye_bbox(right_contour, right_pupil, shape, 1.5)
        right_bbox = (x1, y1, x2, y2)
        right_eye = face_image[y1:y2, x1:x2]
        
        return left_eye, right_eye, left_pupil, right_pupil, (left_bbox, right_bbox)
        
    def __estimate_head_pose(self, face_image: np.ndarray) -> np.ndarray:
        model_hw = self._head_pose_estimation_model.input(0).shape[2:4]
        preprocessed_image = self.preprocess_image(face_image, model_hw)
        
        output = np.array([v.squeeze().item() for v in self._head_pose_estimation_model(preprocessed_image).values()])
        
        return np.expand_dims(output, axis=0)
    
    def __estimate_gaze_vec_vino(self, eyes: Tuple, angles: np.ndarray) -> np.ndarray:
        left_eye, right_eye = eyes
        
        if any([s == 0 for s in left_eye.shape]) or any([s == 0 for s in right_eye.shape]) :
            return [0, 0, 0] 
        
        model_hw = self._gaze_vector_estimation_model.input(0).shape[2:4]
        
        preprocessed_left  = self.preprocess_image(left_eye, model_hw)
        preprocessed_right = self.preprocess_image(right_eye, model_hw)
        
        output = self._gaze_vector_estimation_model((preprocessed_left, preprocessed_right, angles))
        output = output[self._gaze_vector_estimation_model.output(0)].squeeze()

        l = np.linalg.norm(output)
        output /= l if l != 0 else 1
        
        output *= np.array([1, -1, -1])
        
        return output

    @torch.no_grad()
    def __estimate_gaze_vec_torch(self, face: np.ndarray) -> np.ndarray:
        if any([s == 0 for s in face.shape]):
            return np.array([0, 0, 0], dtype=np.float32) 
        
        face_rgb = face[..., ::-1]
        face_tensor = self.transforms(face_rgb).unsqueeze(0).to(device)
        
        yaw_logits, pitch_logits = self._gaze_vector_estimation_model(face_tensor)

        yaw_probs   = torch.softmax(yaw_logits,   dim=1)
        pitch_probs = torch.softmax(pitch_logits, dim=1)
        
        idx_tensor = torch.arange(90, dtype=torch.float32, device=device)
        
        yaw_pred   = torch.sum(yaw_probs   * idx_tensor, dim=1) # math expectation formula \sum{x * p(x)}
        pitch_pred = torch.sum(pitch_probs * idx_tensor, dim=1) # math expectation
        
        # 1 bin = 4 degree; yaw_pred = math expectation of 90 bins => 90 bins = 360 degree; degree \in [0, 360] - 180 = [-180; +180]
        yaw_deg   = yaw_pred   * 4.0 - 180.0
        pitch_deg = pitch_pred * 4.0 - 180.0
        
        # degrees into radians
        yaw_rad = np.deg2rad(yaw_deg.item())
        pitch_rad = np.deg2rad(pitch_deg.item())
        
        # aircraft principal axes to cartesian
        x = -np.cos(pitch_rad) * np.sin(yaw_rad)
        y = -np.sin(pitch_rad)
        z = np.cos(pitch_rad) * np.cos(yaw_rad)
        
        gaze_vec = np.array([x, y, z])
        norm = np.linalg.norm(gaze_vec)
        
        gaze_vec /= norm if norm != 0 else 1
        return gaze_vec
    
    def estimate(self, frame: np.ndarray) -> Tuple[List, List, List, List]:
        vid_h, vid_w = frame.shape[:2] # opencv image shape h w c
        faces = self.__detect_faces(frame, (vid_h, vid_w))
        
        gaze_vecs = [] 
        pupils    = []
        offsets   = []
        eyes_bbox = []
        
        for face, x_offset, y_offset in faces:
            if any([s == 0 for s in face.shape]):
                return [], [], [], []
            
            h, w = face.shape[:2]
            left_eye, right_eye, left_pupil, right_pupil, bbox = self.__detect_eyes(face, (h, w))
            
            angles = self.__estimate_head_pose(face)
            
            if not self.__use_torch_gaze:
                gaze_vec = self.__estimate_gaze_vec_vino((left_eye, right_eye), angles)
            else:
                gaze_vec = self.__estimate_gaze_vec_torch(face)
            
            gaze_vecs.append(gaze_vec)
            pupils.append((left_pupil, right_pupil))
            offsets.append((x_offset, y_offset))
            eyes_bbox.append(bbox)
            
        return gaze_vecs, pupils, offsets, eyes_bbox
        