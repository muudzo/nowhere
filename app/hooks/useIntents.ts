import { useState, useEffect, useCallback } from 'react';
import { Alert } from 'react-native';
import { api } from '../utils/api';
import { getCurrentLocation, CoarseLocation } from '../utils/location';

export interface Intent {
    id: string;
    title: string;
    emoji: string;
    latitude: number;
    longitude: number;
    join_count: number;
}

export function useIntents() {
    const [nearby, setNearby] = useState<Intent[]>([]);
    const [loading, setLoading] = useState(true);
    const [location, setLocation] = useState<CoarseLocation | null>(null);
    const [message, setMessage] = useState<string | null>(null);

    const fetchData = useCallback(async () => {
        setLoading(true);
        try {
            const loc = await getCurrentLocation();
            setLocation(loc);
            if (loc) {
                const res = await api.get('/intents/nearby', {
                    params: { lat: loc.latitude, lon: loc.longitude }
                });
                setNearby(res.data.intents);
                setMessage(res.data.message || null);
            } else {
                setMessage("We need your location to find the Nowhere.");
            }
        } catch (e) {
            console.error(e);
            Alert.alert("Error", "Could not fetch nearby events");
        } finally {
            setLoading(false);
        }
    }, []);

    const joinIntent = useCallback(async (id: string) => {
        try {
            await api.post(`/intents/${id}/join`);
            Alert.alert("Joined!", "You are in.");
            fetchData();
            return true;
        } catch (e) {
            console.error(e);
            Alert.alert("Error", "Could not join intent");
            return false;
        }
    }, [fetchData]);

    useEffect(() => {
        fetchData();
    }, [fetchData]);

    return {
        nearby,
        loading,
        location,
        message,
        fetchData,
        joinIntent
    };
}
