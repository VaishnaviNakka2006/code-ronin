<script lang="ts">
  import { onMount } from 'svelte';
  import { requireAuth } from '$lib/guards/authGuard';
  
  import { goto } from '$app/navigation';
  async function logout() {
    await supabase.auth.signOut();
    goto('/login');
  }

  async function testAIMission() {
    try {
      const {
        data: { session }
      } = await supabase.auth.getSession();


      const res = await fetch(
        `${import.meta.env.VITE_API_URL}/missions/generate-ai`,
        {
          method: "POST",
          headers: {
            Authorization: `Bearer ${session?.access_token}`
          }
        }
      );

      const data = await res.json();


      aiMission = data;
    } catch (err) {
      console.error(err);
    }
  }

  import { supabase } from '$lib/supabaseClient';

  import { user } from '$lib/stores/userStore';

  import RankBadge from '$lib/components/RankBadge.svelte';

  import StreakFortress from '$lib/components/StreakFortress.svelte';

  import NeonButton from '$lib/components/NeonButton.svelte';

  import { sound } from '$lib/utils/soundManager';

  import HolographicRankCard from '$lib/components/HolographicRankCard.svelte';

  let missions = [
    {
      id: 1,
      title: 'The Broken Airlock',
      difficulty: 'Easy',
      xpReward: 10
    },

    {
      id: 2,
      title: 'Loop the Security Scan',
      difficulty: 'Medium',
      xpReward: 20
    },

    {
      id: 3,
      title: 'Corrupted Core (BOSS)',
      difficulty: 'Hard',
      xpReward: 50,
      isBoss: true
    }
  ];

  let xpValue = 0;

  let aiMission = null;

  let maxXP = 100;

  let communityGoal = {
    current_total: 0,
    next_target: 100000,
    progress_percentage: 0,
    reward: ''
  };

  onMount(async () => {

    await requireAuth();

    console.log('USER STORE:', $user);

    xpValue = $user.xp;

    await loadCommunityGoal();
  });

  async function loadCommunityGoal() {

    try {

      const res = await fetch(
        `${import.meta.env.VITE_API_URL}/community/goal`
      );

      communityGoal = await res.json();

    } catch (err) {

      console.error(err);
    }
  }

  function handleLevelUp() {

    sound.play('levelup');

    alert('RANK UP!');
  }
</script>

<div class="min-h-screen p-8">

  <div class="max-w-6xl mx-auto">

    <div class="flex justify-between items-center mb-8">

      <h1 class="text-4xl font-mono glow-text">
        NEXUS: DASHBOARD
      </h1>

      <div class="flex gap-4">

        <RankBadge rank={$user.rank} />
        
        <div class="text-neon-cyan">
          🔥 Streak: {$user.streak} days
        </div>

        <a
          href="/achievements"
          class="px-4 py-2 rounded-lg border border-cyan-400 text-cyan-400 hover:bg-cyan-400 hover:text-black transition-all font-mono">🏆 ACHIEVEMENTS</a>
        
        <a
          href="/leaderboard"
          class="px-4 py-2 rounded-lg border border-cyan-400 text-cyan-400 hover:bg-cyan-400 hover:text-black transition-all font-mono"
        >
          🏆 LEADERBOARD
        </a>

        <a
          href="/friends"
          class="px-4 py-2 rounded-lg border border-pink-400 text-pink-400 hover:bg-pink-400 hover:text-black transition-all font-mono"
        >
          👥 FRIENDS
        </a>

        <a
          href="/dojo"
          class="px-4 py-2 rounded-lg border border-purple-400 text-purple-400 hover:bg-purple-400 hover:text-black transition-all font-mono"
        >
          🎯 INFINITE DOJO
        </a>

        <button
          on:click={logout}
          class="px-4 py-2 rounded-lg border border-red-400 text-red-400 hover:bg-red-400 hover:text-black transition-all font-mono"
        >
          🚪 LOGOUT
        </button>

        <button
          on:click={testAIMission}
          class="px-4 py-2 rounded-lg border border-green-400 text-green-400 hover:bg-green-400 hover:text-black transition-all font-mono"
        >
          🤖 TEST AI
        </button>

      </div>
    </div>

    <div class="grid md:grid-cols-3 gap-8">

      <!-- LEFT PANEL -->

      <div class="bg-transparent">

        <HolographicRankCard
          username={$user.username || 'Ronin'}
          rank={$user.rank}
          xp={$user.xp}
          streakDays={$user.streak}
        />

      </div>

      <!-- MISSIONS PANEL -->

      <div class="md:col-span-2 bg-neon-gray/40 p-4 rounded-lg cyber-border">

        <h2 class="text-xl mb-3">
          ACTIVE MISSIONS
        </h2>

        <div class="space-y-3">

          {#each missions as mission}

            <div class="flex justify-between items-center border-b border-neon-cyan/30 py-2">

              <div>

                <span class="font-bold">
                  {mission.title}
                </span>

                <span class="text-xs ml-2 text-gray-400">
                  {mission.difficulty}
                </span>

              </div>

              <NeonButton
                href={`/mission/${mission.id}`}
                small
              >
                DEPLOY
              </NeonButton>

            </div>

          {/each}

        </div>

      </div>

    </div>

    {#if aiMission}

    <div
      class="mt-8 bg-black/40 border border-green-500 rounded-xl p-6"
    >

      <h2
        class="text-2xl text-green-400 font-mono mb-4"
      >
        🤖 AI GENERATED MISSION
      </h2>

      <h3
        class="text-xl text-white mb-3"
      >
        {aiMission.title}
      </h3>

      <p
        class="text-gray-300 mb-4"
      >
        {aiMission.description}
      </p>

      <div
        class="text-green-300"
      >
        Difficulty:
        {aiMission.difficulty}
      </div>

      <div
        class="mt-4"
      >
        <strong>Code Stub:</strong>

        <pre
          class="mt-2 p-3 bg-black rounded overflow-auto"
        >
    {aiMission.code_stub}
        </pre>

      </div>

    </div>

    {/if}

    <!-- STREAK FORTRESS -->

    <div class="mt-8">

      <StreakFortress />

    </div>

    <!-- COMMUNITY GOAL -->

    <div
      class="mt-8 bg-black/40 border border-cyan-500 rounded-xl p-6"
    >

      <h2
        class="text-2xl text-cyan-300 font-mono mb-4"
      >
        🌍 COMMUNITY GOAL
      </h2>

      <div class="text-white mb-2">

        {communityGoal.current_total}
        /
        {communityGoal.next_target}
        XP

      </div>

      <div
        class="w-full h-5 bg-gray-900 rounded-full overflow-hidden mb-4"
      >

        <div
          class="h-full bg-cyan-400 transition-all duration-500"
          style={`width: ${communityGoal.progress_percentage}%`}
        ></div>

      </div>

      <div class="text-cyan-300">

        Progress:
        {communityGoal.progress_percentage.toFixed(2)}%

      </div>

      <div class="mt-3 text-yellow-400">

        Reward:
        {communityGoal.reward}

      </div>

    </div>
  
  </div>

</div>