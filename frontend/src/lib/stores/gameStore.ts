import { writable } from 'svelte/store';

export const currentMissionId = writable<string | null>(null);
export const bossHealth = writable(100);
export const showReward = writable(false);