import { writable } from 'svelte/store';

export const currentMission = writable<number | null>(null);

export const showCinematic = writable(false);

declare global {
  interface Window {
    __cinematicComplete?: () => void;
  }
}

export async function startMission(
  missionId: number
) {

  currentMission.set(missionId);

  showCinematic.set(true);

  return new Promise((resolve) => {

    const handleComplete = () => {

      showCinematic.set(false);

      resolve(true);
    };

    window.__cinematicComplete =
      handleComplete;
  });
}