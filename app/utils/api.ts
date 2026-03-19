import axios from 'axios';
import { getOrCreateIdentity, getAccessToken } from './identity';
import { API_URL } from './config';

export const api = axios.create({
    baseURL: API_URL,
    withCredentials: true,
    timeout: 10000,
});

api.interceptors.request.use(async (config) => {
    try {
        const token = await getAccessToken();
        if (token) {
            config.headers['Authorization'] = `Bearer ${token}`;
        }
    } catch (e) {
        // Fallback — request proceeds without auth
    }
    return config;
});
