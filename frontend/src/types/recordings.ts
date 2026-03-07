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

export function createRecording(data: Omit<Recording, 'expanded'>): Recording {
    return {
        ...data,
        expanded: false,
    };
}