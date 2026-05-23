<script lang="ts">
  import {
    latestAchievement
  }
  from '$lib/stores/achievements';

  let visible = false;

  $: if ($latestAchievement) {

    visible = true;

    setTimeout(() => {
      visible = false;
    }, 4000);
  }
</script>

{#if visible && $latestAchievement}

<div
  class="fixed top-6 right-6 z-[9999]
  bg-black/90 border border-yellow-400
  rounded-xl p-5 shadow-2xl
  backdrop-blur-md animate-pulse
  w-[320px]"
>

  <div class="text-yellow-400 text-sm font-mono">
    🏆 ACHIEVEMENT UNLOCKED
  </div>

  <div class="mt-2 text-white text-lg font-bold">
    {$latestAchievement.name}
  </div>

  <div class="text-gray-300 text-sm mt-1">
    {$latestAchievement.description}
  </div>

  <div class="mt-3 text-cyan-400 text-sm">
    +{$latestAchievement.xpReward} XP
  </div>

</div>

{/if}