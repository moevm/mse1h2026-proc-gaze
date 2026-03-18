import cv2
import tkinter as tk
from typing import List, Tuple
import time

class Calibration(tk.Tk):
    def __init__(self, n_points: int=4, duration:float = 2.5):
        super().__init__()
        self.resizable = False, False
        self.attributes("-fullscreen", True)
        
        w, h = self.winfo_screenwidth(), self.winfo_screenheight()
        self.canvas = tk.Canvas(self, width=w, height=h, bg='white')
        self.canvas.pack(fill=tk.BOTH, expand=True)
        
        # points on screen for calibration
        self.n_points = n_points
        self.points = self.gen_points(n_points)

        self.records = 0
        self.duration = duration
        self.is_recording = False
        
        self.bind("q", self.close)
        self.bind("r", self.record)
        self.__dump_points()

    def __dump_points(self) -> None:
        with open("../calibration/points.txt", "w+", encoding="utf-8") as f:
            for p in self.points:
                x, y = p
                f.write(f"{x} {y}\n")
    
    def gen_points(self, n_points: int) -> List:
        res = []
        
        w, h = self.winfo_screenwidth(), self.winfo_screenheight()
        margin = 0.1
        
        left_top = (margin * w, margin * h)
        left_bot = (margin * w, h - margin * h)
        right_top = (w - margin * w, margin * h)
        right_bot = (w - margin * w, h - margin * h)
        
        res.extend([left_top, left_bot, right_top, right_bot])
        return res[:n_points]
        
    def draw_point(self, point: Tuple) -> None:
        x, y = point
        self.canvas.delete("all")
        self.canvas.create_oval(x, y, x+10, y+10, outline="red", fill="red")
        self.update_idletasks()
        self.update()
        
    def close(self, event: tk.Event) -> None:
        self.destroy()
        
    def record(self, event: tk.Event) -> None:
        if self.n_points > self.records:
            if self.is_recording:
                print("still recording")
                return
            point = self.points[self.records]
            self.draw_point(point)
            
            time.sleep(1.0)
            print("recording")
            self.__record_video()
            self.records += 1
        else:
            self.canvas.delete("all")
            self.destroy()
    
    def __record_video(self) -> None:    
        start_time = time.time()
        
        
        cap = cv2.VideoCapture(0)
        width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
        height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
        fps = int(cap.get(cv2.CAP_PROP_FPS)) or 30
        w, h = self.winfo_screenwidth(), self.winfo_screenheight() 
        
        writer = cv2.VideoWriter(f"../calibration/calibration_{self.records}.mp4", cv2.VideoWriter_fourcc(*"mp4v"), fps, (width, height))
        t = 0.0
        
        while True:
            ret, frame = cap.read()
            
            if not ret:
                break
                
            t = time.time() - start_time
            writer.write(frame)
            self.canvas.delete("text")
            self.canvas.create_text(w // 2, h // 2, text=f"Time: {t:.4f}", fill="red", font=("Helvetica", 24, "bold"), tags="text")
            self.canvas.update()
            self.update_idletasks()
            
            if t >= self.duration:
                break
        
        self.canvas.create_text(w // 2, h // 2, text=f"Time: {t:.4f}", fill="green", font=("Helvetica", 24, "bold"))
        
        cap.release()
        writer.release()

if __name__ == "__main__":
    cal = Calibration()
    cal.mainloop()