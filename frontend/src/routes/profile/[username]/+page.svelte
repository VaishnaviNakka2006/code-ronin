<script lang="ts">
  import { onMount } from 'svelte';

  export let data;

  let profile: any = null;

  let loading = true;

  async function loadProfile() {

    try {

      const username = window.location.pathname.split('/').pop();

      const res = await fetch(
        `http://127.0.0.1:8000/profile/${username}`
      );

      profile = await res.json();

    } catch (err) {

      console.error(err);

    } finally {

      loading = false;
    }
  }

  onMount(() => {

    loadProfile();
  });
</script>

<div class="min-h-screen bg-black p-8">

  <div class="max-w-4xl mx-auto">

    {#if loading}

      <div class="text-cyan-300 animate-pulse font-mono">
        Loading profile...
      </div>

    {:else if profile}

      <div
        class="bg-black/40 border border-cyan-500 rounded-2xl p-8"
      >

        <div class="flex justify-between items-center mb-8">

          <div>

            <h1 class="text-4xl glow-text font-mono">
              {profile.username}
            </h1>

            <p class="text-cyan-300 mt-2">
              NEXUS Operative
            </p>

          </div>

          <div
            class="px-4 py-2 border border-cyan-400 rounded-full text-cyan-300"
          >
            {profile.rank}
          </div>

        </div>

        <!-- STATS -->

        <div class="grid md:grid-cols-3 gap-6">

          <div
            class="bg-cyan-500/5 border border-cyan-500/20 rounded-xl p-6"
          >

            <h2 class="text-cyan-300 mb-2">
              XP
            </h2>

            <div class="text-3xl text-white font-bold">
              {profile.xp}
            </div>

          </div>

          <div
            class="bg-cyan-500/5 border border-cyan-500/20 rounded-xl p-6"
          >

            <h2 class="text-cyan-300 mb-2">
              Rank
            </h2>

            <div class="text-2xl text-white font-bold">
              {profile.rank}
            </div>

          </div>

          <div
            class="bg-cyan-500/5 border border-cyan-500/20 rounded-xl p-6"
          >

            <h2 class="text-cyan-300 mb-2">
              Streak
            </h2>

            <div class="text-2xl text-white font-bold">
              🔥 {profile.streak_days}
            </div>

          </div>

        </div>

        <!-- RECENT ACTIVITY -->

        <div class="mt-8">

          <h2 class="text-2xl text-cyan-300 mb-4">
            Recent Activity
          </h2>

          <div
            class="border border-cyan-500/20 rounded-xl p-6 text-gray-400"
          >
            Activity system coming in next phase...
          </div>

        </div>

      </div>

    {:else}

      <div class="text-red-400 font-mono">
        Profile not found
      </div>

    {/if}

  </div>

</div>