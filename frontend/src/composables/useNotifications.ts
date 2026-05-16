import { ref, onMounted, onUnmounted } from 'vue';
import type { NotificationRead } from '@/api';
import { createNotificationEventSource } from '@/api';
import { emitter } from '@/eventBus';

export function useNotifications() {
    const pendingNotifications = ref<NotificationRead[]>([]);
    let eventSource: EventSource | null = null;

    const connectSSE = () => {
        eventSource = createNotificationEventSource();

        eventSource.addEventListener('notification', (event) => {
            try {
                const notification: NotificationRead = JSON.parse(event.data);
                pendingNotifications.value.push(notification);
                if (notification.type === 'DONE') {
                    emitter.emit('recording:status-changed', {
                        recording_id: notification.recording_id,
                        status: 'DONE',
                    });
                }
            } catch (err) {
                console.error('Failed to parse SSE notification:', err);
            }
        });

        eventSource.onerror = (err) => {
            console.error('SSE connection error:', err);
        };
    };

    onMounted(() => {
        connectSSE();
    });

    onUnmounted(() => {
        if (eventSource) {
            eventSource.close();
            eventSource = null;
        }
    });

    return {
        pendingNotifications,
        removeNotification: (id: string) => {
            const index = pendingNotifications.value.findIndex(n => n.notification_id === id);
            if (index !== -1) pendingNotifications.value.splice(index, 1);
        },
    };
}