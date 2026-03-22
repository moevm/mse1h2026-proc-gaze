import numpy as np
import torch.nn as nn
import torch

device = torch.device("cuda" if torch.cuda.is_available() else "cpu")

class GazeMapper(nn.Module):
    def __init__(self):
        super().__init__()
        
        # we believe that webcam is on the top and is parallel to the screen surface
        self.rotation_mat = torch.tensor([[-1,  0, 0 ],
                                          [ 0, -1, 0 ],
                                          [ 0,  0, 1 ]], device=device, dtype=torch.float32)
        self.translation_vec = nn.Parameter(torch.tensor([1.0, 1.0, 1.0], device=device, dtype=torch.float32))

    def __calc_lambda(self, gaze_vec: np.ndarray|torch.Tensor) -> np.float32:
        z_s = torch.tensor([0, 0, 1], device=device, dtype=torch.float32)
        z_g = self.rotation_mat @ z_s
        
        if isinstance(gaze_vec, np.ndarray):
            gaze_tensor = torch.tensor(gaze_vec, device=device, dtype=torch.float32)
        else: 
            gaze_tensor = gaze_vec
            
        t_g = self.rotation_mat @ self.translation_vec
        result = (z_g @ t_g) / (z_g @ gaze_tensor)
        
        return result.item()
        
    def project(self, gaze_vec: np.ndarray) -> np.ndarray:
        gaze_tensor = torch.tensor(gaze_vec, dtype=torch.float32, device=device)
        l = self.__calc_lambda(gaze_vec)
        print(l)
        
        return self.rotation_mat @ (l * gaze_tensor) + self.translation_vec
    
    def calibrate(self) -> None:
        pass
    