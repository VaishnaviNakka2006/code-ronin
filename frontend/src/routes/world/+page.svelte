

<script lang="ts">
  import { goto } from '$app/navigation';
  import { onMount } from 'svelte';
  import { supabase } from '$lib/supabaseClient';

  const missions = [
    {
      id: 1,
      title: 'Variable Initialization',
      subtitle: 'Initialize your first variable',
      difficulty: 'EASY',
      xp: 10,
      boss: 'Training Protocol',
      isBoss: false,
      color: 'cyan'
    },
    {
      id: 2,
      title: 'The Broken Airlock',
      subtitle: 'Breach the outer firewall',
      difficulty: 'EASY',
      xp: 10,
      boss: 'Firewall Sentinel',
      isBoss: true,
      color: 'purple'
    },
    {
      id: 3,
      title: 'Corrupted Core',
      subtitle: 'Confront the system overlord',
      difficulty: 'HARD',
      xp: 50,
      boss: 'Corrupted Core',
      isBoss: true,
      color: 'red'
    }
  ];



  let completedMissionIds: number[] = [];
  let loadingProgress = true;
  let progressError = '';

  $: completedCount = missions.filter((mission) =>
    completedMissionIds.includes(mission.id)
  ).length;

  $: progressPercent = Math.round(
    (completedCount / missions.length) * 100
  );
  function isUnlocked(missionId: number): boolean {
    if (missionId === 1) return true;

    return completedMissionIds.includes(missionId - 1);
  }

  async function loadProgress() {
    loadingProgress = true;
    progressError = '';

    try {
      const apiUrl = import.meta.env.VITE_API_URL;

      if (!apiUrl) {
        throw new Error('Backend API URL is not configured.');
      }

      
      const { data: sessionData, error: sessionError } =
        await supabase.auth.getSession();
      
      if (sessionError || !sessionData.session) {
        throw new Error('Your login session is unavailable. Please sign in again.');
      }
      
      const token = sessionData.session.access_token;
      
      const response = await fetch(`${apiUrl}/missions/progress/me`, {
        headers: {
          Authorization: `Bearer ${token}`
        }
      });
      

      if (!response.ok) {
        throw new Error(
          response.status === 401
            ? 'Please sign in again to load your campaign progress.'
            : `Could not load progress (HTTP ${response.status}).`
        );
      }

      const data = await response.json();

      completedMissionIds = Array.isArray(data.completed_mission_ids)
        ? data.completed_mission_ids
            .map(Number)
            .filter((id: number) =>
              missions.some((mission) => mission.id === id)
            )
        : [];
    } catch (error) {
      progressError =
        error instanceof Error
          ? error.message
          : 'Unable to load campaign progress.';
    } finally {
      loadingProgress = false;
    }
  }

  
  function deployMission(id: number) {
    if (loadingProgress) {
      alert('Campaign progress is still loading. Please wait.');
      return;
    }

    if (progressError) {
      alert('Campaign progress could not load. Please sign in again.');
      return;
    }

    if (!isUnlocked(id)) {
      alert('Complete the previous mission to unlock this one.');
      return;
    }

    goto(`/mission/${id}`);
  }


  onMount(() => {
    void loadProgress();
  });
</script>


<svelte:head>
  <title>Mission World | Code Ronin</title>
  <meta
    name="description"
    content="Explore the Code Ronin mission world and face its enemies."
  />
</svelte:head>

<div class="min-h-screen bg-neon-dark px-4 py-8 text-white sm:px-8">
  <div class="mx-auto max-w-6xl">
    <a
      href="/dashboard"
      class="text-cyan-300 transition hover:text-cyan-100"
    >
      â† BACK TO DASHBOARD
    </a>

    <header class="my-8">
      <p class="font-mono text-sm tracking-[0.3em] text-cyan-400">
        NEXUS CAMPAIGN // SECTOR 01
      </p>

      <h1 class="mt-3 text-4xl font-black tracking-tight sm:text-6xl">
        MISSION <span class="text-cyan-400">WORLD</span>
      </h1>

      <p class="mt-4 max-w-2xl text-gray-300">
        Breach the defenses, master each challenge, and prepare for the
        Corrupted Core. Your next victory starts here.
      </p>
    </header>

    <section
      class="mb-8 rounded-2xl border border-cyan-500/40 bg-black/40 p-5"
    >
      <div class="flex flex-wrap items-center justify-between gap-4">
        <div>
          <p class="text-sm text-gray-400">CAMPAIGN</p>
          <h2 class="mt-1 text-2xl font-bold">Python Origins</h2>
        </div>

        <div class="rounded-lg border border-cyan-400/40 px-4 py-2 font-mono text-cyan-300">
          3 ENCOUNTERS
        </div>
      </div>

      <div class="mt-5 h-2 overflow-hidden rounded-full bg-gray-800">
        <div
          class="h-full rounded-full bg-cyan-400 transition-all duration-500"
          style={`width: ${progressPercent}%`}
        ></div>
      </div>
      <p class="mt-2 text-xs text-gray-500">
        {#if loadingProgress}
          Loading campaign progress...
        {:else if progressError}
          {progressError}
        {:else}
          {completedCount} of {missions.length} missions completed
          ({progressPercent}%)
        {/if}
      </p>
    </section>

    <div class="grid gap-5 md:grid-cols-2 lg:grid-cols-3">
      {#each missions as mission}
        <article
          class={`relative flex flex-col overflow-hidden rounded-2xl border bg-black/50 p-5 transition duration-300 hover:-translate-y-1 ${
            mission.isBoss
              ? 'border-red-500/70 hover:shadow-[0_0_28px_rgba(239,68,68,0.2)]'
              : mission.id === 2
                ? 'border-purple-400/50 hover:shadow-[0_0_24px_rgba(168,85,247,0.18)]'
                : 'border-cyan-400/50 hover:shadow-[0_0_24px_rgba(34,211,238,0.18)]'
          }`}
        >
          <div class="mb-5 flex items-start justify-between gap-3">
            <div
              class={`flex h-12 w-12 items-center justify-center rounded-xl border font-mono text-xl ${
                mission.isBoss
                  ? 'border-red-500/50 bg-red-500/10 text-red-400'
                  : mission.id === 2
                    ? 'border-purple-400/50 bg-purple-400/10 text-purple-300'
                    : 'border-cyan-400/50 bg-cyan-400/10 text-cyan-300'
              }`}
            >
              {mission.isBoss ? 'â˜ ' : `0${mission.id}`}
            </div>

            <span
              class={`rounded-full border px-3 py-1 text-xs font-bold tracking-wider ${
                mission.isBoss
                  ? 'border-red-500/50 text-red-400'
                  : 'border-gray-600 text-gray-300'
              }`}
            >
              {mission.difficulty}
            </span>
          </div>

          <p class="text-xs uppercase tracking-widest text-gray-500">
            Encounter {mission.id}
          </p>

          <h2 class="mt-2 text-xl font-bold">
            {mission.title}
          </h2>

          <p class="mt-2 min-h-12 text-sm text-gray-400">
            {mission.subtitle}
          </p>

          <div class="my-5 rounded-lg bg-white/5 p-3">
            <p class="text-xs text-gray-500">ENEMY</p>
            <p
              class={`mt-1 font-mono ${
                mission.isBoss ? 'text-red-400' : 'text-cyan-300'
              }`}
            >
              {mission.boss}
            </p>
          </div>

          <div class="mt-auto flex items-center justify-between gap-3">
            <span class="font-mono text-sm text-yellow-300">
              +{mission.xp} XP
            </span>

            <button
              type="button"
              on:click={() => deployMission(mission.id)}
              class={`rounded-lg px-4 py-2 text-sm font-bold transition ${
                mission.isBoss
                  ? 'bg-red-500 text-white hover:bg-red-400'
                  : 'bg-cyan-400 text-black hover:bg-cyan-300'
              }`}
            >
              {mission.isBoss ? 'FACE BOSS â†’' : 'DEPLOY â†’'}
            </button>
          </div>
        </article>
      {/each}
    </div>

    <footer class="mt-8 rounded-xl border border-gray-700 bg-black/30 p-4 text-sm text-gray-400">
      <span class="text-cyan-300">SYSTEM NOTE:</span>
      This first version displays the existing encounters. Mission locking,
      persistent completion tracking, and boss unlock rules are not enabled yet.
    </footer>
  </div>
</div>
