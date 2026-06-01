<script lang="ts">
  import { onMount } from 'svelte';

  let leaderboard: any[] = [];

  let loading = true;

  async function loadLeaderboard() {

    try {

      const res = await fetch(
        'http://127.0.0.1:8000/leaderboard/global'
      );

      leaderboard = await res.json();

    } catch (err) {

      console.error(err);

    } finally {

      loading = false;
    }
  }

  onMount(() => {

    loadLeaderboard();
  });
</script>

<div class="min-h-screen bg-neon-dark p-8">

  <div class="max-w-5xl mx-auto">

    <h1 class="text-4xl font-mono glow-text mb-8">
      GLOBAL LEADERBOARD
    </h1>

    {#if loading}

      <div class="text-neon-cyan animate-pulse font-mono">
        Loading leaderboard...
      </div>

    {:else}

      <div class="bg-black/40 rounded-xl border border-cyan-500 overflow-hidden">

        <table class="w-full text-left">

          <thead class="bg-cyan-500/10 text-cyan-300 font-mono">

            <tr>

              <th class="p-4">#</th>

              <th class="p-4">USERNAME</th>

              <th class="p-4">XP</th>

              <th class="p-4">RANK</th>

            </tr>

          </thead>

          <tbody>

            {#each leaderboard as player, index}

              <tr
                class="border-t border-cyan-500/20 hover:bg-cyan-500/5 transition-all"
              >

                <td class="p-4 font-mono">
                  {index + 1}
                </td>

                <td class="p-4 text-white">
                  {player.username}
                </td>

                <td class="p-4 text-neon-cyan font-bold">
                  {player.xp}
                </td>

                <td class="p-4">

                  <span
                    class="px-3 py-1 rounded-full border border-cyan-400 text-cyan-300 text-sm"
                  >
                    {player.rank}
                  </span>

                </td>

              </tr>

            {/each}

          </tbody>

        </table>

      </div>

    {/if}

  </div>

</div>