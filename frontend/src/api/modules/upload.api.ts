import { apiFileClient } from '../config'
import type { ApiResponse } from '../config'
import {T} from "vue-router/dist/index-DFCq6eJK";

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
}

export const uploadApi = new UploadApi();