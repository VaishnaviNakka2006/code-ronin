<script lang="ts">
  import { onMount } from 'svelte';
  import { goto } from '$app/navigation';
  import { battleWS } from '$lib/services/battleWebSocket';

  let difficulty = 'easy';
  let statusText = '';
  let isInQueue = false;

  let unsubscribeStatus: (() => void) | null = null;

  function updateStatus(status: string) {
    switch (status) {
      case 'disconnected':
        statusText = 'Disconnected. Reconnecting...';
        break;

      case 'connecting':
        statusText = 'Connecting...';
        break;

      case 'connected':
        statusText = 'Ready. Select difficulty and find match.';
        break;

      case 'in_queue':
        statusText = `Searching (${difficulty})...`;
        break;

      case 'matched':
        statusText = 'Match found! Redirecting...';
        break;

      default:
        statusText = '';
    }
  }

  onMount(() => {
    battleWS.connect();

    unsubscribeStatus = battleWS.status.subscribe((status) => {
      updateStatus(status);

      isInQueue = status === 'in_queue';
    });

    battleWS.onMessage((event) => {

        console.log("LOBBY EVENT:", event);

        if (event.type === "battle_found") {

            console.log("MATCH FOUND");

            console.log(event);

            goto(`/battle/${event.room_id}`);
        }

    });

    return () => {
      if (unsubscribeStatus) {
        unsubscribeStatus();
      }

      battleWS.disconnect();
    };
  });

  function findMatch() {
    battleWS.joinQueue(difficulty);
  }

  function cancelSearch() {
    battleWS.leaveQueue();
  }
</script>

<div class="min-h-screen bg-neon-dark p-8">
  <div class="max-w-md mx-auto">

    <h1 class="text-3xl font-mono glow-text mb-6">
      ⚔️ Battle Lobby
    </h1>

    <div class="bg-black/40 p-6 rounded-lg border border-neon-cyan">

      <div class="mb-4">
        <label class="block mb-2 text-sm text-neon-cyan">
          Difficulty
        </label>

        <select
          bind:value={difficulty}
          disabled={isInQueue}
          class="w-full bg-black/60 border border-neon-cyan rounded p-2"
        >
          <option value="easy">Easy</option>
          <option value="medium">Medium</option>
          <option value="hard">Hard</option>
        </select>
      </div>

      <div class="flex gap-4">

        {#if !isInQueue}
          <button
            on:click={findMatch}
            class="flex-1 px-4 py-2 rounded bg-neon-cyan text-black font-bold hover:shadow-[0_0_20px_#00f3ff]"
          >
            FIND MATCH
          </button>

        {:else}

          <button
            on:click={cancelSearch}
            class="flex-1 px-4 py-2 rounded bg-red-500 text-white font-bold hover:shadow-[0_0_20px_#ff0000]"
          >
            CANCEL
          </button>

        {/if}

      </div>

      <div class="mt-6 text-sm font-mono text-neon-cyan">
        {statusText}
      </div>

    </div>

  </div>
</div>