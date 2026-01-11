import React, { useEffect, useState } from 'react';
import { View, Text, FlatList, StyleSheet, ActivityIndicator, Alert, Button } from 'react-native';
import { getCurrentLocation, CoarseLocation } from '../utils/location';
import { api } from '../utils/api';

interface Intent {
    id: string;
    title: string;
    emoji: string;
    latitude: number;
    longitude: number;
    join_count: number;
}

interface Props {
    onCreate: () => void;
}

export default function HomeScreen({ onCreate }: Props) {
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

    const handleJoin = async (id: string) => {
        try {
            await api.post(`/intents/${id}/join`);
            // Refresh logic - optimistic or fetch? Fetch for MVP is safer to get updated count.
            fetchData();
            Alert.alert("Joined!", "You are in.");
        } catch (e) {
            console.error(e);
            Alert.alert("Error", "Could not join intent");
        }
    };

    if (loading && !nearby.length) {
        return (
            <View style={styles.center}>
                <ActivityIndicator size="large" />
            </View>
        )
    }

    return (
        <View style={styles.container}>
            <View style={styles.headerRow}>
                <Text style={styles.header}>Nowhere</Text>
                <Button title="+" onPress={onCreate} />
            </View>
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
                        <View style={styles.actions}>
                            <Button title="Join" onPress={() => handleJoin(item.id)} />
                            {/* Show Enter if joined logic? For MVP, always show Enter, let it fail 403 or succeed? 
                                 Or just a generic "Open" button?
                                 "Temporary Chat Screen".
                                 I'll just add the button.
                              */}
                            <Button title="Chat" color="#666" onPress={() => onChat(item.id)} />
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
    },
    headerRow: {
        flexDirection: 'row',
        justifyContent: 'space-between',
        alignItems: 'center',
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
    actions: {
        flexDirection: 'column', // Stack buttons? Or row? Row better.
        flexDirection: 'row',
        gap: 8,
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
