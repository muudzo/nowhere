import axios from 'axios';

// Replace with your machine's IP if running on device
export const API_URL = 'http://localhost:8000';

export const api = axios.create({
    baseURL: API_URL,
    withCredentials: true, // For cookies
});
