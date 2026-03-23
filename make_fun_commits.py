import os
import subprocess

jokes = [
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
    "What do cows read at the breakfast table? The moo-spaper.",
    "What sound do you hear when you drop a bomb on a cow? Cow-boom!",
    "Why did the blonde buy a brown cow? To get chocolate milk.",
    "What is a cow's favorite color? Maroon."
]

hook_file_path = "app/hooks/useCowJokes.ts"

os.makedirs("app/hooks", exist_ok=True)

subprocess.run(["git", "checkout", "-b", "feature/fun-easter-egg"])

initial_content = """// Fun Easter Egg Hook: useCowJokes
import { useState } from 'react';

export const useCowJokes = () => {
  const [jokes] = useState<string[]>([
"""

with open(hook_file_path, "w") as f:
    f.write(initial_content)

subprocess.run(["git", "add", hook_file_path])
subprocess.run(["git", "commit", "-m", "feat: create useCowJokes hook with initial setup"])

for i, joke in enumerate(jokes):
    with open(hook_file_path, "a") as f:
        f.write(f'    "{joke}",\n')
    
    subprocess.run(["git", "add", hook_file_path])
    subprocess.run(["git", "commit", "-m", f"feat(jokes): add cow joke #{i+1}"])

with open(hook_file_path, "a") as f:
    f.write("""  ]);

  const getRandomJoke = () => jokes[Math.floor(Math.random() * jokes.length)];

  return { jokes, getRandomJoke };
};
""")

subprocess.run(["git", "add", hook_file_path])
subprocess.run(["git", "commit", "-m", "feat: finalize useCowJokes hook with getRandomJoke function"])

print("Successfully created feature branch and 22 commits!")
