import * as SecureStore from 'expo-secure-store';
import { v4 as uuidv4 } from 'uuid';
import { Platform } from 'react-native';

const IDENTITY_KEY = 'nowhere_anon_id';

export async function getOrCreateIdentity(): Promise<string> {
    let id: string | null = null;

    try {
        if (Platform.OS === 'web') {
            id = localStorage.getItem(IDENTITY_KEY);
        } else {
            id = await SecureStore.getItemAsync(IDENTITY_KEY);
        }
    } catch (e) {
        console.warn("Failed to read identity:", e);
    }

    if (!id) {
        id = uuidv4();
        try {
            if (Platform.OS === 'web') {
                localStorage.setItem(IDENTITY_KEY, id);
            } else {
                await SecureStore.setItemAsync(IDENTITY_KEY, id);
            }
        } catch (e) {
            console.warn("Failed to save identity:", e);
        }
    }

    return id;
}
