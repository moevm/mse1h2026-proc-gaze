import { ref, onUnmounted } from 'vue';
import { notificationApi, NotificationRead } from '@/api/modules/notification.api';
import { emitter } from '@/eventBus';

export function useNotifications() {
    const pendingNotifications = ref<NotificationRead[]>([]);
    let pollingTimer: ReturnType<typeof setInterval> | null = null;

    const fetchNotifications = async () => {
        try {
            const data = await notificationApi.getNotifications();
            if (data.length > 0) {
                pendingNotifications.value.push(...data);
                data.forEach((notif) => {
                    if (notif.type === 'DONE') {
                        emitter.emit('recording:status-changed', {
                            recording_id: notif.recording_id,
                            status: 'DONE',
                        });
                    }
                });
            }
        } catch (error) {
            console.error('Notification polling error:', error);
        }
    };

    const startPolling = (intervalMs = 10000) => {
        fetchNotifications();
        pollingTimer = setInterval(fetchNotifications, intervalMs);
    };

    const stopPolling = () => {
        if (pollingTimer) {
            clearInterval(pollingTimer);
            pollingTimer = null;
        }
    };

    const removeNotification = (id: string) => {
        const index = pendingNotifications.value.findIndex(
            (n) => n.notification_id === id
        );
        if (index !== -1) {
            pendingNotifications.value.splice(index, 1);
        }
    };

    onUnmounted(() => {
        stopPolling();
    });

    return {
        pendingNotifications,
        startPolling,
        stopPolling,
        removeNotification,
    };
}