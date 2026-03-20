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
    "Why do cows have hooves instead of feet? Because they lactose.",
    "What do you call a magical cow? Moo-dini.",
    "What do you call a cow that won't give milk? An udder failure.",
    "What do you call a cow playing a guitar? A moo-sician.",
    "What did the cow say to the calf? It's pasture bedtime.",
    "Why did the cow jump over the moon? Because the farmer had cold hands.",
    "Where do Russian cows come from? Mos-cow.",
    "What do you call a cow that eats grass? A lawn moo-er.",
