<script lang="ts">
  import { onMount } from 'svelte';

  export let oldRank = 'Scavenger';

  export let newRank = 'Runner';

  export let visible = false;

  let showUpgrade = false;

  onMount(() => {

    if (visible) {

      setTimeout(() => {
        showUpgrade = true;
      }, 1200);
    }
  });
</script>

{#if visible}

<div
  class="fixed inset-0 z-[99999]
  bg-black/95 backdrop-blur-md
  flex items-center justify-center"
>

  <div
    class="relative w-full max-w-3xl
    border border-cyan-400
    rounded-2xl
    bg-black/80
    p-10 overflow-hidden"
  >

    <!-- Glow -->
    <div
      class="absolute inset-0 bg-cyan-400/5 animate-pulse"
    ></div>

    <!-- Header -->
    <div
      class="text-center text-cyan-400
      text-5xl font-mono font-bold
      animate-pulse"
    >
      ⚡ LEVEL UP ⚡
    </div>

    <!-- Rank Transition -->
    <div
      class="flex items-center justify-center
      gap-10 mt-12"
    >

      <!-- Old Rank -->
      <div
        class="text-center opacity-60"
      >

        <div class="text-gray-400 text-sm">
          PREVIOUS RANK
        </div>

        <div
          class="mt-2 text-3xl font-bold text-white"
        >
          {oldRank}
        </div>

      </div>

      <!-- Arrow -->
      <div
        class="text-6xl text-cyan-400 animate-bounce"
      >
        →
      </div>

      <!-- New Rank -->
      <div
        class="text-center"
      >

        <div class="text-cyan-300 text-sm">
          NEW RANK
        </div>

        <div
          class="mt-2 text-5xl font-bold
          text-yellow-400
          animate-pulse"
        >
          {newRank}
        </div>

      </div>

    </div>

    <!-- Footer -->
    <div
      class="mt-12 text-center text-gray-400 font-mono"
    >
      >_ STATUS UPDATED // RONIN PROTOCOL ASCENDED
    </div>

  </div>

</div>

{/if}