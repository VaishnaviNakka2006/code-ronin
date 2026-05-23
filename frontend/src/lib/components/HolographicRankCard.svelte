<script lang="ts">
  import { onMount } from 'svelte';
  import anime from 'animejs/lib/anime.es.js';
  

  export let username: string = 'Ronin';
  export let rank: 'Scavenger' | 'Runner' | 'Hacker' = 'Scavenger';
  export let xp: number = 0;
  export let streakDays: number = 0;

  let cardRef: HTMLDivElement;
  let glowRef: HTMLDivElement;
  let rotation = { x: 0, y: 0 };
  let rankColor = '';

  const rankColors = {
    Scavenger: 'from-gray-500 to-gray-700 border-gray-400',
    Runner: 'from-neon-cyan to-blue-500 border-neon-cyan',
    Hacker: 'from-neon-magenta to-purple-600 border-neon-magenta'
  };

  const rankNext = {
    Scavenger: { name: 'Runner', xpNeeded: 30 - xp, xpTotal: 30 },
    Runner: { name: 'Hacker', xpNeeded: 100 - xp, xpTotal: 100 },
    Hacker: { name: 'MAX', xpNeeded: 0, xpTotal: 100 }
  };

  $: rankColor = rankColors[rank];
  $: nextRank = rankNext[rank];
  $: progressToNext = Math.min(100, Math.floor((xp / nextRank.xpTotal) * 100));

  // Mouse move handler for holographic tilt
  function handleMouseMove(e: MouseEvent) {
    if (!cardRef) return;
    const rect = cardRef.getBoundingClientRect();
    const centerX = rect.left + rect.width / 2;
    const centerY = rect.top + rect.height / 2;
    const deltaX = (e.clientX - centerX) / (rect.width / 2);
    const deltaY = (e.clientY - centerY) / (rect.height / 2);
    rotation.y = deltaX * 10; // max ±10deg
    rotation.x = -deltaY * 10;
    anime({
      targets: cardRef,
      rotateX: rotation.x,
      rotateY: rotation.y,
      duration: 200,
      easing: 'easeOutQuad'
    });
    // Move glow
    if (glowRef) {
      const glowX = (e.clientX - rect.left) / rect.width;
      const glowY = (e.clientY - rect.top) / rect.height;
      glowRef.style.background = `radial-gradient(circle at ${glowX * 100}% ${glowY * 100}%, rgba(0,243,255,0.4), transparent 70%)`;
    }
  }

  function handleMouseLeave() {
    anime({
      targets: cardRef,
      rotateX: 0,
      rotateY: 0,
      duration: 400,
      easing: 'easeOutQuad'
    });
    if (glowRef) {
      glowRef.style.background = 'radial-gradient(circle at 50% 50%, rgba(0,243,255,0.2), transparent 70%)';
    }
  }

  onMount(() => {
    // Initial glow
    if (glowRef) {
      glowRef.style.background = 'radial-gradient(circle at 50% 50%, rgba(0,243,255,0.2), transparent 70%)';
    }
    // Subtle floating animation
    anime({
      targets: cardRef,
      translateY: [-5, 5],
      duration: 3000,
      direction: 'alternate',
      loop: true,
      easing: 'easeInOutSine'
    });
  });
</script>

<div class="relative w-full max-w-md mx-auto perspective-1000">
  <div
    bind:this={cardRef}
    class="relative bg-gradient-to-br {rankColor} bg-opacity-20 backdrop-blur-md rounded-2xl border-2 shadow-2xl p-6 transition-all duration-200 cursor-pointer"
    on:mousemove={handleMouseMove}
    on:mouseleave={handleMouseLeave}
    style="transform-style: preserve-3d; background-color: rgba(0,0,0,0.6);"
  >
    <!-- Holographic glow overlay -->
    <div bind:this={glowRef} class="absolute inset-0 rounded-2xl pointer-events-none transition-all duration-100"></div>
    
    <!-- Scanning line animation -->
    <div class="absolute inset-0 overflow-hidden rounded-2xl pointer-events-none">
      <div class="w-full h-1 bg-neon-cyan/50 animate-scan absolute top-0 left-0"></div>
    </div>
    
    <!-- Rank icon & title -->
    <div class="flex items-center gap-4 mb-4 relative" style="transform: translateZ(20px)">
      <div class="text-5xl">
        {#if rank === 'Scavenger'}🔧
        {:else if rank === 'Runner'}⚡
        {:else}💀
        {/if}
      </div>
      <div>
        <p class="text-xs text-gray-400 font-mono">CALLSIGN</p>
        <p class="text-2xl font-bold text-white tracking-wider">{username}</p>
      </div>
    </div>
    
    <!-- Rank badge with glitch -->
    <div class="mb-4 relative" style="transform: translateZ(15px)">
      <div class="inline-block px-4 py-2 bg-black/60 border-2 rounded-lg" class:border-neon-cyan={rank === 'Runner'} class:border-neon-magenta={rank === 'Hacker'} class:border-gray-500={rank === 'Scavenger'}>
        <span class="text-xl font-mono font-bold" class:text-neon-cyan={rank === 'Runner'} class:text-neon-magenta={rank === 'Hacker'} class:text-gray-400={rank === 'Scavenger'}>
          {rank.toUpperCase()}
        </span>
      </div>
    </div>
    
    <!-- XP progress to next rank -->
    <div class="relative" style="transform: translateZ(10px)">
      <div class="flex justify-between text-sm font-mono mb-1">
        <span class="text-gray-400">→ NEXT: {nextRank.name}</span>
        <span class="text-neon-cyan">{nextRank.xpNeeded > 0 ? `${nextRank.xpNeeded} XP needed` : 'MAX RANK'}</span>
      </div>
      <div class="h-2 bg-gray-800 rounded-full overflow-hidden">
        <div class="h-full bg-gradient-to-r from-neon-cyan to-neon-magenta transition-all duration-500" style="width: {progressToNext}%"></div>
      </div>
    </div>
    
    <!-- Stats grid -->
    <div class="grid grid-cols-2 gap-4 mt-6 relative" style="transform: translateZ(25px)">
      <div class="text-center border-r border-neon-cyan/30">
        <p class="text-xs text-gray-400">TOTAL XP</p>
        <p class="text-2xl font-mono text-neon-cyan">{xp}</p>
      </div>
      <div class="text-center">
        <p class="text-xs text-gray-400">STREAK</p>
        <p class="text-2xl font-mono text-neon-magenta">🔥 {streakDays}</p>
      </div>
    </div>
    
    <!-- Holographic corner decorations -->
    <div class="absolute top-0 left-0 w-8 h-8 border-t-2 border-l-2 border-neon-cyan/70 rounded-tl-lg"></div>
    <div class="absolute top-0 right-0 w-8 h-8 border-t-2 border-r-2 border-neon-cyan/70 rounded-tr-lg"></div>
    <div class="absolute bottom-0 left-0 w-8 h-8 border-b-2 border-l-2 border-neon-cyan/70 rounded-bl-lg"></div>
    <div class="absolute bottom-0 right-0 w-8 h-8 border-b-2 border-r-2 border-neon-cyan/70 rounded-br-lg"></div>
  </div>
</div>

<!-- Add perspective utility class -->
<style>
  .perspective-1000 {
    perspective: 1000px;
  }
  @keyframes scan {
    0% { transform: translateY(-100%); }
    100% { transform: translateY(1000%); }
  }
  .animate-scan {
    animation: scan 4s linear infinite;
  }
</style>