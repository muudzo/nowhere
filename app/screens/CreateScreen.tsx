import React, { useState } from 'react';
import { View, Text, TextInput, Button, StyleSheet, Alert, ActivityIndicator } from 'react-native';
import { getCurrentLocation } from '../utils/location';
import { api } from '../utils/api';

interface Props {
    onCancel: () => void;
    onCreated: () => void;
}

export default function CreateScreen({ onCancel, onCreated }: Props) {
    const [title, setTitle] = useState('');
    const [emoji, setEmoji] = useState('📍');
    const [creating, setCreating] = useState(false);

    const handleCreate = async () => {
        if (!title.trim()) {
            Alert.alert("Needed", "Please add a title");
            return;
        }

        setCreating(true);
        console.log("Starting creation flow...");
        try {
            console.log("Getting location...");
            const loc = await getCurrentLocation();
            console.log("Location received:", loc);
            if (!loc) {
                Alert.alert("Permission", "Location needed to create intent");
                setCreating(false);
                return;
            }

            console.log("Sending API request to:", '/intents/');
            await api.post('/intents/', {
                title: title,
                emoji: emoji,
                latitude: loc.latitude,
                longitude: loc.longitude
            });
            console.log("API request successful");

            onCreated();
        } catch (e) {
            console.error("Creation failed:", e);
            Alert.alert("Error", "Failed to create intent");
        } finally {
            console.log("Creation flow finished (finally block)");
            setCreating(false);
        }
    };

    if (creating) {
        return (
            <View style={styles.center}>
                <ActivityIndicator size="large" />
                <Text>Creating...</Text>
            </View>
        )
    }

    return (
        <View style={styles.container}>
            <Text style={styles.header}>New Intent</Text>

            <Text style={styles.label}>What's happening?</Text>
            <TextInput
                style={styles.input}
                placeholder="Coffee run? Frisbee?"
                value={title}
                onChangeText={setTitle}
                maxLength={50}
            />

            <Text style={styles.label}>Emoji</Text>
            <TextInput
                style={styles.input}
                placeholder="📍"
                value={emoji}
                onChangeText={setEmoji}
                maxLength={2}
            />

            <View style={styles.buttons}>
                <Button title="Cancel" onPress={onCancel} color="#999" />
                <Button title="Create" onPress={handleCreate} />
            </View>
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
        fontSize: 28,
        fontWeight: 'bold',
        marginBottom: 30
    },
    label: {
        fontSize: 16,
        marginBottom: 8,
        fontWeight: '600'
    },
    input: {
        borderWidth: 1,
        borderColor: '#ddd',
        padding: 12,
        borderRadius: 8,
        fontSize: 18,
        marginBottom: 20
    },
    buttons: {
        flexDirection: 'row',
        justifyContent: 'space-between',
        marginTop: 20
    }
});
