<script lang="ts">
  import { onMount } from 'svelte';
  import { requireAuth } from '$lib/guards/authGuard';

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

  let maxXP = 100;

  onMount(async () => {

    await requireAuth();

    xpValue = $user.xp;
  });

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

        <a
          href="/achievements"
          class="px-4 py-2 rounded-lg border border-cyan-400 text-cyan-400 hover:bg-cyan-400 hover:text-black transition-all font-mono">🏆 ACHIEVEMENTS</a>

        <div class="text-neon-cyan">
          🔥 Streak: {$user.streak} days
        </div>

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

    <!-- STREAK FORTRESS -->

    <div class="mt-8">

      <StreakFortress />

    </div>

  </div>

</div>