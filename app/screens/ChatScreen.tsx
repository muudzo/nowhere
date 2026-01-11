import React, { useEffect, useState, useRef } from 'react';
import { View, Text, FlatList, StyleSheet, TextInput, Button, KeyboardAvoidingView, Platform, Alert } from 'react-native';
import { api } from '../utils/api';

interface Message {
    id: string;
    user_id: string;
    content: string;
    created_at: string;
}

interface Props {
    intentId: string;
    onBack: () => void;
}

export default function ChatScreen({ intentId, onBack }: Props) {
    const [messages, setMessages] = useState<Message[]>([]);
    const [text, setText] = useState('');
    const [loading, setLoading] = useState(true);

    // Polling ref
    const intervalRef = useRef<NodeJS.Timeout | null>(null);

    const fetchMessages = async () => {
        try {
            const res = await api.get(`/intents/${intentId}/messages`);
            setMessages(res.data);
        } catch (e) {
            console.error(e);
            // Don't alert on poll fail to avoid spam
        } finally {
            setLoading(false);
        }
    };

    const startPolling = () => {
        fetchMessages(); // initial
        intervalRef.current = setInterval(fetchMessages, 3000); // Poll every 3s
    };

    useEffect(() => {
        startPolling();
        return () => {
            if (intervalRef.current) clearInterval(intervalRef.current);
        };
    }, [intentId]);

    const handleSend = async () => {
        if (!text.trim()) return;
        try {
            await api.post(`/intents/${intentId}/messages`, {
                user_id: "ignored_by_backend", // Backend uses cookie
                content: text
            });
            setText('');
            fetchMessages(); // Immediate refresh
        } catch (e) {
            console.error(e);
            Alert.alert("Error", "Could not send message");
        }
    };

    return (
        <KeyboardAvoidingView behavior={Platform.OS === "ios" ? "padding" : "height"} style={styles.container}>
            <View style={styles.headerRow}>
                <Button title="<" onPress={onBack} />
                <Text style={styles.header}>Chat</Text>
            </View>

            <FlatList
                data={messages}
                keyExtractor={(item) => item.id}
                inverted={false} // List should show newest at bottom? 
                // Usually chat is bottom-up.
                // But for simple list, simplest is normal order, scroll to end?
                // Or inverted with data reversed.
                // Let's stick to normal order for MVP.
                renderItem={({ item }) => (
                    <View style={styles.bubble}>
                        <Text style={styles.content}>{item.content}</Text>
                    </View>
                )}
            />

            <View style={styles.inputRow}>
                <TextInput
                    style={styles.input}
                    value={text}
                    onChangeText={setText}
                    placeholder="Type a message..."
                />
                <Button title="Send" onPress={handleSend} />
            </View>
        </KeyboardAvoidingView>
    );
}

const styles = StyleSheet.create({
    container: {
        flex: 1,
        paddingTop: 50,
        backgroundColor: '#fff',
    },
    headerRow: {
        flexDirection: 'row',
        alignItems: 'center',
        paddingHorizontal: 10,
        borderBottomWidth: 1,
        borderBottomColor: '#eee',
        paddingBottom: 10
    },
    header: {
        fontSize: 20,
        fontWeight: 'bold',
        marginLeft: 10
    },
    bubble: {
        padding: 10,
        margin: 10,
        backgroundColor: '#e6f7ff',
        borderRadius: 10,
        alignSelf: 'flex-start',
        maxWidth: '80%'
    },
    content: {
        fontSize: 16
    },
    inputRow: {
        flexDirection: 'row',
        padding: 10,
        borderTopWidth: 1,
        borderTopColor: '#eee',
        alignItems: 'center'
    },
    input: {
        flex: 1,
        borderWidth: 1,
        borderColor: '#ddd',
        borderRadius: 20,
        paddingHorizontal: 15,
        paddingVertical: 10,
        marginRight: 10,
        fontSize: 16
    }
});
