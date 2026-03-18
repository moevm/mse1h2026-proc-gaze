import numpy as np
import torch.nn as nn
import torch

from tqdm import tqdm
from torch.utils.data import DataLoader, Dataset
from typing import List, Tuple

device = torch.device("cuda" if torch.cuda.is_available() else "cpu")

class GazeMapper(nn.Module):
    def __init__(self):
        super().__init__()
        
        # we believe that webcam is on the top and is parallel to the screen surface
        self.rotation_mat = torch.tensor([[-1,  0, 0 ],
                                          [ 0, -1, 0 ],
                                          [ 0,  0, 1 ]], device=device, dtype=torch.float32)
        self.translation_vec = nn.Parameter(torch.tensor([1.0, 1.0, 1.0], device=device, dtype=torch.float32))

    def __calc_lambda(self, gaze_tensor: np.ndarray|torch.Tensor) -> np.float32:
        z_s = torch.tensor([0, 0, 1], device=device, dtype=torch.float32)
        z_g = self.rotation_mat @ z_s
            
        t_g = self.rotation_mat @ self.translation_vec
        l = (z_g @ t_g) / (z_g @ gaze_tensor)
        
        return l.item()
        
    def project(self, gaze_vec: np.ndarray) -> np.ndarray:
        gaze_tensor = torch.tensor(gaze_vec, dtype=torch.float32, device=device)
        l = self.__calc_lambda(gaze_tensor)
        print(l)
        
        return self.rotation_mat @ (l * gaze_tensor) + self.translation_vec
    
class GazeDataset(Dataset):
    def __init__(self, gaze_vectors: List[np.ndarray], real_points: List[np.ndarray]):
        super().__init__()
        
        self.gaze_vecs: List[np.ndarray] = gaze_vectors
        self.points:    List[np.ndarray] = real_points
        
    def __getitem__(self, index: int) -> Tuple[np.ndarray, np.ndarray]: 
        return self.gaze_vecs[index], self.points[index]

    def __len__(self) -> int:
        return len(self.gaze_vecs)
        
def calibrate(n_epochs: int, model: GazeMapper, train_loader: DataLoader, val_loader: DataLoader, verbose: bool=True) -> GazeMapper:
    model = model.to(device)
    
    criterion = nn.MSELoss()
    optimizer = torch.optim.AdamW(model.parameters(), lr=1e-3, weight_decay=1e-4)
    
    for epoch in range(1, n_epochs+1):
        train_bar = tqdm(train_loader, f"Training {epoch}/{n_epochs}")
        model.train()
        train_total = 0.0
        for i, (gaze, point) in enumerate(train_bar, 1):
            proj_point = model.project(gaze)
            
            optimizer.zero_grad()
            loss = criterion(proj_point, point)
            train_total += loss.item()
            loss.backward()
            optimizer.step()

            train_bar.set_postfix_str(f"train_loss: {train_total/i}")
            
        val_bar = tqdm(val_loader, f"Validation {epoch}/{n_epochs}")
        model.eval()
        with torch.no_grad():
            val_total = 0.0
            for i, gaze, point in enumerate(val_bar, 1):
                proj_point = model.project(gaze)
                loss = criterion(proj_point, point)
                val_total += loss.item()

                val_bar.set_postfix_str(f"val_loss: {val_total/i}")
        print()
        