import { StatusBar } from 'expo-status-bar';
import { useState } from 'react';
import HomeScreen from './screens/HomeScreen';
import CreateScreen from './screens/CreateScreen';
import ChatScreen from './screens/ChatScreen';

type Screen = 'home' | 'create' | 'chat';

export default function App() {
  const [screen, setScreen] = useState<Screen>('home');
  const [activeIntentId, setActiveIntentId] = useState<string | null>(null);

  const openChat = (id: string) => {
    setActiveIntentId(id);
    setScreen('chat');
  };

  return (
    <>
      {screen === 'home' && (
        <HomeScreen
          onCreate={() => setScreen('create')}
          onChat={openChat}
        />
      )}
      {screen === 'create' && <CreateScreen onCancel={() => setScreen('home')} onCreated={() => setScreen('home')} />}
      {screen === 'chat' && activeIntentId && (
        <ChatScreen
          intentId={activeIntentId}
          onBack={() => setScreen('home')}
        />
      )}
      <StatusBar style="auto" />
    </>
  );
}
