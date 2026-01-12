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

import { getAccessToken } from './identity';

// ... (existing imports/setup)

api.interceptors.request.use(async (config) => {
    try {
        const token = await getAccessToken();
        if (token) {
            config.headers['Authorization'] = `Bearer ${token}`;
        }

        // Also send legacy header just in case or for smooth migration?
        // Let's remove it to force JWT usage if we trust handshake.
        // Or keep it as "X-Nowhere-Identity" if getAccessToken fails? 
        // Logic: getAccessToken handles handshake. If it fails, token is null.

    } catch (e) {
        // Fallback
    }
    return config;
});
