<script lang="ts">
  import { onMount } from 'svelte';

  import { supabase } from '$lib/supabaseClient';

  let requests: any[] = [];

  let friendsLeaderboard: any[] = [];

  let username = '';

  let loading = true;

  let searchQuery = '';

  let searchResults: any[] = [];

  let searching = false;

  function isOnline(lastActive: string) {

    if (!lastActive) return false;

    const last = new Date(lastActive).getTime();

    const now = Date.now();

    const diffMinutes = (now - last) / (1000 * 60);

    return diffMinutes <= 5;
  }

  async function loadRequests() {

    try {

      const {
        data: { session }
      } = await supabase.auth.getSession();

      const token = session?.access_token;

      const res = await fetch(
        '${import.meta.env.VITE_API_URL}/friends/requests',
        {
          headers: {
            Authorization: `Bearer ${token}`
          }
        }
      );

      requests = await res.json();

    } catch (err) {

      console.error(err);
    }
  }

  async function searchUsers() {

    if (!searchQuery.trim()) {

      searchResults = [];

      return;
    }

    searching = true;

    try {

        const {
          data: { session }
        } = await supabase.auth.getSession();

        const token = session?.access_token;

        const res = await fetch(
          `${import.meta.env.VITE_API_URL}/friends/search?q=${encodeURIComponent(searchQuery)}`,
          {
            headers: {
              Authorization: `Bearer ${token}`
            }
          }
        );

        searchResults = await res.json();

    } catch (err) {

        console.error(err);

    } finally {

        searching = false;
    }
  }

  async function loadFriendsLeaderboard() {

    try {

      const {
        data: { session }
      } = await supabase.auth.getSession();

      const token = session?.access_token;

      const res = await fetch(
        '${import.meta.env.VITE_API_URL}/leaderboard/friends',
        {
          headers: {
            Authorization: `Bearer ${token}`
          }
        }
      );

      friendsLeaderboard = await res.json();

    } catch (err) {

      console.error(err);
    }
  }

  async function sendFriendRequest(targetUserId: string) {

    try {

      const {
        data: { session }
      } = await supabase.auth.getSession();

      const token = session?.access_token;

      const res = await fetch(
        `${import.meta.env.VITE_API_URL}/friends/request/${targetUserId}`,
        {
          method: 'POST',
          headers: {
            Authorization: `Bearer ${token}`
          }
        }
      );

      const data = await res.json();

      alert(data.message);

    } catch (err) {

      console.error(err);

      alert('Failed to send friend request');
    }
  }

  async function acceptRequest(id: number) {

    try {

      const {
        data: { session }
      } = await supabase.auth.getSession();

      const token = session?.access_token;

      await fetch(
        `${import.meta.env.VITE_API_URL}/friends/accept/${id}`,
        {
          method: 'POST',
          headers: {
            Authorization: `Bearer ${token}`
          }
        }
      );

      await loadRequests();

      await loadFriendsLeaderboard();

    } catch (err) {

      console.error(err);
    }
  }

  onMount(async () => {

    await loadRequests();

    await loadFriendsLeaderboard();

    loading = false;
  });
</script>

<div class="min-h-screen bg-black p-8">

  <div class="max-w-5xl mx-auto">

    <h1 class="text-4xl font-mono glow-text mb-8">
      FRIENDS NETWORK
    </h1>

    <!-- ADD FRIEND -->

    <div class="bg-black/40 border border-cyan-500 rounded-xl p-6 mb-8">

      <h2 class="text-xl text-cyan-300 mb-4">
        Add Friend
      </h2>

      <div class="flex gap-4">

        <input
          bind:value={username}
          placeholder="Enter username..."
          class="flex-1 bg-black border border-cyan-500 rounded-lg px-4 py-2 text-white outline-none"
        />

        <button
          on:click={sendFriendRequest}
          class="px-6 py-2 bg-cyan-500/20 border border-cyan-400 rounded-lg text-cyan-300 hover:bg-cyan-500/30 transition-all"
        >
          SEND
        </button>

      </div>

    </div>

    <!-- SEARCH USERS -->

    <div class="bg-black/40 border border-cyan-500 rounded-xl p-6 mb-8">

      <h2 class="text-xl text-cyan-300 mb-4">
        Search Players
      </h2>

      <input
        bind:value={searchQuery}
        on:input={searchUsers}
        placeholder="Find players by username..."
        class="w-full bg-black border border-cyan-500 rounded-lg px-4 py-2 text-white outline-none mb-4"
      />

      {#if searching}

        <div class="text-cyan-300 animate-pulse">
          Searching...
        </div>

      {/if}

      {#if searchResults.length > 0}

        <div class="space-y-3">

          {#each searchResults as player}

            <div
              class="flex justify-between items-center border border-cyan-500/20 rounded-lg p-4"
            >

              <div>

                <div class="text-white font-bold">
                  {player.username}
                </div>

                <div class="text-cyan-300 text-sm">
                  {player.xp} XP • {player.rank}
                </div>

              </div>

              <button
                on:click={() => sendFriendRequest(player.id)}
                class="px-4 py-2 border border-cyan-400 text-cyan-300 rounded-lg hover:bg-cyan-500/20 transition-all"
              >
                ADD FRIEND
              </button>

            </div>

          {/each}

        </div>

      {/if}

    </div>

    <!-- FRIEND REQUESTS -->

    <div class="bg-black/40 border border-cyan-500 rounded-xl p-6 mb-8">

      <h2 class="text-xl text-cyan-300 mb-4">
        Incoming Requests
      </h2>

      {#if requests.length === 0}

        <p class="text-gray-400">
          No pending requests
        </p>

      {:else}

        <div class="space-y-4">

          {#each requests as req}

            <div
              class="flex justify-between items-center border border-cyan-500/30 rounded-lg p-4"
            >

              <div class="text-white">
                Friend Request
              </div>

              <button
                on:click={() => acceptRequest(req.id)}
                class="px-4 py-2 border border-green-400 text-green-300 rounded-lg hover:bg-green-500/20 transition-all"
              >
                ACCEPT
              </button>

            </div>

          {/each}

        </div>

      {/if}

    </div>

    <!-- FRIENDS LEADERBOARD -->

    <div class="bg-black/40 border border-cyan-500 rounded-xl p-6">

      <h2 class="text-xl text-cyan-300 mb-4">
        Friends Leaderboard
      </h2>

      {#if loading}

        <div class="text-cyan-300 animate-pulse">
          Loading...
        </div>

      {:else if friendsLeaderboard.length === 0}

        <p class="text-gray-400">
          No friends added yet
        </p>

      {:else}

        <div class="space-y-3">

          {#each friendsLeaderboard as friend, index}

            <div
              class="flex justify-between items-center border border-cyan-500/20 rounded-lg p-4 hover:bg-cyan-500/5 transition-all"
            >

              <div class="flex gap-4 items-center">

                <span class="text-cyan-300 font-mono">
                  #{index + 1}
                </span>

                <span
                  class={`w-3 h-3 rounded-full ${
                    isOnline(friend.last_active)
                      ? 'bg-green-500'
                      : 'bg-gray-500'
                  }`}
                ></span>

                <span class="text-white">
                  {friend.username}
                </span>

              </div>

              <div class="flex gap-6 items-center">

                <span class="text-cyan-300">
                  {friend.xp} XP
                </span>

                <span
                  class="px-3 py-1 border border-cyan-400 rounded-full text-cyan-300 text-sm"
                >
                  {friend.rank}
                </span>

              </div>

            </div>

          {/each}

        </div>

      {/if}

    </div>

  </div>

</div>