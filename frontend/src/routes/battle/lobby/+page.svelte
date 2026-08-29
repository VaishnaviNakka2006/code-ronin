<script lang="ts">
  import { onMount } from 'svelte';
  import { goto } from '$app/navigation';
  import { battleWS } from '$lib/services/battleWebSocket';

  let difficulty = 'easy';
  let statusText = '';
  let isInQueue = false;

  let unsubscribeStatus: (() => void) | null = null;
  let unsubscribeMessage: (() => void) | null = null;

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

  function findMatch() {
    console.log('FIND MATCH BUTTON CLICKED');
    console.log('Selected difficulty:', difficulty);

    try {
      battleWS.joinQueue(difficulty);
      console.log('joinQueue message sent');
    } catch (err) {
      console.error('Find match failed:', err);
      statusText = 'Failed to join matchmaking queue.';
    }
  }

  function cancelSearch() {
    battleWS.leaveQueue();
  }

  onMount(() => {
    async function setup() {
      try {
        await battleWS.connect();

        unsubscribeStatus = battleWS.status.subscribe((status) => {
          console.log('Battle status:', status);

          updateStatus(status);

          isInQueue = status === 'in_queue';
        });

        unsubscribeMessage = battleWS.onMessage((event) => {
          console.log('LOBBY EVENT:', event);

          if (
            event.type === 'battle_found' ||
            event.type === 'room_joined'
          ) {
            console.log('MATCH FOUND:', event);

            goto(`/battle/${event.room_id}`);
          }

          if (event.type === 'error') {
            console.error('Battle error:', event.message);

            statusText = event.message || 'Battle error.';
            isInQueue = false;
          }
        });
      } catch (err) {
        console.error('Battle WebSocket connection failed:', err);
        statusText = 'Failed to connect to battle server.';
      }
    }

    setup();

    return () => {
      if (unsubscribeStatus) {
        unsubscribeStatus();
      }

      if (unsubscribeMessage) {
        unsubscribeMessage();
      }
    };
  });
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
            class="flex-1 px-4 py-2 rounded bg-neon-cyan text-black font-bold hover:shadow-[0_0_20px_#00f3ff] transition"
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