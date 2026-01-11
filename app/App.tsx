import { StatusBar } from 'expo-status-bar';
import { useState } from 'react';
import HomeScreen from './screens/HomeScreen';
import CreateScreen from './screens/CreateScreen';

type Screen = 'home' | 'create';

export default function App() {
  const [screen, setScreen] = useState<Screen>('home');

  return (
    <>
      {screen === 'home' && <HomeScreen onCreate={() => setScreen('create')} />}
      {screen === 'create' && <CreateScreen onCancel={() => setScreen('home')} onCreated={() => setScreen('home')} />}
      <StatusBar style="auto" />
    </>
  );
}
