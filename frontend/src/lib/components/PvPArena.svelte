<script lang="ts">
  import { onMount } from 'svelte';

  let socket: WebSocket;

  let messages: string[] = [];

  let input = '';

  let connected = false;

  onMount(() => {

    socket = new WebSocket(
      'wss://code-ronin.onrender.com/ws/pvp'
    );

    socket.onopen = () => {

      connected = true;

      messages = [
        ...messages,
        '✅ Connected to PvP Arena'
      ];
    };

    socket.onmessage = (event) => {

      messages = [
        ...messages,
        event.data
      ];
    };

    socket.onclose = () => {

      connected = false;

      messages = [
        ...messages,
        '❌ Disconnected'
      ];
    };
  });

  function sendMessage() {

    if (
      socket &&
      input.trim()
    ) {

      socket.send(input);

      input = '';
    }
  }
</script>

<div
  class="min-h-screen bg-black text-white p-6"
>

  <div
    class="max-w-4xl mx-auto"
  >

    <h1
      class="text-4xl font-mono text-cyan-400 mb-6"
    >
      ⚔️ PvP Arena
    </h1>

    <div
      class="mb-4 text-sm"
    >

      Status:

      {#if connected}

        <span class="text-green-400">
          CONNECTED
        </span>

      {:else}

        <span class="text-red-400">
          OFFLINE
        </span>

      {/if}

    </div>

    <!-- Messages -->
    <div
      class="bg-black/60 border border-cyan-500 rounded-lg h-[400px] overflow-y-auto p-4 font-mono text-sm"
    >

      {#each messages as msg}

        <div class="mb-2">
          {msg}
        </div>

      {/each}

    </div>

    <!-- Input -->
    <div
      class="flex gap-3 mt-4"
    >

      <input
        bind:value={input}

        placeholder="Send battle message..."

        class="flex-1 bg-black border border-cyan-500 rounded-lg p-3 outline-none"
      />

      <button
        on:click={sendMessage}

        class="bg-cyan-500 text-black px-6 rounded-lg font-bold hover:bg-cyan-400"
      >
        SEND
      </button>

    </div>

  </div>

</div>