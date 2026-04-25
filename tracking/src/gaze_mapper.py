import numpy as np
import torch.nn as nn
import torch

from tqdm import tqdm
from torch.utils.data import DataLoader, Dataset
from typing import List, Tuple

from torchmin.optim import Minimizer

device = torch.device("cuda" if torch.cuda.is_available() else "cpu")

class GazeMapper(nn.Module):
    def __init__(self):
        super().__init__()
        
        # we believe that webcam is on the top and is parallel to the screen surface
        self.rotation_mat = torch.tensor([[-1,  0, 0 ],
                                          [ 0, -1, 0 ],
                                          [ 0,  0, 1 ]], device=device, dtype=torch.float32, requires_grad=False)
        self.translation_vec = nn.Parameter(torch.tensor([1500.0, 1000.0, 4000.0], device=device, dtype=torch.float32), requires_grad=True)

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
    
def compute_rmse(model: GazeMapper, loader: DataLoader) -> float:
    total_sq_error = 0.0
    n_samples = 0
    
    for vec, point in loader:
        vec = vec.to(device)
        point = point.to(device)
        output = model.project(vec)
        total_sq_error += torch.sum((point - output) ** 2).item()
        n_samples += point.size(0)
        
    return (total_sq_error / n_samples) ** 0.5
        
def calibrate(n_epochs: int, model: GazeMapper, train_loader: DataLoader, val_loader: DataLoader, verbose: bool=True) -> GazeMapper:
    model = model.to(device).train()

    optimizer = Minimizer(model.parameters(), method="bfgs", max_iter=n_epochs, tol=1e-9, disp=2 if verbose else 0)
    
    def closure() -> torch.Tensor:
        optimizer.zero_grad()
        total_sq_error = torch.tensor(0.0, device=device)
        n_samples = 0
        
        for vec, point in train_loader:
            vec = vec.to(device)
            point = point.to(device)
            output = model.project(vec)
            
            total_sq_error += torch.sum((point - output) ** 2)
            n_samples += point.size(0)
        l2_reg = torch.sum(torch.stack([p.pow(2).sum() for p in model.parameters()]))
        mse = total_sq_error / n_samples
        return mse + 1e-3 * l2_reg
    
    final_mse = optimizer.step(closure)
    
    model.eval()
    with torch.no_grad():
        train_rmse = compute_rmse(model, train_loader)
        val_rmse = compute_rmse(model, val_loader)
        
    if verbose:
        print(f"Optimization finished. Final MSE: {final_mse.item():.6f}")
        print(f"Train RMSE: {train_rmse:.6f} | Val RMSE: {val_rmse:.6f}")
        
    return model

def calibrate_stochastic(n_epochs: int, model: GazeMapper, train_loader: DataLoader, val_loader: DataLoader, verbose: bool=True) -> GazeMapper:
    model = model.to(device)
    
    optimizer = torch.optim.Adafactor(model.parameters(), lr=1e-3)
    
    for epoch in range(1, n_epochs+1):
        train_bar = tqdm(train_loader, f"Training {epoch}/{n_epochs}")
        model.train()
        train_total = 0.0
        for i, (gaze, point) in enumerate(train_bar, 1):
            gaze = gaze.float().to(device)
            point = point.float().to(device).squeeze() 
            
            proj_point = model.project(gaze)
            
            optimizer.zero_grad()
            loss = torch.sum((point - proj_point) ** 2)
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
                loss = torch.sum((point - proj_point) ** 2)
                val_total += loss.item()

                val_bar.set_postfix_str(f"val_loss: {val_total/i:.4f}")
                
    model.eval()
    with torch.no_grad():
        train_rmse = compute_rmse(model, train_loader)
        val_rmse = compute_rmse(model, val_loader)
        
    if verbose:
        print(f"Optimization finished. Final MSE: {train_total:.6f}")
        print(f"Train RMSE: {train_rmse:.6f} | Val RMSE: {val_rmse:.6f}")
            
    return model