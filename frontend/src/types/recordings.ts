export interface RecordingRead {
    recording_id: string;
    student_id: string;
    status: 'PENDING' | 'PROCESSING' | 'DONE';
    count_suspicions: number | null;
    path_webcam: string;
    path_screen: string;
    created_date: string;
    processed_date: string | null;
    suspicion_level: number;
}

export interface Recording {
    recording_id: string;
    student_id: string;
    status: 'PENDING' | 'PROCESSING' | 'DONE';
    count_suspicions: number | null;
    camera_video_name: string;
    screen_video_name: string;
    created_date: string;
    processed_date: string | null;
    expanded?: boolean;
}

export function convertRecordingReadToRecording(data: RecordingRead): Recording {
    return {
        recording_id: data.recording_id,
        student_id: data.student_id,
        status: data.status,
        count_suspicions: data.count_suspicions,
        camera_video_name: data.path_webcam,
        screen_video_name: data.path_screen,
        created_date: data.created_date,
        processed_date: data.processed_date,
        expanded: false,
    };
}