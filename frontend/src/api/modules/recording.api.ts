import { apiFileClient, apiJsonClient } from '../config';
import type { SuspiciousItem } from '@/types/suspicious';

class RecordingApi {
    async getWebcamVideo(recordingId: string): Promise<Blob> {
        const response = await apiFileClient.get(`/recording/webcam/${recordingId}`, {
            responseType: 'blob',
        });
        return response.data;
    }

    async getScreenVideo(recordingId: string): Promise<Blob> {
        const response = await apiFileClient.get(`/recording/screen/${recordingId}`, {
            responseType: 'blob',
        });
        return response.data;
    }

    async getSuspicious(recordingId: string): Promise<SuspiciousItem[]> {
        const response = await apiJsonClient.get(`/suspicious/${recordingId}`);
        return response.data;
    }
}

export const recordingApi = new RecordingApi();