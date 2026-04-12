import { apiJsonClient } from '../config'
import { RecordingRead } from "@/types/recordings";

class MainApi {
    async getRecordings(): Promise<RecordingRead[]> {
        const response = await apiJsonClient.get(`/recording`);
        return response.data;
    }
}

export const mainApi = new MainApi();