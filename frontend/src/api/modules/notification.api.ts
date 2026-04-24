import { apiJsonClient } from '../config';

export interface NotificationRead {
    notification_id: string;
    recording_id: string;
    created_date: string;
    sent_date: string | null;
    type: 'DONE';
}

class NotificationApi {
    async getNotifications(): Promise<NotificationRead[]> {
        const response = await apiJsonClient.get('/notification');
        return response.data;
    }
}

export const notificationApi = new NotificationApi();