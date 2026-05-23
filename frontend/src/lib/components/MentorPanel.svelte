<script lang="ts">
  import { onMount, tick } from 'svelte';
  import { typewriter } from '$lib/animations/typewriter';

  export let message = '';

  let messageEl: HTMLParagraphElement;

  async function animateMessage() {
    await tick();

    if (messageEl && message) {
      typewriter(messageEl, message, 20);
    }
  }

  $: if (message) {
    animateMessage();
  }
</script>

<div class="bg-purple-900/20 border border-fuchsia-500 rounded-lg p-5">
  <div class="text-cyan-300 font-bold mb-3">
    ⚡ AI MENTOR [VEX]
  </div>

  <p
    bind:this={messageEl}
    class="text-white min-h-[60px] leading-relaxed"
  ></p>
</div>