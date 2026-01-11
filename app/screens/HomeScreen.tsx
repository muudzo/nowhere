import React, { useEffect, useState } from 'react';
import { View, Text, FlatList, StyleSheet, ActivityIndicator, Alert } from 'react-native';
import { getCurrentLocation, CoarseLocation } from '../utils/location';
import { api } from '../utils/api';

interface Intent {
    id: string;
    title: string;
    emoji: string;
    latitude: float;
    longitude: float;
    join_count: number;
}

export default function HomeScreen() {
    const [nearby, setNearby] = useState<Intent[]>([]);
    const [loading, setLoading] = useState(true);
    const [location, setLocation] = useState<CoarseLocation | null>(null);
    const [message, setMessage] = useState<string | null>(null);

    const fetchData = async () => {
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
    };

    useEffect(() => {
        fetchData();
    }, []);

    if (loading && !nearby.length) {
        return (
            <View style={styles.center}>
                <ActivityIndicator size="large" />
            </View>
        )
    }

    return (
        <View style={styles.container}>
            <Text style={styles.header}>Nowhere</Text>
            {message && <Text style={styles.message}>{message}</Text>}

            <FlatList
                data={nearby}
                keyExtractor={(item) => item.id}
                refreshing={loading}
                onRefresh={fetchData}
                renderItem={({ item }) => (
                    <View style={styles.card}>
                        <Text style={styles.emoji}>{item.emoji}</Text>
                        <View style={styles.info}>
                            <Text style={styles.title}>{item.title}</Text>
                            <Text style={styles.meta}>{item.join_count} joined</Text>
                        </View>
                    </View>
                )}
            />
        </View>
    );
}

const styles = StyleSheet.create({
    container: {
        flex: 1,
        paddingTop: 60,
        backgroundColor: '#fff',
        paddingHorizontal: 20
    },
    center: {
        flex: 1,
        justifyContent: 'center',
        alignItems: 'center'
    },
    header: {
        fontSize: 32,
        fontWeight: 'bold',
        marginBottom: 20
    },
    message: {
        fontSize: 16,
        color: '#666',
        marginBottom: 20
    },
    card: {
        flexDirection: 'row',
        padding: 15,
        marginBottom: 10,
        backgroundColor: '#f8f8f8',
        borderRadius: 12,
        alignItems: 'center'
    },
    emoji: {
        fontSize: 30,
        marginRight: 15
    },
    info: {
        flex: 1
    },
    title: {
        fontSize: 18,
        fontWeight: '600'
    },
    meta: {
        fontSize: 14,
        color: '#888',
        marginTop: 4
    }
});
