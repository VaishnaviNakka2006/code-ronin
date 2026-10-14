<script lang="ts">
  export let roomId: string;
  export let roomInfo: {
    player1_id: string;
    player2_id: string;
    player1_username: string;
    player2_username: string;
    difficulty: string;
    status: string;
  };
  export let myUserId: string;
  export let myReady: boolean;
  export let opponentReady: boolean;
  export let roomStatus: string;
  export let timerSeconds: number | null;
  export let problemTitle: string | null;
  export let finalSubmitted: boolean;
  export let opponentSubmitted: boolean;

  function formatTime(seconds: number): string {
    const m = Math.floor(seconds / 60);
    const s = seconds % 60;
    return `${m.toString().padStart(2, '0')}:${s.toString().padStart(2, '0')}`;
  }

  $: isPlayer1 = myUserId === roomInfo.player1_id;
  $: myName = isPlayer1 ? roomInfo.player1_username : roomInfo.player2_username;
  $: opponentName = isPlayer1 ? roomInfo.player2_username : roomInfo.player1_username;
  $: shortRoomId = roomId.slice(0, 8);

  function playerStatusLabel(isMe: boolean): { text: string; color: string } {
    const ready = isMe ? myReady : opponentReady;
    const submitted = isMe ? finalSubmitted : opponentSubmitted;
    if (submitted) return { text: '✅ SUBMITTED', color: 'text-neon-cyan' };
    if (ready) return { text: '✅ READY', color: 'text-green-400' };
    if (isMe) return { text: '⏳ NOT READY', color: 'text-yellow-400' };
    return { text: '⏳ WAITING', color: 'text-gray-500' };
  }

  $: myStatus = playerStatusLabel(true);
  $: oppStatus = playerStatusLabel(false);

  const DIFFICULTY_COLORS: Record<string, string> = {
    easy: 'text-green-400',
    medium: 'text-yellow-400',
    hard: 'text-orange-400'
  };
  $: difficultyColor = DIFFICULTY_COLORS[roomInfo.difficulty] ?? 'text-yellow-400';

  $: statusColor =
    roomStatus === 'active' ? 'text-green-400'
    : roomStatus === 'finished' ? 'text-neon-magenta'
    : roomStatus === 'countdown' ? 'text-neon-cyan'
    : 'text-yellow-400';
</script>

<div class="mb-6 bg-black/40 border border-neon-cyan/30 rounded-lg shadow-lg overflow-hidden">

  <!-- Top meta bar -->
  <div class="flex flex-wrap items-center gap-x-3 gap-y-1 px-4 py-2 border-b border-neon-cyan/20 text-xs font-mono">
    <span class="text-neon-cyan glow-text font-bold tracking-widest text-sm">
      ⚔️ BATTLE ARENA
    </span>
    <span class="text-gray-600">·</span>
    <span class="text-gray-400">
      ROOM <span class="text-neon-cyan">{shortRoomId}</span>
    </span>
    <span class="text-gray-600">·</span>
    <span class="text-gray-400">
      DIFFICULTY <span class="{difficultyColor}">{roomInfo.difficulty.toUpperCase()}</span>
    </span>
    <span class="text-gray-600">·</span>
    <span class="text-gray-400">
      STATUS <span class="{statusColor}">{roomStatus.toUpperCase()}</span>
    </span>
    <span class="ml-auto flex items-center gap-2 text-gray-400">
      ⏱️
      <span class="text-neon-cyan font-bold">
        {timerSeconds !== null ? formatTime(timerSeconds) : '--:--'}
      </span>
    </span>
  </div>

  <!-- Players row -->
  <div class="grid grid-cols-[1fr_auto_1fr] items-center gap-2 px-4 py-3">
    <div class="text-right min-w-0">
      <div class="font-mono text-neon-cyan text-sm md:text-base truncate">
        {myName}
      </div>
      <div class="text-[10px] font-mono text-gray-500 mt-0.5 tracking-widest">YOU</div>
      <div class="text-[11px] font-mono mt-1 {myStatus.color}">{myStatus.text}</div>
    </div>

    <div class="text-neon-magenta font-mono text-lg md:text-xl font-bold glow-text px-2">
      VS
    </div>

    <div class="text-left min-w-0">
      <div class="font-mono text-neon-magenta text-sm md:text-base truncate">
        {opponentName}
      </div>
      <div class="text-[10px] font-mono text-gray-500 mt-0.5 tracking-widest">OPPONENT</div>
      <div class="text-[11px] font-mono mt-1 {oppStatus.color}">{oppStatus.text}</div>
    </div>
  </div>

  <!-- Problem title -->
  {#if problemTitle}
    <div class="px-4 py-2 border-t border-neon-cyan/20 text-xs font-mono">
      <span class="text-gray-500">📋 PROBLEM </span>
      <span class="text-neon-cyan">{problemTitle}</span>
    </div>
  {/if}
</div>