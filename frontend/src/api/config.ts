import axios, { AxiosInstance } from 'axios';

const API_BASE_URL = import.meta.env.VITE_API_URL || '/api';

const createJsonApiClient = (): AxiosInstance => {
    const instance = axios.create({
        baseURL: API_BASE_URL,
        headers: {
            'Content-Type': 'application/json',
            'Accept': 'application/json',
        },
        timeout: 10000,
        withCredentials: true,
    });

    return instance;
}

const createFileApiClient = (): AxiosInstance => {
    const instance = axios.create({
        baseURL: API_BASE_URL,
        withCredentials: true,
        timeout: 30000,
    });
    return instance;
}

export const apiJsonClient = createJsonApiClient();
export const apiFileClient = createFileApiClient();

export interface ApiResponse<T> {
    content: T;
    status_code: string;
}