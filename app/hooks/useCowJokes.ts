// Fun Easter Egg Hook: useCowJokes
import { useState } from 'react';

export const useCowJokes = () => {
  const [jokes] = useState<string[]>([
    "What do you call a cow with no legs? Ground beef.",
    "What do you call a cow with a twitch? Beef jerky.",
