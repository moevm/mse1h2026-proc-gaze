import numpy as np
import torch.nn as nn
import torch

from tqdm import tqdm
from torch.utils.data import DataLoader, Dataset
from typing import List, Tuple
from .video import Video

from torch.utils.data import random_split
import os

from .gaze_estimator import GazeEstimator

device = torch.device("cuda" if torch.cuda.is_available() else "cpu")

class GazeMapper(nn.Module):
    def __init__(self):
        super().__init__()
        
        # we believe that webcam is on the top and is parallel to the screen surface
        self.rotation_mat = torch.tensor([[-1,  0, 0 ],
                                          [ 0, -1, 0 ],
                                          [ 0,  0, 1 ]], device=device, dtype=torch.float32, requires_grad=False)
        self.translation_vec = nn.Parameter(torch.randn(3, device=device), requires_grad=True)

    def __calc_lambda(self, gaze_tensor: np.ndarray|torch.Tensor) -> np.float32:
        z_s = torch.tensor([0, 0, 1], device=device, dtype=torch.float32)
        z_g = self.rotation_mat @ z_s
            
        t_g = -self.rotation_mat @ self.translation_vec
        l = (z_g @ t_g) / (z_g @ gaze_tensor)
        
        return l
        
    def project(self, gaze_vec: np.ndarray) -> np.ndarray:
        gaze_tensor = torch.as_tensor(gaze_vec, dtype=torch.float32, device=device).squeeze()
        l = self.__calc_lambda(gaze_tensor)

        return self.rotation_mat @ (l * gaze_tensor) + self.translation_vec
    
class GazeDataset(Dataset):
    def __init__(self, data: List[Tuple[np.ndarray, np.ndarray]]):
        super().__init__()
        
        self.data: List[Tuple[np.ndarray, np.ndarray]] = data
        
    def __getitem__(self, index: int) -> Tuple[np.ndarray, np.ndarray]: 
        return self.data[index]

    def __len__(self) -> int:
        return len(self.data)
        
def calibrate(n_epochs: int, model: GazeMapper, train_loader: DataLoader, val_loader: DataLoader, verbose: bool=True) -> GazeMapper:
    model = model.to(device)
    
    criterion = nn.MSELoss()
    optimizer = torch.optim.Adam(model.parameters(), lr=0.3)
    scheduler = torch.optim.lr_scheduler.ReduceLROnPlateau(optimizer, factor=0.5)
    
    for epoch in range(1, n_epochs+1):
        train_bar = tqdm(train_loader, f"Training {epoch}/{n_epochs}")
        model.train()
        train_total = 0.0
        for i, (gaze, point) in enumerate(train_bar, 1):
            gaze = gaze.float().to(device)
            point = point.float().to(device).squeeze() 
            
            proj_point = model.project(gaze)
            
            optimizer.zero_grad()
            loss = criterion(proj_point, point)
            train_total += loss.item()
            loss.backward()
            optimizer.step()

            train_bar.set_postfix_str(f"train_loss: {train_total/i:.4f}")
            
        val_bar = tqdm(val_loader, f"Validation {epoch}/{n_epochs}")
        model.eval()
        with torch.no_grad():
            val_total = 0.0
            for i, (gaze, point) in enumerate(val_bar, 1):
                gaze = gaze.float().to(device)
                point = point.float().to(device).squeeze() 
                
                proj_point = model.project(gaze)
                loss = criterion(proj_point, point)
                val_total += loss.item()

                val_bar.set_postfix_str(f"val_loss: {val_total/i:.4f}")
        print()
        
    return model

if __name__ == "__main__":
    mapper = GazeMapper()
    gaze_estimator = GazeEstimator(use_torch_gaze=True)
    
    vids = [Video(os.path.join("../calibration", p)) for p in os.listdir("../calibration") if not ".txt" in p]
    file = open("../calibration/points.txt", "r", encoding="utf-8")
    points = [np.array(list(map(float, l.split()))) for l in file.readlines()]
    
    data = []
    for v, p in zip(vids, points):
        vecs = []
        for frame in v:
            gaze_vec, _, _, _ = gaze_estimator.estimate(frame)
            vecs.append((gaze_vec[0], p))
            
        data.extend(vecs)
    
    dataset = GazeDataset(data)
    
    g = torch.Generator().manual_seed(0)
    train, val = random_split(dataset, [0.9, 0.1], g)
    
    train_loader = DataLoader(train, batch_size=1, shuffle=True, num_workers=2, pin_memory=True)
    val_loader = DataLoader(val, batch_size=1, shuffle=True, num_workers=2, pin_memory=True)
    
    epochs = 200
    mapper = calibrate(epochs, mapper, train_loader, val_loader)
    
    torch.save(mapper, "../models/other/mapper.pth")