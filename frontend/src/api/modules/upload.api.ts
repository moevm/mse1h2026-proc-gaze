import { apiFileClient } from '../config'
import type { ApiResponse } from '../config'
import {T} from "vue-router/dist/index-DFCq6eJK";

interface CalibrationData {
    windowWidth: number;
    windowHeight: number;
    screenWidth: number;
    screenHeight: number;
    windowScreenX: number;
    windowScreenY: number;
    clicks: Array<{ time: number; x: number; y: number }>;
}

class UploadApi {
    async upload(studentId: string, webcam: File, screencast: File): Promise<ApiResponse<any>> {
        const formData = new FormData();
        formData.append('student_id', studentId);
        formData.append('webcam', webcam);
        formData.append('screencast', screencast);

        const response = await apiFileClient.post<ApiResponse<T>>('/recording/upload', formData, {
            headers: {
            'Content-Type': 'multipart/form-data'
            }
        });
        return response.data;
    }

    async uploadCalibration(studentId: string, webcamBlob: Blob, screenBlob: Blob,
                            calibrationData: CalibrationData): Promise<ApiResponse<any>> {
        const formData = new FormData();
        formData.append('student_id', studentId);
        formData.append('webcam_video', webcamBlob, 'webcam.webm');
        formData.append('screen_video', screenBlob, 'screen.webm');
        formData.append('calibration_data', JSON.stringify(calibrationData));

        const response = await apiFileClient.post<ApiResponse<any>>('/recording/calibration', formData, {
            headers: {
                'Content-Type': 'multipart/form-data'
            }
        });
        return response.data;
    }
}

export const uploadApi = new UploadApi();