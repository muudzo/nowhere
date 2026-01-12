import axios from 'axios';
import { getOrCreateIdentity } from './identity';

// Use local network IP for physical device testing, or localhost for simulator
// In Expo, localhost often refers to the device itself.
// Use 10.0.2.2 for Android Emulator loopback.
// Use machine IP for physical device.
// Hardcoding for now based on env or default.
const BASE_URL = 'http://localhost:8000';

export const api = axios.create({
    baseURL: BASE_URL,
    withCredentials: true, // Persist cookies still, for backward compat/fallback
});

api.interceptors.request.use(async (config) => {
    try {
        const identity = await getOrCreateIdentity();
        config.headers['X-Nowhere-Identity'] = identity;
    } catch (e) {
        // Fallback to no header (cookie will work)
    }
    return config;
});
