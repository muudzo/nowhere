import * as SecureStore from 'expo-secure-store';
import { v4 as uuidv4 } from 'uuid';
import { Platform } from 'react-native';

const IDENTITY_KEY = 'nowhere_anon_id';
const ROTATION_INTERVAL_MS = 30 * 24 * 60 * 60 * 1000; // 30 days

interface IdentityData {
    id: string;
    created_at: number;
}

export async function getOrCreateIdentity(): Promise<string> {
    let data: IdentityData | null = null;
    let raw: string | null = null;

    try {
        if (Platform.OS === 'web') {
            raw = localStorage.getItem(IDENTITY_KEY);
        } else {
            raw = await SecureStore.getItemAsync(IDENTITY_KEY);
        }

        if (raw) {
            try {
                // Try parsing as JSON first
                data = JSON.parse(raw);
            } catch (e) {
                // Failed to parse, must be legacy string (Commit 1)
                // Migrate it
                data = { id: raw, created_at: Date.now() };
                await saveIdentity(data);
            }
        }
    } catch (e) {
        console.warn("Failed to read identity:", e);
    }

    // Check rotation
    const now = Date.now();
    if (data && (now - data.created_at > ROTATION_INTERVAL_MS)) {
        console.log("Identity expired, rotating...");
        data = null; // Force regeneration
    }

    if (!data) {
        data = { id: uuidv4(), created_at: now };
        await saveIdentity(data);
    }

    return data.id;
}

async function saveIdentity(data: IdentityData) {
    const str = JSON.stringify(data);
    try {
        if (Platform.OS === 'web') {
            localStorage.setItem(IDENTITY_KEY, str);
        } else {
            await SecureStore.setItemAsync(IDENTITY_KEY, str);
        }
    } catch (e) {
        console.warn("Failed to save identity:", e);
    }
}
