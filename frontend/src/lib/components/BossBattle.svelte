<script lang="ts">
  import { onMount, onDestroy } from 'svelte';

  import { sound }
    from '$lib/utils/soundManager';

  import {
    bossHealth
  } from '$lib/stores/gameStore';

  import {
    corruptScreen
  }
  from '$lib/animations/corruptScreen';

  export let bossName =
    'Corrupted Core';

  export let maxHealth = 100;

  let currentHealth =
    maxHealth;

  let bossAttackMessage = '';

  let attackInterval: any;

  const attacks = [
    '💀 SYNTAX VIRUS: Your code is scrambled!',
    '🌀 INFINITE LOOP: Time slows down...',
    '⚡ MEMORY LEAK: Resources draining...',
    '🔥 STACK OVERFLOW: Critical damage incoming!'
  ];

  onMount(() => {

    attackInterval = setInterval(() => {

      if (currentHealth <= 0)
        return;

      bossAttackMessage =
        attacks[
          Math.floor(
            Math.random() *
            attacks.length
          )
        ];

      sound.play('bossHit');

      setTimeout(() => {
        bossAttackMessage = '';
      }, 2500);

    }, 8000);
  });

  onDestroy(() => {
    clearInterval(attackInterval);
  });

  export function damage(
    amount: number
  ) {

    currentHealth =
      Math.max(
        0,
        currentHealth - amount
      );

    bossHealth.set(currentHealth);

    if (currentHealth <= 0) {

      clearInterval(
        attackInterval
      );
      corruptScreen(1);
      sound.play(
        'bossDefeat'
      );

    } else {
    
      corruptScreen(0.7);
      sound.play(
        'bossHit'
      );
    }
  }

  $: healthPercent =
    (currentHealth / maxHealth) * 100;
</script>

<div
  class="relative bg-black/70 border border-red-500 rounded-lg p-5 mb-6 overflow-hidden"
>

  <!-- Glowing Overlay -->
  <div
    class="absolute inset-0 bg-red-500/5 animate-pulse pointer-events-none"
  ></div>

  <!-- Header -->
  <div class="flex justify-between items-center">

    <h2
      class="text-2xl font-mono text-red-500 animate-pulse"
    >
      🐉 {bossName}
    </h2>

    <!-- Health Bar -->
    <div
      class="w-64 bg-gray-900 rounded-full h-4 overflow-hidden border border-red-500"
    >

      <div
        class="bg-gradient-to-r from-red-700 to-red-400 h-full transition-all duration-500"
        style="width: {healthPercent}%"
      ></div>

    </div>

  </div>

  <!-- Boss Attack Message -->
  {#if bossAttackMessage}

    <div
      class="mt-3 text-red-400 font-mono text-sm animate-pulse"
    >
      {bossAttackMessage}
    </div>

  {/if}

</div>