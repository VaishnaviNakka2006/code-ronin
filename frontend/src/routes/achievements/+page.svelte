<script lang="ts">
  import { onMount } from 'svelte';

  import {
    achievements,
    unlockedCount,
    loadAchievements
  } from '$lib/stores/achievementStore';

  import AchievementCard from '$lib/components/achievements/AchievementCard.svelte';

  let loading = true;

  onMount(async () => {
    await loadAchievements();

    loading = false;
  });
</script>

<div class="min-h-screen bg-black p-8">
  <div class="max-w-6xl mx-auto">

    <div class="flex justify-between items-center mb-8">

      <h1 class="text-4xl font-mono text-cyan-400">
        ACHIEVEMENTS
      </h1>

      <div class="text-cyan-400 font-mono">
        {$unlockedCount} / {$achievements.length} unlocked
      </div>

    </div>

    {#if loading}

      <div class="text-center text-cyan-400 font-mono animate-pulse">
        LOADING ACHIEVEMENTS...
      </div>

    {:else}

      <div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">

        {#each $achievements as ach (ach.id)}

          <AchievementCard achievement={ach} />

        {/each}

      </div>

    {/if}

  </div>
</div>