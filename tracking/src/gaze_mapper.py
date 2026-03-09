import numpy as np
import torch.nn as nn
import torch

device = torch.device("cuda" if torch.cuda.is_available() else "cpu")

class GazeMapper(nn.Module):
    def __init__(self):
        # we believe that webcam is on the top and is parallel to the screen surface
        self.rotation_mat = np.ndarray([[-1,  0, 0],
                                        [ 0, -1, 0],
                                        [ 0,  0, 1]])
        self.shift_vector = nn.Parameter(torch.Tensor([0, 0, 0], device=device))

    def __calc_lambda(self, gaze_vec: np.ndarray) -> np.float32:
        z_s = np.array([0, 0, 1])
        z_g = np.dot(self.rotation_mat, z_s)
        
        t_g = np.dot(self.rotation_mat, self.shift_vector)
        l = np.dot(z_g, t_g) / np.dot(z_g, gaze_vec)
        
        return l
        
    def project(self, gaze_vec: np.ndarray) -> np.ndarray:
        l = self.__calc_lambda(gaze_vec)
        
        return np.dot(self.rotation_mat, l*gaze_vec) + self.shift_vector
    
    def calibrate(self) -> None:
        pass
    