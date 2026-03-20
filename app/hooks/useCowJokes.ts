// Fun Easter Egg Hook: useCowJokes
import { useState } from 'react';

export const useCowJokes = () => {
  const [jokes] = useState<string[]>([
    "What do you call a cow with no legs? Ground beef.",
    "What do you call a cow with a twitch? Beef jerky.",
    "What do you get from a pampered cow? Spoiled milk.",
    "Where do cows go for entertainment? The moo-vies.",
    "What do you call a cow in an earthquake? A milkshake.",
    "Why did the cow cross the road? To get to the udder side.",
    "What do you call a sleeping cow? A bull-dozer.",
    "How do farmers count their cows? With a cow-culator.",
