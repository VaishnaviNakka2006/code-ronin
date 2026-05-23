import { writable } from 'svelte/store';

export interface Achievement {

  id: number;

  name: string;

  description: string;

  unlocked: boolean;

  xpReward: number;
}

export const achievements =
  writable<Achievement[]>([

    {
      id: 1,

      name: 'First Blood',

      description:
        'Complete your first mission',

      unlocked: false,

      xpReward: 10
    },

    {
      id: 2,

      name: 'Streak Master',

      description:
        'Maintain a 7 day streak',

      unlocked: false,

      xpReward: 50
    },

    {
      id: 3,

      name: 'Boss Slayer',

      description:
        'Defeat a boss',

      unlocked: false,

      xpReward: 100
    }

  ]);

export const latestAchievement =
  writable<Achievement | null>(null);

export function unlockAchievement(
  id: number
) {

  achievements.update((list) => {

    return list.map((a) => {

      if (
        a.id === id &&
        !a.unlocked
      ) {

        const unlocked = {
          ...a,
          unlocked: true
        };

        latestAchievement.set(
          unlocked
        );

        return unlocked;
      }

      return a;
    });
  });
}