<script lang="ts">
  import { tick } from 'svelte';
  import { typewriter } from '$lib/animations/typewriter';

  export let message = '';

  let mentorText: HTMLParagraphElement;

  let avatarState: 'idle' | 'talking' = 'idle';

  async function animateMessage() {

    await tick();

    if (mentorText && message) {

      avatarState = 'talking';

      await typewriter(
        mentorText,
        message,
        20
      );

      setTimeout(() => {
        avatarState = 'idle';
      }, 1000);
    }
  }

  $: if (message) {
    animateMessage();
  }
</script>

<div
  class="relative bg-black/70 border border-fuchsia-500 rounded-lg p-4 backdrop-blur-md shadow-lg"
>

  <div class="flex gap-4">

    <!-- Avatar -->
    <div
      class="relative w-16 h-16 bg-black rounded-full border border-cyan-400 overflow-hidden flex items-center justify-center"
    >

      <div
        class="absolute inset-0 bg-gradient-to-b from-cyan-400/20 to-transparent"
      ></div>

      <div class="text-3xl z-10 animate-pulse">

        {#if avatarState === 'talking'}
          ⚡
        {:else}
          👾
        {/if}

      </div>

      <div
        class="absolute bottom-0 left-0 w-full h-1 bg-cyan-400 animate-pulse"
      ></div>

    </div>

    <!-- Text -->
    <div class="flex-1">

      <p class="text-cyan-300 text-sm font-mono">
        AI MENTOR [VEX]
      </p>

      <p
        bind:this={mentorText}
        class="text-white mt-2 font-mono text-sm leading-relaxed min-h-[60px]"
      ></p>

    </div>

  </div>

</div>