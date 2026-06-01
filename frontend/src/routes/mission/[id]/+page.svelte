


<script lang="ts">
  import { page } from '$app/stores';
  import { goto } from '$app/navigation';
  import { onMount } from 'svelte';
  import { get } from 'svelte/store';

  import CodeEditor from '$lib/components/CodeEditor.svelte';
  import AnimatedMentor from '$lib/components/AnimatedMentor.svelte';
  import BossBattle from '$lib/components/BossBattle.svelte';

  import CinematicIntro
    from '$lib/components/cinematic/CinematicIntro.svelte';

  import MissionCompleteScreen
    from '$lib/components/cinematic/MissionCompleteScreen.svelte';

  import XPPopup from '$lib/components/XPPopup.svelte';

  import{
    showAchievementToast
  } from '$lib/utils/achievementToast';

  import{
    addNewlyUnlocked
  } from '$lib/stores/achievementStore'

  import { bossHealth }
    from '$lib/stores/gameStore';

  import {
    showCinematic,
    startMission
  } from '$lib/stores/missionStore';

  import {
    user,
    updateXP
  } from '$lib/stores/userStore';

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

  let mission: any = null;

  // COMPLETION SYSTEM
  let showCompletionScreen = false;

  let completionData: any = null;

  let nextMissionId: number | null = null;

  let rankUpAfter:
    { oldRank: string; newRank: string }
    | null = null;

  let xpPopups:
    { id: number; xp: number }[] = [];

  let nextPopupId = 0;

  function addXPPopup(xp: number) {

    const id = nextPopupId++;

    xpPopups = [
      ...xpPopups,
      { id, xp }
    ];
  }

  function removeXPPopup(id: number) {

    xpPopups = xpPopups.filter(
      (p) => p.id !== id
    );
  }

  async function loadMission() {

    try {

      const res = await fetch(
        `http://127.0.0.1:8000/missions/${missionId}`
      );

      mission = await res.json();

    } catch (err) {

      console.error(err);

      mission = {
        title: 'Mission Load Failed',
        description: 'Backend connection failed.',
        isBoss: false
      };

    }

  }

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
      const result = await submitMission(userCode, missionId);
      // Display detailed test output
      output = result.output;   // shows which tests passed/failed

      if (result.success) {

        const oldRank = $user.rank;

        updateXP($user.xp + result.xp_gained);

        const newRank = $user.rank;

        const rankChanged = oldRank !== newRank;

        // STEP 6B START

        if (result.xp_gained > 0) {

          addXPPopup(result.xp_gained);
        }

        if (
          result.new_achievements &&
          result.new_achievements.length
        ) {

          addNewlyUnlocked(
            result.new_achievements
          );

          for (
            const ach of result.new_achievements
          ) {

            showAchievementToast(
              ach.name,
              ach.xp_reward
            );

            if (ach.xp_reward > 0) {

              addXPPopup(
                ach.xp_reward
              );
            }
          }
        }

        // STEP 6B END

        if (bossVisible) {
          bossHealth.update(h => Math.max(0, h - 50));
          const currentHealth = get(bossHealth);
          if (currentHealth <= 0) {
            // Boss defeated – trigger completion screen
            completionData = {
              title: mission?.title || missionsData[missionId]?.title,
              xpGained: result.xp_gained,
              isBoss: true,
            };
            if (rankChanged) rankUpAfter = { oldRank, newRank };
            nextMissionId = missionId + 1 <= 3 ? missionId + 1 : null;
            showCompletionScreen = true;
            return;
          } else {
            mentorMsg = `Hit! Boss health: ${currentHealth}%`;
          }
        } else {
          // Normal mission complete
          completionData = {
            title: mission?.title || missionsData[missionId]?.title,
            xpGained: result.xp_gained,
            isBoss: false,
          };
          if (rankChanged) rankUpAfter = { oldRank, newRank };
          nextMissionId = missionId + 1 <= 3 ? missionId + 1 : null;
          showCompletionScreen = true;
          return;
        }
      } else {
        const ai = await getAIHint(result.output, userCode);
        mentorMsg = ai.hint || `Tests failed: ${result.tests_passed}/${result.total_tests} passed.`;
      }
    } catch (err) {
      console.error(err);
      output = 'Execution failed';
      mentorMsg = 'System error occurred.';
    }
  }

  async function handleContinue() {

    showCompletionScreen = false;

    if (nextMissionId) {

      await goto(
        `/mission/${nextMissionId}`
      );

      window.location.reload();

    } else {

      goto('/dashboard');
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
  }}
/>

{/if}

{#if cinematicDone && !showCompletionScreen}

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

{#if showCompletionScreen && completionData}

<MissionCompleteScreen
  missionTitle={
    completionData.title
  }

  xpGained={
    completionData.xpGained
  }

  isBoss={
    completionData.isBoss
  }

  rankUp={
    rankUpAfter
  }

  nextMissionId={
    nextMissionId
  }

  onContinue={
    handleContinue
  }
/>

{/if}

{#each xpPopups as popup}

  <XPPopup
    xp={popup.xp}
    onComplete={( ) =>
removeXPPopup(popup.id)}
  />

{/each}




async function handleExecute()


result.success