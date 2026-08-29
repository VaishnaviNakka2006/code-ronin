<script lang="ts">
  import { page } from '$app/stores';
  import { onMount } from 'svelte';
  import { goto } from '$app/navigation';
  import { battleWS } from '$lib/services/battleWebSocket';
  import { supabase } from '$lib/supabaseClient';
  import { getBattleRoom } from '$lib/api/battle';
  import CodeEditor from '$lib/components/CodeEditor.svelte';

  let roomId = $page.params.room_id ?? '';
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
  let timerSeconds: number | null = null;
  let code = '';
  let codeResult: any = null;
  let isSubmitting = false;
  let codeEditorKey = 0;

  // NEW: Phase 4 state
  let finalSubmitted = false;
  let opponentSubmitted = false;
  let finalSubmitting = false;
  let battleResult: any = null;
  let showResult = false;
  let gameOver = false;

  function submitCode() {
    if (!code.trim() || finalSubmitted) {
      return;
    }
    isSubmitting = true;
    battleWS.submitCode(code);
  }

  // NEW: Submit final solution
  function submitFinal() {
    if (!code.trim() || finalSubmitted || gameOver) {
      return;
    }
    finalSubmitting = true;
    battleWS.submitFinal(code);
  }

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

  onMount(() => {
    let unsubscribe: (() => void) | undefined;

    async function initializeBattle() {
      try {
        const session = await supabase.auth.getSession();
        myUserId = session.data.session?.user?.id || '';

        await fetchRoom();

        if (!roomInfo) {
          return;
        }

        unsubscribe = battleWS.onMessage((event) => {
          console.log('BATTLE ROOM EVENT:', event);

          // ================================
          // CODE RESULT
          // ================================
          if (event.type === 'code_result' && event.room_id === roomId) {
            isSubmitting = false;
            codeResult = event;
          }

          // ================================
          // ERROR
          // ================================
          if (event.type === 'error') {
            isSubmitting = false;
            finalSubmitting = false;
            error = event.message || 'Battle error';
          }

          // ================================
          // ROOM STATE
          // ================================
          if (event.type === 'room_state' && event.room_id === roomId) {
            console.log('ROOM STATE:', event);
            roomStatus = event.status;
            if (event.player1_id === myUserId) {
              myReady = event.player1_ready;
              opponentReady = event.player2_ready;
            } else if (event.player2_id === myUserId) {
              myReady = event.player2_ready;
              opponentReady = event.player1_ready;
            }
          }

          // ================================
          // COUNTDOWN
          // ================================
          if (event.type === 'countdown_update' && event.room_id === roomId) {
            console.log('COUNTDOWN:', event.countdown);
            countdown = event.countdown;
            roomStatus = 'countdown';
          }

          // ================================
          // BATTLE START
          // ================================
          if (event.type === 'battle_start' && event.room_id === roomId) {
            console.log('BATTLE START:', event);
            battleStarted = true;
            countdown = null;
            roomStatus = 'active';
            problemData = event.problem;
            code = event.problem?.starter_code || '';
            codeEditorKey += 1;
            codeResult = null;
            isSubmitting = false;
            finalSubmitted = false;
            opponentSubmitted = false;
            finalSubmitting = false;
            battleResult = null;
            showResult = false;
            gameOver = false;
          }

          // ================================
          // TIMER UPDATE
          // ================================
          if (event.type === 'timer_update' && event.room_id === roomId) {
            timerSeconds = event.seconds;
          }

          // ================================
          // TIMER END (fallback)
          // ================================
          if (event.type === 'timer_end' && event.room_id === roomId) {
            timerSeconds = 0;
            roomStatus = 'finished';
            // If battle hasn't been finalized yet, we show result with whatever we have
            if (!gameOver) {
              // We'll wait for battle_finished, but if it doesn't come, we'll show a generic result
              // We'll handle this in a separate timeout or rely on battle_finished
            }
          }

          // ================================
          // FINAL SUBMISSION ACK
          // ================================
          if (event.type === 'final_submission_ack' && event.room_id === roomId) {
            finalSubmitting = false;
            finalSubmitted = true;
            // Optionally show a message
          }

          // ================================
          // OPPONENT SUBMITTED
          // ================================
          if (event.type === 'opponent_submitted' && event.room_id === roomId) {
            opponentSubmitted = true;
            // Show a notification (we'll handle in UI)
          }

          // ================================
          // BATTLE FINISHED
          // ================================
          if (event.type === 'battle_finished' && event.room_id === roomId) {
            console.log('BATTLE FINISHED:', event);
            battleResult = event;
            showResult = true;
            gameOver = true;
            roomStatus = 'finished';
            timerSeconds = 0;
            // Disable further code execution
            finalSubmitting = false;
          }
        });

        await battleWS.connect();
        console.log('Joining battle room:', roomId);
        battleWS.joinRoom(roomId);

        // Set a safety timeout: if battle_finished doesn't arrive within 10 seconds of timer_end,
        // we could show a fallback result, but we'll rely on the backend.

      } catch (err: any) {
        console.error('Battle initialization failed:', err);
        error = 'Failed to connect to battle server.';
      }
    }

    initializeBattle();

    return () => {
      unsubscribe?.();
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

  function formatTime(seconds: number): string {
    const minutes = Math.floor(seconds / 60);
    const secs = seconds % 60;
    return `${minutes.toString().padStart(2, '0')}:${secs.toString().padStart(2, '0')}`;
  }

  function getWinnerUsername(): string {
    if (!battleResult) return 'Unknown';
    if (battleResult.draw) return 'Draw';
    const winnerId = battleResult.winner_id;
    if (winnerId === roomInfo.player1_id) return roomInfo.player1_username;
    if (winnerId === roomInfo.player2_id) return roomInfo.player2_username;
    return 'Unknown';
  }

  function getMyScore(): number {
    if (!battleResult) return 0;
    if (myUserId === roomInfo?.player1_id) return battleResult.player1_score;
    if (myUserId === roomInfo?.player2_id) return battleResult.player2_score;
    return 0;
  }

  function getOpponentScore(): number {
    if (!battleResult) return 0;
    if (myUserId === roomInfo?.player1_id) return battleResult.player2_score;
    if (myUserId === roomInfo?.player2_id) return battleResult.player1_score;
    return 0;
  }

  function getMyTime(): number | null {
    if (!battleResult) return null;
    if (myUserId === roomInfo?.player1_id) return battleResult.player1_time;
    if (myUserId === roomInfo?.player2_id) return battleResult.player2_time;
    return null;
  }

  function getOpponentTime(): number | null {
    if (!battleResult) return null;
    if (myUserId === roomInfo?.player1_id) return battleResult.player2_time;
    if (myUserId === roomInfo?.player2_id) return battleResult.player1_time;
    return null;
  }

  function formatTimeDisplay(seconds: number | null): string {
    if (seconds === null || seconds === undefined) return 'N/A';
    return `${seconds.toFixed(1)}s`;
  }

  $: statusLabel = roomStatus.toUpperCase();
  $: isFinalButtonDisabled = finalSubmitting || finalSubmitted || gameOver || !battleStarted;
</script>

<div class="min-h-screen bg-neon-dark p-8">
  <div class="max-w-2xl mx-auto">

    {#if loading}
      <div class="text-neon-cyan font-mono animate-pulse">
        Loading battle...
      </div>

    {:else if error}
      <div class="text-red-500 font-mono">
        {error}
      </div>

    {:else if roomInfo}

      <!-- Result Screen Overlay -->
      {#if showResult && battleResult}
        <div class="fixed inset-0 z-50 flex items-center justify-center bg-black/80 backdrop-blur-md p-4">
          <div class="bg-black/90 border border-neon-cyan rounded-2xl p-8 max-w-lg w-full shadow-2xl">
            <h2 class="text-3xl font-mono glow-text text-center mb-4">
              {#if battleResult.draw}
                🤝 DRAW
              {:else}
                🏆 {getWinnerUsername()} WINS!
              {/if}
            </h2>

            <div class="grid grid-cols-2 gap-4 text-center mb-4">
              <div class="border-r border-neon-cyan/30 pr-4">
                <p class="text-sm text-gray-400">You</p>
                <p class="text-2xl font-mono text-neon-cyan">{getMyScore().toFixed(1)}</p>
                <p class="text-xs text-gray-500">Time: {formatTimeDisplay(getMyTime())}</p>
              </div>
              <div>
                <p class="text-sm text-gray-400">Opponent</p>
                <p class="text-2xl font-mono text-neon-magenta">{getOpponentScore().toFixed(1)}</p>
                <p class="text-xs text-gray-500">Time: {formatTimeDisplay(getOpponentTime())}</p>
              </div>
            </div>

            <div class="text-center text-sm text-gray-400 mb-4">
              <p>Problem: <span class="text-neon-cyan">{battleResult.problem_title || problemData?.title || 'Unknown'}</span></p>
              <p>Difficulty: <span class="text-yellow-400">{roomInfo.difficulty}</span></p>
            </div>

            <div class="flex gap-4 justify-center mt-6">
              <button
                on:click={() => goto('/battle/lobby')}
                class="px-6 py-2 bg-neon-cyan text-black font-bold rounded-lg hover:shadow-[0_0_20px_#00f3ff] transition"
              >
                🔄 Play Again
              </button>
              <button
                on:click={() => goto('/dashboard')}
                class="px-6 py-2 bg-gray-700 text-white font-bold rounded-lg hover:bg-gray-600 transition"
              >
                🏠 Dashboard
              </button>
            </div>
          </div>
        </div>
      {/if}

      <!-- Main Battle UI -->
      <div class="bg-black/40 p-6 rounded-lg border border-neon-cyan shadow-lg">

        <h1 class="text-3xl font-mono glow-text mb-4">
          ⚔️ BATTLE ROOM
        </h1>

        <!-- Room Info -->
        <div class="flex flex-wrap justify-between gap-4 text-sm text-gray-300 border-b border-neon-cyan/30 pb-4 mb-4">
          <span>
            Room: <span class="font-mono text-neon-cyan">{roomId.slice(0, 8)}</span>
          </span>
          <span>
            Difficulty: <span class="text-yellow-400 font-mono">{roomInfo.difficulty}</span>
          </span>
          <span>
            Status: <span class="font-mono {roomStatus === 'active' ? 'text-green-400' : 'text-yellow-400'}">
              {statusLabel}
            </span>
          </span>
          <span>
            ⏱️ <span class="font-mono text-neon-cyan">
              {timerSeconds !== null ? formatTime(timerSeconds) : '--:--'}
            </span>
          </span>
        </div>

        <!-- Players -->
        <div class="grid grid-cols-2 gap-6">
          <!-- Player 1 -->
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
                {#if finalSubmitted}
                  <span class="text-green-400 font-mono text-sm">✅ SUBMITTED</span>
                {:else if myReady}
                  <span class="text-green-400 font-mono text-sm">✅ READY</span>
                {:else}
                  <span class="text-yellow-400 font-mono text-sm">⏳ NOT READY</span>
                {/if}
              {:else}
                {#if opponentSubmitted}
                  <span class="text-green-400 font-mono text-sm">✅ SUBMITTED</span>
                {:else if opponentReady}
                  <span class="text-green-400 font-mono text-sm">✅ READY</span>
                {:else}
                  <span class="text-gray-500 font-mono text-sm">⏳ Waiting...</span>
                {/if}
              {/if}
            </div>
          </div>

          <!-- Player 2 -->
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
                {#if finalSubmitted}
                  <span class="text-green-400 font-mono text-sm">✅ SUBMITTED</span>
                {:else if myReady}
                  <span class="text-green-400 font-mono text-sm">✅ READY</span>
                {:else}
                  <span class="text-yellow-400 font-mono text-sm">⏳ NOT READY</span>
                {/if}
              {:else}
                {#if opponentSubmitted}
                  <span class="text-green-400 font-mono text-sm">✅ SUBMITTED</span>
                {:else if opponentReady}
                  <span class="text-green-400 font-mono text-sm">✅ READY</span>
                {:else}
                  <span class="text-gray-500 font-mono text-sm">⏳ Waiting...</span>
                {/if}
              {/if}
            </div>
          </div>
        </div>

        <!-- Countdown -->
        {#if countdown !== null && !battleStarted}
          <div class="text-center py-8">
            <p class="text-8xl font-mono text-neon-cyan glow-text animate-pulse">
              {countdown}
            </p>
            <p class="text-sm text-gray-400 mt-2">Get ready!</p>
          </div>
        {/if}

        <!-- Ready Button -->
        {#if !battleStarted && countdown === null && !showResult}
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
                Waiting for battle to begin...
              {/if}
            </p>
          </div>

        <!-- Battle Interface -->
        {:else if battleStarted && problemData && !showResult}
          <div class="mt-6 p-4 bg-black/60 rounded-lg border border-neon-cyan">
            <h2 class="text-2xl font-mono text-neon-cyan glow-text">
              {problemData.title}
            </h2>
            <p class="text-gray-300 mt-2 whitespace-pre-wrap">
              {problemData.description}
            </p>

            <div class="mt-4">
              <p class="text-sm text-gray-400">Starter code</p>
              <pre class="bg-black/80 p-3 rounded border border-gray-700 font-mono text-sm text-green-400 overflow-x-auto">{problemData.starter_code}</pre>
            </div>

            <!-- Code Editor -->
            <div class="mt-6">
              <p class="text-sm text-gray-400 mb-2">Your Solution</p>
              {#key codeEditorKey}
                <CodeEditor
                  bind:code={code}
                  language="python"
                  onExecute={submitCode}
                />
              {/key}
            </div>

            <!-- Action Buttons -->
            <div class="mt-4 flex flex-wrap gap-4 items-center">
              <button
                on:click={submitCode}
                disabled={isSubmitting || !code.trim() || finalSubmitted || gameOver}
                class="px-6 py-3 bg-neon-cyan text-black font-bold rounded-lg hover:shadow-[0_0_20px_#00f3ff] transition disabled:opacity-50 disabled:cursor-not-allowed"
              >
                {#if isSubmitting}
                  RUNNING...
                {:else}
                  ⚡ RUN CODE
                {/if}
              </button>

              <button
                on:click={submitFinal}
                disabled={isFinalButtonDisabled}
                class="px-6 py-3 bg-neon-magenta text-black font-bold rounded-lg hover:shadow-[0_0_20px_#ff00e5] transition disabled:opacity-50 disabled:cursor-not-allowed"
              >
                {#if finalSubmitting}
                  SUBMITTING...
                {:else if finalSubmitted}
                  ✅ SUBMITTED
                {:else}
                  📤 SUBMIT SOLUTION
                {/if}
              </button>

              {#if opponentSubmitted && !finalSubmitted}
                <span class="text-sm text-neon-cyan">Opponent has submitted their final solution.</span>
              {/if}
              {#if finalSubmitted && !opponentSubmitted}
                <span class="text-sm text-neon-cyan">You submitted. Waiting for opponent...</span>
              {/if}
              {#if finalSubmitted && opponentSubmitted}
                <span class="text-sm text-green-400">Both players submitted! Calculating results...</span>
              {/if}
            </div>

            <!-- Test Results -->
            {#if codeResult}
              <div class="mt-6 p-4 bg-black/60 rounded-lg border border-gray-700">
                <h3 class="text-lg font-mono text-neon-cyan mb-3">TEST RESULTS</h3>
                <div class="flex gap-6 text-sm">
                  <span>
                    Passed:
                    <span class="text-green-400">{codeResult.tests_passed}</span>
                    / {codeResult.total_tests}
                  </span>
                  <span>
                    Score:
                    <span class="text-yellow-400">{Math.round(codeResult.score * 100)}%</span>
                  </span>
                </div>
                <pre class="mt-4 p-3 bg-black/80 rounded text-sm text-gray-300 whitespace-pre-wrap overflow-x-auto">{codeResult.output}</pre>
              </div>
            {/if}
          </div>

        <!-- Battle started but no problem yet -->
        {:else if battleStarted && !showResult}
          <div class="mt-8 text-center text-neon-magenta font-mono text-2xl animate-pulse">
            ⚔️ BATTLE IN PROGRESS
          </div>

        {/if}

        <!-- Return to Dashboard (hidden when result is shown) -->
        {#if !showResult}
          <div class="mt-6 text-center">
            <button
              on:click={() => goto('/dashboard')}
              class="text-sm text-gray-500 hover:text-neon-cyan transition"
            >
              Return to Dashboard
            </button>
          </div>
        {/if}

      </div>

    {:else}
      <div class="text-red-500">Room not found or invalid.</div>
    {/if}

  </div>
</div>