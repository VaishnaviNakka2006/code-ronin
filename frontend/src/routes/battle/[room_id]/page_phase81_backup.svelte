<script lang="ts">
  import { page } from '$app/state';
  import { onMount } from 'svelte';
  import { goto } from '$app/navigation';
  import { getBattleRoom } from '$lib/api/battle';

  let roomId = '';
  let roomInfo: any = null;
  let loading = true;
  let error = '';

  onMount(async () => {
    roomId = page.params.room_id;

    try {
      roomInfo = await getBattleRoom(roomId);
    } catch (err) {
      console.error(err);
      error = 'Room not found.';
    } finally {
      loading = false;
    }
  });
</script>

<div class="min-h-screen bg-neon-dark p-8">
  <div class="max-w-2xl mx-auto">

    {#if loading}
      <div class="text-neon-cyan font-mono animate-pulse">
        Loading battle...
      </div>

    {:else if error}
      <div class="bg-black/40 p-6 rounded-lg border border-red-500">
        <h1 class="text-2xl font-mono text-red-400 mb-4">
          Battle Room
        </h1>

        <p class="text-red-300">
          {error}
        </p>

        <button
          class="mt-6 px-4 py-2 bg-neon-cyan text-black rounded"
          onclick={() => goto('/battle/lobby')}
        >
          Back to Lobby
        </button>
      </div>

    {:else}

      <div class="bg-black/40 p-6 rounded-lg border border-neon-cyan">

        <h1 class="text-3xl font-mono glow-text mb-6">
          ⚔️ Battle Room
        </h1>

        <p class="text-gray-300">
          Room ID:
          <span class="text-neon-cyan font-mono">
            {roomId}
          </span>
        </p>

        <p class="text-gray-300 mt-2">
          Difficulty:
          <span class="text-yellow-400">
            {roomInfo.difficulty}
          </span>
        </p>

        <div class="flex justify-between mt-8">

          <div class="text-center flex-1">
            <div class="text-sm text-gray-400">
              Player 1
            </div>

            <div class="text-xl font-mono text-neon-cyan mt-2">
              {roomInfo.player1_username}
            </div>
          </div>

          <div class="flex items-center justify-center px-8">
            <span class="text-3xl text-neon-magenta">
              VS
            </span>
          </div>

          <div class="text-center flex-1">
            <div class="text-sm text-gray-400">
              Player 2
            </div>

            <div class="text-xl font-mono text-neon-magenta mt-2">
              {roomInfo.player2_username}
            </div>
          </div>

        </div>

        <div class="mt-10 text-center text-gray-400">
          ⏳ Waiting for battle to start...
        </div>

        <div class="mt-3 text-center text-xs text-gray-500">
          Battle engine will be implemented in Phase 8.2
        </div>

        <div class="mt-8 text-center">
          <button
            class="px-5 py-2 bg-neon-cyan text-black rounded"
            onclick={() => goto('/dashboard')}
          >
            Return to Dashboard
          </button>
        </div>

      </div>

    {/if}

  </div>
</div>