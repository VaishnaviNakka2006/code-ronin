<script lang="ts">
  import { onMount } from 'svelte';
  import anime from 'animejs/lib/anime.es.js';
  import { sound } from '$lib/utils/soundManager';

  export let currentXP: number = 0;
  export let maxXP: number = 100;
  export let onLevelUp: () => void = () => {};

  let displayXP = currentXP;
  let percent = (currentXP / maxXP) * 100;
  let barRef: HTMLDivElement;
  let glitchActive = false;

  $: percent = (displayXP / maxXP) * 100;

  // Animate XP gain
  export function addXP(amount: number) {
    const newXP = Math.min(currentXP + amount, maxXP);
    const oldPercent = (currentXP / maxXP) * 100;
    const newPercent = (newXP / maxXP) * 100;

    // Trigger sound
    sound.play('correct');

    // Animate the bar
    anime({
      targets: barRef,
      width: [`${oldPercent}%`, `${newPercent}%`],
      duration: 600,
      easing: 'easeOutElastic(1, .5)',
      update: () => {
        displayXP = Math.floor((parseFloat(barRef.style.width) / 100) * maxXP);
      },
      complete: () => {
        currentXP = newXP;
        displayXP = currentXP;
        if (currentXP >= maxXP) {
          // Level up!
          onLevelUp();
          // Reset XP with overflow
          const overflow = currentXP - maxXP;
          currentXP = overflow;
          displayXP = overflow;
          percent = (currentXP / maxXP) * 100;
          barRef.style.width = `${percent}%`;
        }
      }
    });

    // Particle burst
    const particles = document.createElement('div');
    particles.className = 'fixed inset-0 pointer-events-none z-50';
    for (let i = 0; i < 20; i++) {
      const particle = document.createElement('div');
      particle.className = 'absolute w-1 h-1 bg-neon-cyan rounded-full';
      particle.style.left = `${Math.random() * 100}%`;
      particle.style.top = `${Math.random() * 100}%`;
      particle.style.opacity = '1';
      particles.appendChild(particle);
      anime({
        targets: particle,
        translateX: anime.random(-100, 100),
        translateY: anime.random(-100, 100),
        opacity: 0,
        duration: 800,
        easing: 'easeOutCubic',
        complete: () => particle.remove()
      });
    }
    document.body.appendChild(particles);
    setTimeout(() => particles.remove(), 1000);
  }
</script>

<div class="relative w-full">
  <!-- Glow effect background -->
  <div class="absolute inset-0 bg-neon-cyan/20 blur-xl rounded-full"></div>
  
  <!-- XP Bar container -->
  <div class="relative h-6 bg-gray-800 rounded-full overflow-hidden border border-neon-cyan/50 shadow-[0_0_10px_rgba(0,243,255,0.3)]">
    <div 
      bind:this={barRef}
      class="h-full bg-gradient-to-r from-neon-cyan to-neon-magenta transition-all duration-300 relative"
      style="width: 0%"
    >
      <!-- Glossy shine -->
      <div class="absolute inset-0 bg-gradient-to-b from-white/20 to-transparent"></div>
      <!-- Scanning line -->
      <div class="absolute top-0 left-0 w-full h-full bg-[repeating-linear-gradient(90deg,transparent,transparent_10px,rgba(255,255,255,0.1)_10px,rgba(255,255,255,0.1)_20px)]"></div>
    </div>
  </div>
  
  <!-- XP text with glitch effect -->
  <div class="flex justify-between mt-2 font-mono text-sm">
    <span class="text-neon-cyan glow-text">{displayXP} / {maxXP} XP</span>
    <span class="text-gray-400">{Math.floor(percent)}%</span>
  </div>
  
  <!-- Level up indicator (brief) -->
  {#if glitchActive}
    <div class="absolute -top-8 left-1/2 transform -translate-x-1/2 text-neon-cyan font-bold animate-glitch">
      LEVEL UP!
    </div>
  {/if}
</div>