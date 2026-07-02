<script lang="ts">
  import { page } from '$app/stores';
  import { onMount } from 'svelte';
  import { goto } from '$app/navigation';
  import { battleWS } from '$lib/services/battleWebSocket';
  import { supabase } from '$lib/supabaseClient';
  import { getBattleRoom } from '$lib/api/battle';

  let roomId = $page.params.room_id;
  let roomInfo: any = null;
  let loading = true;
  let myUserId = '';
  let myReady = false;
  let opponentReady = false;
  let roomStatus = 'waiting';
  let error = '';

  let countdown: number | null = null;
  let battleStarted = false;
  let problemData: any = null;

  async function fetchRoom() {
    try {
      roomInfo = await getBattleRoom(roomId);
    } catch (err: any) {
      console.error(err);
      error = 'Failed to load room details.';
    } finally {
      loading = false;
    }
  }

  onMount(async () => {
    const session = await supabase.auth.getSession();
    myUserId = session.data.session?.user?.id || '';

    await fetchRoom();

    // Connect WebSocket and join room
    await battleWS.connect();

    battleWS.joinRoom(roomId);

    // Give the server a moment to register the room
    await new Promise(resolve => setTimeout(resolve, 200));

    // Listen for room_state events
    const unsubscribe = battleWS.onMessage((event) => {

      // Room state updates
      if (event.type === 'room_state' && event.room_id === roomId) {
        roomStatus = event.status;

        if (event.status !== 'active') {
          battleStarted = false;
          problemData = null;
        }

        if (event.player1_id === myUserId) {
          myReady = event.player1_ready;
          opponentReady = event.player2_ready;
        } else if (event.player2_id === myUserId) {
          myReady = event.player2_ready;
          opponentReady = event.player1_ready;
        }
      }

      // Countdown updates
      if (event.type === 'countdown_update' && event.room_id === roomId) {
        countdown = event.countdown;
      }

      // Battle started
      if (event.type === 'battle_start' && event.room_id === roomId) {
        battleStarted = true;
        countdown = null;
        roomStatus = 'active';
        problemData = event.problem;
      }

    });

    return () => {
      unsubscribe();
      // Optionally leave room? For MVP, we just close connection.
      // BattleWS disconnect is called in lobby cleanup, but here we keep it open.
    };
  });

  function toggleReady() {
    if (roomStatus === 'waiting' || roomStatus === 'ready') {
      if (myReady) {
        battleWS.notReady();
      } else {
        battleWS.ready();
      }
    }
  }

  $: statusLabel = roomStatus.toUpperCase();
</script>

<div class="min-h-screen bg-neon-dark p-8">
  <div class="max-w-2xl mx-auto">
    {#if loading}
      <div class="text-neon-cyan font-mono animate-pulse">Loading battle...</div>
    {:else if error}
      <div class="text-red-500 font-mono">{error}</div>
    {:else if roomInfo}
      <div class="bg-black/40 p-6 rounded-lg border border-neon-cyan shadow-lg">
        <h1 class="text-3xl font-mono glow-text mb-4">⚔️ BATTLE ROOM</h1>

        <div class="flex flex-wrap justify-between gap-4 text-sm text-gray-300 border-b border-neon-cyan/30 pb-4 mb-4">
          <span>Room: <span class="font-mono text-neon-cyan">{roomId.slice(0, 8)}</span></span>
          <span>Difficulty: <span class="text-yellow-400 font-mono">{roomInfo.difficulty}</span></span>
          <span>Status: <span class="font-mono {roomStatus === 'ready' ? 'text-green-400' : 'text-yellow-400'}">{statusLabel}</span></span>
        </div>

        <!-- Players -->
        <div class="grid grid-cols-2 gap-6">
          <div class="p-4 border border-neon-cyan/30 rounded-lg text-center">
            <div class="text-sm text-gray-400">Player 1</div>
            <div class="font-mono text-neon-cyan text-xl mt-1">{roomInfo.player1_username}</div>
            <div class="mt-2 text-xs">
              {#if myUserId === roomInfo.player1_id}
                <span class="text-green-400">(You)</span>
              {/if}
            </div>
            <div class="mt-3">
              {#if myUserId === roomInfo.player1_id}
                {#if myReady}<span class="text-green-400 font-mono text-sm">✅ READY</span>{:else}<span class="text-yellow-400 font-mono text-sm">⏳ NOT READY</span>{/if}
              {:else}
                {#if opponentReady}<span class="text-green-400 font-mono text-sm">✅ READY</span>{:else}<span class="text-gray-500 font-mono text-sm">⏳ Waiting...</span>{/if}
              {/if}
            </div>
          </div>
          <div class="p-4 border border-neon-magenta/30 rounded-lg text-center">
            <div class="text-sm text-gray-400">Player 2</div>
            <div class="font-mono text-neon-magenta text-xl mt-1">{roomInfo.player2_username}</div>
            <div class="mt-2 text-xs">
              {#if myUserId === roomInfo.player2_id}
                <span class="text-green-400">(You)</span>
              {/if}
            </div>
            <div class="mt-3">
              {#if myUserId === roomInfo.player2_id}
                {#if myReady}<span class="text-green-400 font-mono text-sm">✅ READY</span>{:else}<span class="text-yellow-400 font-mono text-sm">⏳ NOT READY</span>{/if}
              {:else}
                {#if opponentReady}<span class="text-green-400 font-mono text-sm">✅ READY</span>{:else}<span class="text-gray-500 font-mono text-sm">⏳ Waiting...</span>{/if}
              {/if}
            </div>
          </div>
        </div>

        {#if countdown !== null && !battleStarted}
          <div class="text-center py-8">
            <p class="text-8xl font-mono text-neon-cyan glow-text animate-pulse">
              {countdown}
            </p>
            <p class="text-sm text-gray-400 mt-2">
              Get ready!
            </p>
          </div>
        {/if}

        {#if !battleStarted && countdown === null}
          <div class="mt-8 text-center">
            <button
              on:click={toggleReady}
              disabled={roomStatus !== 'waiting' && roomStatus !== 'ready'}
              class="px-6 py-3 bg-neon-cyan text-black font-bold rounded-lg hover:shadow-[0_0_20px_#00f3ff] transition disabled:opacity-50 disabled:cursor-not-allowed"
            >
              {myReady ? 'NOT READY' : 'READY'}
            </button>

            <p class="mt-2 text-sm text-gray-400">
              {#if roomStatus === 'waiting' || roomStatus === 'ready'}
                {#if myReady}
                  You are ready. Waiting for opponent...
                {:else}
                  Click "READY" when you are prepared.
                {/if}
              {:else}
                Battle already in progress.
              {/if}
            </p>
          </div>

        {:else if battleStarted && problemData}
          <div class="mt-6 p-4 bg-black/60 rounded-lg border border-neon-cyan">

            <h2 class="text-2xl font-mono text-neon-cyan glow-text">
              {problemData.title}
            </h2>

            <p class="text-gray-300 mt-2 whitespace-pre-wrap">
              {problemData.description}
            </p>

            <div class="mt-4">
              <p class="text-sm text-gray-400">
                Starter code
              </p>

              <pre class="bg-black/80 p-3 rounded border border-gray-700 font-mono text-sm text-green-400 overflow-x-auto">
        {problemData.starter_code}
              </pre>
            </div>

          </div>

        {:else if battleStarted}

          <div class="mt-8 text-center text-neon-magenta font-mono text-2xl animate-pulse">
            ⚔️ BATTLE IN PROGRESS
          </div>

        {/if}

        <div class="mt-6 text-center">
          <button on:click={() => goto('/dashboard')} class="text-sm text-gray-500 hover:text-neon-cyan transition">
            Return to Dashboard
          </button>
        </div>
      </div>
    {:else}
      <div class="text-red-500">Room not found or invalid.</div>
    {/if}
  </div>
</div>