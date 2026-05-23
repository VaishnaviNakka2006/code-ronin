<script lang="ts">
  import { onDestroy, onMount } from 'svelte';
  import anime from 'animejs';
  import { Howl } from 'howler';

  export let missionTitle: string;
  export let missionDifficulty:
    | 'easy'
    | 'medium'
    | 'hard'
    | 'boss' = 'easy';

  export let onComplete: () => void = () => {};

  let visible = true;
  let countdown = 3;
  let interval: any;

  // Sounds temporarily disabled until mp3 files added
  let alarmSound: Howl | null = null;
  let introSound: Howl | null = null;

  onMount(() => {

    // Glitch animation
    anime({
      targets: '.glitch-text',

      translateX: [
        '-2px',
        '2px',
        '-1px',
        '1px',
        '0px'
      ],

      translateY: [
        '1px',
        '-1px',
        '2px',
        '-2px',
        '0px'
      ],

      duration: 200,
      loop: true,
      direction: 'alternate'
    });

    // Countdown
    interval = setInterval(() => {

      countdown--;

      if (countdown === 0) {

        clearInterval(interval);

        setTimeout(() => {
          visible = false;
          onComplete();
        }, 500);
      }

    }, 1000);
  });

  onDestroy(() => {
    clearInterval(interval);
  });

  const difficultyColor = {
    easy: 'text-cyan-400',
    medium: 'text-yellow-400',
    hard: 'text-orange-500',
    boss: 'text-red-500'
  }[missionDifficulty];
</script>

{#if visible}

<div class="fixed inset-0 z-50 bg-black/95 flex items-center justify-center backdrop-blur-md">

  <div class="relative w-full max-w-2xl p-8 border border-cyan-400 rounded-lg shadow-2xl bg-black/80">

    <!-- Scanlines -->
    <div
      class="absolute inset-0 pointer-events-none opacity-20"
      style="
        background:
        repeating-linear-gradient(
          0deg,
          rgba(0,255,255,0.05) 0px,
          rgba(0,255,255,0.05) 2px,
          transparent 2px,
          transparent 4px
        );
      "
    ></div>

    <!-- Header -->
    <div
      class="glitch-text text-5xl font-mono text-center mb-8 text-cyan-400"
      style="text-shadow: 0 0 10px #00ffff;"
    >
      ⚡ MISSION INCOMING ⚡
    </div>

    <!-- Mission Info -->
    <div class="text-center space-y-4">

      <p class="text-2xl font-bold {difficultyColor}">
        {missionTitle}
      </p>

      <p class="text-sm text-gray-400">
        Difficulty:
        <span class={difficultyColor}>
          {missionDifficulty.toUpperCase()}
        </span>
      </p>

      <!-- Countdown -->
      <div class="text-7xl font-mono text-cyan-400 mt-8 animate-pulse">
        {countdown}
      </div>

      <!-- Siren Dots -->
      <div class="flex justify-center gap-2 mt-4">

        {#each [0,1,2] as i}

          <div
            class="w-3 h-3 bg-red-500 rounded-full animate-ping"
            style="animation-delay: {i * 0.2}s"
          ></div>

        {/each}

      </div>
    </div>

    <!-- Terminal Footer -->
    <div class="mt-8 font-mono text-xs text-center text-gray-500 animate-pulse">
      >_ SYSTEM BOOT // CODE RONIN v2.33 //
    </div>

  </div>
</div>

{/if}