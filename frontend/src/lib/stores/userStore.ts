import { writable } from 'svelte/store';

export interface User {
  id: string;
  username: string;
  xp: number;
  rank: 'Scavenger' | 'Runner' | 'Hacker';
  streak: number;
}

export const user = writable<User>({
  id: '',
  username: 'Ronin',
  xp: 0,
  rank: 'Scavenger',
  streak: 0
});

export function updateXP(newXP: number) {
  user.update((u) => {
    u.xp = newXP;

    // RANK LOGIC
    if (u.xp >= 100) {
      u.rank = 'Hacker';
    } else if (u.xp >= 30) {
      u.rank = 'Runner';
    } else {
      u.rank = 'Scavenger';
    }

    return {
      ...u
    };
  });
}

export function resetUser() {
  user.set({
    id: '',
    username: 'Ronin',
    xp: 0,
    rank: 'Scavenger',
    streak: 0
  });
}