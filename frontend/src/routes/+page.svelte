<script>
  import NeonButton from '$lib/components/NeonButton.svelte';
</script>

<div class="min-h-screen flex flex-col items-center justify-center text-center px-4 relative overflow-hidden">
  <div class="absolute inset-0 bg-[url('/grid.svg')] opacity-20"></div>
  <h1 class="text-6xl md:text-8xl font-mono glow-text animate-pulse-neon">NEXUS: CODE RONIN</h1>
  <p class="text-xl mt-4 text-gray-300 max-w-xl">Hack the system. Master the code. Ascend the ranks.</p>
  <div class="mt-8 flex gap-4">
    <a
      href="/dashboard"
      class="inline-block px-4 py-2 bg-transparent border border-neon-cyan text-neon-cyan rounded hover:bg-neon-cyan hover:text-black transition-all"
    >
      ENTER THE NEXUS
    </a>
  </div>
</div>