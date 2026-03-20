// Fun Easter Egg Hook: useCowJokes
import { useState } from 'react';

export const useCowJokes = () => {
  const [jokes] = useState<string[]>([
