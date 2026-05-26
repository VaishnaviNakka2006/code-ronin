<script lang="ts">
  import type { Achievement } from '$lib/types/achievement';

  export let achievement: Achievement;

  $: isUnlocked = achievement.unlocked;
</script>

<div
  class="relative p-4 rounded-lg border-2 transition-all duration-300
    {isUnlocked
      ? 'border-cyan-400 shadow-lg bg-black/60 backdrop-blur-sm'
      : 'border-gray-700 bg-black/30 opacity-60 grayscale'}
    hover:scale-105 cursor-default"
>
  {#if isUnlocked}
    <div class="absolute inset-0 rounded-lg border-2 border-cyan-400/30 animate-pulse pointer-events-none"></div>
  {/if}

  <div class="flex items-start gap-3">
    <div class="text-4xl">
      {#if achievement.icon_name === 'blood'}🩸
      {:else if achievement.icon_name === 'streak'}🔥
      {:else if achievement.icon_name === 'skull'}💀
      {:else if achievement.icon_name === 'star'}⭐
      {:else if achievement.icon_name === 'xp'}⚡
      {:else if achievement.icon_name === 'calendar'}📅
      {:else}🏆
      {/if}
    </div>

    <div class="flex-1">
      <h3 class="font-mono text-lg font-bold text-cyan-400">
        {achievement.name}
      </h3>

      <p class="text-sm text-gray-300">
        {achievement.description}
      </p>

      <div class="flex justify-between items-center mt-2 text-xs">
        <span class="text-pink-400">
          +{achievement.xp_reward} XP
        </span>

        {#if isUnlocked && achievement.unlocked_at}
          <span class="text-gray-500">
            Unlocked:
            {new Date(achievement.unlocked_at).toLocaleDateString()}
          </span>
        {/if}
      </div>
    </div>
  </div>

  {#if !isUnlocked}
    <div class="absolute inset-0 flex items-center justify-center bg-black/50 rounded-lg">
      <span class="text-gray-400 text-sm font-mono">
        ??? LOCKED ???
      </span>
    </div>
  {/if}
</div>