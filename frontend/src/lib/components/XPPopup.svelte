<script lang="ts">
  import { onDestroy } from 'svelte';

  export let xp: number;

  export let onComplete: () => void;

  const timeout = setTimeout(() => {
    onComplete();
  }, 1000);

  onDestroy(() => {
    clearTimeout(timeout);
  });
</script>

<div
  class="fixed bottom-1/4 left-1/2 -translate-x-1/2 animate-float-up text-cyan-400 font-mono text-2xl font-bold z-50 pointer-events-none"
>
  +{xp} XP
</div>

<style>
  @keyframes floatUp {
    0% {
      opacity: 1;
      transform: translate(-50%, 0);
    }

    100% {
      opacity: 0;
      transform: translate(-50%, -80px);
    }
  }

  .animate-float-up {
    animation: floatUp 1s ease-out forwards;
  }
</style>