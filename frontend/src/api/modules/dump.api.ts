import { apiFileClient } from '../config'

class DumpApi {
    async upload(file: File): Promise<any> {
        const formData = new FormData();
        formData.append('file', file);

        const response = await apiFileClient.post('/dump', formData, {
            headers: {
                'Content-Type': 'multipart/form-data'
            }
        });
        return response.data;
    }
}

export const dumpApi = new DumpApi();