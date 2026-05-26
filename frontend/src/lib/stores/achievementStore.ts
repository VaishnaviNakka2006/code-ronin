import { writable } from 'svelte/store';
import type { Achievement } from '$lib/types/achievement';
import { fetchAchievements } from '$lib/api/achievements';

export const achievements = writable<Achievement[]>([]);
export const unlockedCount = writable(0);

export async function loadAchievements() {
  const data = await fetchAchievements();

  achievements.set(data);

  unlockedCount.set(
    data.filter((a) => a.unlocked).length
  );
}

export function addNewlyUnlocked(newAchs: Achievement[]) {
  achievements.update((list) => {
    const updated = list.map((ach) => {
      const found = newAchs.find((n) => n.id === ach.id);

      if (found) {
        return {
          ...ach,
          unlocked: true,
          unlocked_at: new Date().toISOString()
        };
      }

      return ach;
    });

    unlockedCount.set(
      updated.filter((a) => a.unlocked).length
    );

    return updated;
  });
}