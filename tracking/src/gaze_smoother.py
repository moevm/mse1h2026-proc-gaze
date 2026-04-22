import numpy as np
from filterpy.kalman import KalmanFilter

class BaseGazeSmoother:
    def __init__(self):
        pass
    
    def update(self, raw_point: np.ndarray) -> np.ndarray:
        raise NotImplementedError

class GazeSmoother(BaseGazeSmoother):
    def __init__(self, alpha: float = 0.5) -> None:
        self.alpha: float = alpha
        self.prev_point: np.ndarray = None
    
    def update(self, raw_point: np.ndarray) -> np.ndarray:
        if self.prev_point is None:
            self.prev_pos = raw_point.copy()
            return self.prev_pos
        
        smoothed_point = self.alpha * raw_point + (1 - self.alpha) * self.prev_point
        
        self.prev_point = smoothed_point
        
        return smoothed_point

class GazeKalmanSmoother(BaseGazeSmoother):
    def __init__(self, dt: float = 1/60.0, process_var: float = 0.5, measurement_var: float = 1.0, x0: np.ndarray = None):
        self.kf = KalmanFilter(4, 2)
        self.dt = dt
        self.kf.F = np.array([
                    [1, 0, dt, 0],
                    [0, 1, 0, dt],
                    [0, 0, 1,  0],
                    [0, 0, 0,  1]
                ])
        
        self.kf.H = np.array([
            [1, 0, 0, 0],
            [0, 1, 0, 0]
        ])
        
        self.kf.P = np.eye(4) * 1000
        
        self.kf.Q = np.array([
            [dt**4/4, 0,      dt**3/2, 0],
            [0,      dt**4/4, 0,       dt**3/2],
            [dt**3/2, 0,      dt**2,   0],
            [0,      dt**3/2, 0,       dt**2]
        ]) * process_var
        
        self.kf.R = np.eye(2) * measurement_var
        
        if x0 is not None:
            self.kf.x = np.array([x0[0], x0[1], 0, 0]).reshape(4, 1)
        else:
            self.kf.x = np.zeros((4, 1))
        
        self.initialized = x0 is not None
    
    def update(self, raw_point: np.ndarray) -> np.ndarray:
        if not self.initialized:
            self.kf.x = np.array([raw_point[0], raw_point[1], 0, 0]).reshape(4, 1)
            self.initialized = True
            return raw_point.copy()
        
        self.kf.update(raw_point)
        return self.kf.x[:2].flatten()

class AdaptiveGazeKalmanSmoother(GazeKalmanSmoother):
    def __init__(
        self, dt: float = 1/60.0, process_var: float = 0.5, measurement_var: float = 1.0, saccade_threshold: float = 100.0, saccade_factor: float = 5.0
    ):
        super().__init__(dt, process_var, measurement_var)
        self.saccade_threshold = saccade_threshold
        self.saccade_factor = saccade_factor
        self.base_R = np.eye(2) * measurement_var
        self.prev_pos = None
        
    def update(self, measurement: np.ndarray) -> np.ndarray:
        if not self.initialized:
            self.kf.x = np.array([measurement[0], measurement[1], 0, 0]).reshape(4, 1)
            self.initialized = True
            self.prev_pos = measurement.copy()
            return measurement.copy()
        
        if self.prev_pos is not None:
            velocity = np.linalg.norm(measurement - self.prev_pos) / self.dt
            if velocity > self.saccade_threshold:
                self.kf.R = self.base_R / self.saccade_factor
            else:
                self.kf.R = self.base_R
        
        self.kf.update(measurement)
        self.prev_pos = self.kf.x[:2].flatten().copy()
        return self.prev_pos