<script lang="ts">
  export let xp = 0;
  export let maxXP = 100;

  $: percent = (xp / maxXP) * 100;
</script>

<div class="w-full bg-gray-800 rounded-full h-3 overflow-hidden">
  <div
    class="bg-gradient-to-r from-neon-cyan to-neon-magenta h-full transition-all duration-500"
    style="width: {percent}%"
  ></div>
</div>

<p class="text-right text-xs text-neon-cyan mt-1">
  {xp} / {maxXP} XP
</p>