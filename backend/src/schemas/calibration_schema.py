import uuid
from typing import List

from pydantic import BaseModel, Field

class Click(BaseModel):
    time: float = Field(..., description="Время нажатия на круг в секундах")
    x: int = Field(..., description="Y координата круга относительно окна браузера")
    y: int = Field(..., description="X координата круга относительно окна браузера")


class CalibrationData(BaseModel):
    window_width: int = Field(..., description="Ширина окна браузера")
    window_height: int = Field(..., description="Высота окна браузера")
    screen_width: int = Field(..., description="Ширина всего экрана")
    screen_height: int = Field(..., description="Высота всего экрана")
    window_screen_x: int = Field(..., description="Положение окна браузера относительно левого верхнего края экрана по оси X")
    window_screen_y: int = Field(..., description="Положение окна браузера относительно левого верхнего края экрана по оси Y")
    clicks: List[Click] = Field(..., description="Данные кликов")


class CalibrationRead(BaseModel):
    student_id: uuid.UUID = Field(..., description="UUID студента")
    webcam_path: str = Field(..., description="Путь к видеокамере")
    screencast_path: str = Field(..., description="Путь к скринкасту")
    calibration_data: CalibrationData = Field(..., description="Данные калибровки")