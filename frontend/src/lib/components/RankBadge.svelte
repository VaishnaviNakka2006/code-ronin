<script lang="ts">
  export let rank: 'Scavenger' | 'Runner' | 'Hacker' = 'Scavenger';

  const rankColors = {
    Scavenger: 'text-gray-400 border-gray-500',
    Runner: 'text-neon-cyan border-neon-cyan',
    Hacker: 'text-neon-magenta border-neon-magenta',
  };
</script>

<div class="inline-block px-4 py-1 border rounded-full font-mono text-sm {rankColors[rank]} bg-black/50 backdrop-blur">
  {rank.toUpperCase()}
</div>