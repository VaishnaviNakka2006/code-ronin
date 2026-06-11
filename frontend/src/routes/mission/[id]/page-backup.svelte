<script lang="ts">
  import { page } from '$app/stores';
  import { onMount } from 'svelte';

  import CodeEditor from '$lib/components/CodeEditor.svelte';
  import AnimatedMentor from '$lib/components/AnimatedMentor.svelte';
  import BossBattle from '$lib/components/BossBattle.svelte';

  import CinematicIntro
    from '$lib/components/cinematic/CinematicIntro.svelte';

  import { bossHealth }
    from '$lib/stores/gameStore';

  import {
    showCinematic,
    startMission
  } from '$lib/stores/missionStore';

  import {
    submitMission
  } from '$lib/api/codeRunner';

  import { getAIHint }
  from '$lib/api/mentor';

  let missionId = Number($page.params.id);

  let output = '';

  let mentorMsg =
    'Awaiting code execution...';

  let bossVisible = false;

  let userCode = '';

  let cinematicDone = false;

  const missionsData = {

    1: {
      title: 'The Broken Airlock',

      description:
        'Set variable access_code = 1337 and print it.',

      isBoss: false
    },

    2: {
      title: 'Loop the Security Scan',

      description:
        'Use a loop to print numbers 1 to 5.',

      isBoss: false
    },

    3: {
      title: 'Corrupted Core (BOSS)',

      description:
        'Fix the syntax error.',

      isBoss: true
    }
  };

  async function loadMission() {

    try {

      let difficulty = 'easy';

      if (missionId === 2)
        difficulty = 'medium';

      if (missionId === 3)
        difficulty = 'hard';

      const res = await fetch(
        `${import.meta.env.VITE_API_URL}/missions/generate?difficulty=${difficulty}`
      );

      mission = await res.json();

    } catch (err) {

      console.error(err);

      mission = {
        title: 'Mission Load Failed',
        description: 'Backend connection failed.'
      };
    }
  }

  let mission: any = null;

  onMount(async () => {

    await loadMission();

    if (missionId === 3) {

      bossVisible = true;

      bossHealth.set(100);
    }

    await startMission(missionId);

    cinematicDone = true;
  });

  async function handleExecute() {

    output = 'Running...';

    try {

      const result =
        await submitMission(
          userCode,
          missionId
        );

      output =
        JSON.stringify(
          result,
          null,
          2
        );

      if (result.success) {

        mentorMsg =
          `Mission Complete! +${result.xp_gained} XP`;

        if (bossVisible) {

          bossHealth.update(
            h => Math.max(0, h - 50)
          );
        }

      } else {

        const ai =
          await getAIHint(
            result.error || '',
            userCode
          );

        mentorMsg =
          ai.hint ||
            'Mission failed.';
      }

    } catch (err) {

      console.error(err);

      output =
        'Execution failed';

      mentorMsg =
        'System error occurred.';
    }
  }
</script>

{#if $showCinematic}

<CinematicIntro
  missionTitle={
    mission?.title ||
    'UNKNOWN MISSION'
  }

  missionDifficulty={
    mission?.isBoss
      ? 'boss'
      : 'medium'
  }

  onComplete={() => {

    showCinematic.set(false);

    cinematicDone = true;

    if (
      window.__cinematicComplete
    ) {

      window.__cinematicComplete();
    }
  }}
/>

{/if}

{#if cinematicDone}

<div class="min-h-screen p-6 bg-neon-dark">

  <div class="max-w-6xl mx-auto">

    <div class="flex justify-between items-center mb-6">

      <h1 class="text-3xl font-mono glow-text">
        {mission?.title}
      </h1>

      <div class="text-cyan-400">
        Mission #{missionId}
      </div>

    </div>

    {#if bossVisible}

      <div class="mb-4">
        <BossBattle
          bossName="Corrupted Core"
          maxHealth={100}
      />
      </div>

    {/if}

    <div class="grid lg:grid-cols-3 gap-6">

      <div class="lg:col-span-2">

        <div class="bg-black/40 p-4 rounded-lg border border-cyan-500 mb-4">

          <p class="text-gray-300">
            {mission?.description}
          </p>

        </div>

        <CodeEditor
          bind:code={userCode}
          onExecute={handleExecute}
        />

        <div class="mt-4 p-3 bg-black/70 rounded border border-gray-700 font-mono text-sm">

          <span class="text-cyan-400">
            >
          </span>

          {output}

        </div>

      </div>

      <div>

        <AnimatedMentor message={mentorMsg} />

        <div class="mt-4 text-center text-xs text-gray-500">

          ⚡ HINT:
          Use print() to see output.

        </div>

      </div>

    </div>

  </div>

</div>

{/if}