<script lang="ts">
  export let health = 100;
  export let maxHealth = 100;
  $: percent = (health / maxHealth) * 100;
</script>

<div class="w-full bg-red-900 rounded-full h-5 overflow-hidden border border-red-500">
  <div class="bg-red-500 h-full transition-all duration-300" style="width: {percent}%"></div>
</div>
<div class="flex justify-between text-sm">
  <span class="text-red-400 font-mono">🐉 BOSS HP</span>
  <span class="text-red-400 font-mono">{health} / {maxHealth}</span>
</div>