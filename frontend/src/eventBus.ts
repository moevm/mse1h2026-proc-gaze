import mitt from 'mitt';

type Events = {
    'recording:status-changed': { recording_id: string; status: string };
};

export const emitter = mitt<Events>();