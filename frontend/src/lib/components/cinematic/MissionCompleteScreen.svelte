<script lang="ts">
  import { onMount, onDestroy } from 'svelte';
  import anime from 'animejs';
  import { sound } from '$lib/utils/soundManager';
  import { glitchTransition } from '$lib/animations/glitchTransition';

  export let missionTitle: string = 'MISSION';
  export let xpGained: number = 0;
  export let isBoss: boolean = false;
  export let rankUp: { newRank: string; oldRank: string } | null = null;
  export let nextMissionId: number | null = null;
  export let onContinue: () => void = () => {};

  let visible = true;
  let showContinue = false;
  let particleContainer: HTMLDivElement;
  let missionClearedText: HTMLDivElement;

  // Simulate typing effect for "MISSION CLEARED"
  async function typeText() {
    const fullText = isBoss ? '★ BOSS DEFEATED ★' : '✓ MISSION CLEARED ✓';
    missionClearedText.textContent = '';
    for (let i = 0; i < fullText.length; i++) {
      missionClearedText.textContent += fullText[i];
      await new Promise(r => setTimeout(r, 60));
    }
    // Flash glitch
    missionClearedText.classList.add('animate-glitch');
    setTimeout(() => missionClearedText.classList.remove('animate-glitch'), 500);
  }

  onMount(async () => {
    // Play success sound
    sound.play(isBoss ? 'bossDefeat' : 'correct');

    // Slow‑motion effect for boss defeat
    if (isBoss) {
      document.body.style.transition = 'filter 0.5s';
      document.body.style.filter = 'blur(2px)';
      anime({
        targets: document.body,
        filter: ['blur(2px)', 'blur(0px)'],
        duration: 2000,
        easing: 'easeOutQuad'
      });
      // Slow down time globally (CSS hack)
      const style = document.createElement('style');
      style.id = 'slowmo';
      style.textContent = '* { animation-duration: 2s !important; transition-duration: 2s !important; }';
      document.head.appendChild(style);
      setTimeout(() => style.remove(), 2000);
    }

    // Type "MISSION CLEARED"
    await typeText();

    // XP reward animation: floating numbers + particles
    for (let i = 0; i < 30; i++) {
      const particle = document.createElement('div');
      particle.className = 'absolute w-2 h-2 bg-neon-cyan rounded-full pointer-events-none';
      particle.style.left = '50%';
      particle.style.top = '50%';
      particle.style.transform = 'translate(-50%, -50%)';
      particleContainer.appendChild(particle);
      anime({
        targets: particle,
        translateX: anime.random(-200, 200),
        translateY: anime.random(-200, 200),
        scale: [1, 0],
        opacity: [1, 0],
        duration: 800,
        easing: 'easeOutCubic',
        complete: () => particle.remove()
      });
    }

    // Show XP gain text
    const xpText = document.createElement('div');
    xpText.className = 'fixed top-1/2 left-1/2 transform -translate-x-1/2 -translate-y-1/2 text-6xl font-mono text-neon-cyan font-bold z-50 pointer-events-none whitespace-nowrap';
    xpText.textContent = `+${xpGained} XP`;
    document.body.appendChild(xpText);
    anime({
      targets: xpText,
      translateY: [-50, -200],
      opacity: [1, 0],
      duration: 1500,
      easing: 'easeOutCubic',
      complete: () => xpText.remove()
    });

    // Rank‑up popup if needed
    if (rankUp) {
      setTimeout(() => {
        const rankDiv = document.createElement('div');
        rankDiv.className = 'fixed inset-0 flex items-center justify-center z-50 pointer-events-none';
        rankDiv.innerHTML = `
          <div class="bg-black/90 border-4 border-neon-magenta rounded-2xl p-8 text-center animate-glitch">
            <div class="text-5xl mb-2">🏆 RANK UP! 🏆</div>
            <div class="text-2xl text-neon-cyan">${rankUp.oldRank} → ${rankUp.newRank}</div>
          </div>
        `;
        document.body.appendChild(rankDiv);
        sound.play('levelup');
        setTimeout(() => rankDiv.remove(), 2500);
      }, 800);
    }

    // Show continue button after delay
    setTimeout(() => {
      showContinue = true;
    }, 3000);
  });

  function handleContinue() {
    if (!showContinue) return;
    glitchTransition(() => {
      visible = false;
      onContinue();
    });
  }

  onDestroy(() => {
    // Clean up any leftover styles
    document.body.style.filter = '';
    document.getElementById('slowmo')?.remove();
  });
</script>

{#if visible}
<div class="fixed inset-0 z-[100] bg-black/90 backdrop-blur-md flex flex-col items-center justify-center">
  <!-- Particle container -->
  <div bind:this={particleContainer} class="absolute inset-0 overflow-hidden"></div>
  
  <!-- Mission cleared text (typewriter) -->
  <div class="relative z-10 text-center">
    <div bind:this={missionClearedText} class="text-5xl md:text-7xl font-mono font-bold text-neon-cyan glow-text mb-8"></div>
    <div class="text-xl text-white font-mono mb-4">
      {missionTitle}
    </div>
    <!-- Optional extra boss message -->
    {#if isBoss}
      <div class="text-xl text-red-400 font-mono animate-pulse mt-4">SYSTEM SHUTDOWN INITIATED</div>
    {/if}
  </div>

  <!-- Continue button -->
  {#if showContinue}
    <button
      on:click={handleContinue}
      class="mt-12 px-8 py-3 bg-neon-cyan text-black font-bold rounded-lg hover:shadow-[0_0_20px_#00f3ff] transition-all transform hover:scale-105"
    >
      {#if nextMissionId}
        ⚡ CONTINUE TO NEXT MISSION ⚡
      {:else}
        ⚡ RETURN TO HUB ⚡
      {/if}
    </button>
  {/if}
  
  <!-- Glitch overlay effect -->
  <div class="absolute inset-0 pointer-events-none border-4 border-neon-cyan/30 animate-pulse"></div>
</div>
{/if}



