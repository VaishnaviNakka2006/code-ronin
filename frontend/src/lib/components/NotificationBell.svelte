<script lang="ts">
  import { onMount } from 'svelte';
  import { supabase } from '$lib/supabaseClient';

  let unreadCount = 0;
  let notifications: any[] = [];
  let showDropdown = false;

  console.log("API URL =", import.meta.env.VITE_API_URL);

  async function loadUnreadCount() {
    try {
      const {
        data: { session }
      } = await supabase.auth.getSession();

      const token = session?.access_token;

      const res = await fetch(
        `${import.meta.env.VITE_API_URL}/notifications/unread-count`,
        {
          headers: {
            Authorization: `Bearer ${token}`
          }
        }
      );

      const data = await res.json();

      unreadCount = data.count ?? 0;

    } catch (err) {
      console.error(err);
    }
  }

  async function loadNotifications() {
    try {

      const {
        data: { session }
      } = await supabase.auth.getSession();

      const token = session?.access_token;

      const res = await fetch(
        `${import.meta.env.VITE_API_URL}/notifications/`,
        {
          headers: {
            Authorization: `Bearer ${token}`
          }
        }
      );

      notifications = await res.json();

    } catch (err) {

      console.error(err);

    }
  }

  onMount(() => {

    loadUnreadCount();

    loadNotifications();

    const interval = setInterval(() => {

      loadUnreadCount();

      loadNotifications();

    }, 30000);

    return () => clearInterval(interval);

  });


</script>

<div
  class="relative cursor-pointer"
  on:click={() => showDropdown = !showDropdown}
>
  🔔

  {#if unreadCount > 0}
    <span
      class="absolute -top-2 -right-2 bg-red-500 text-white text-xs rounded-full px-2"
    >
      {unreadCount}
    </span>
  {/if}
</div>

{#if showDropdown}

  <div
    class="absolute right-0 mt-2 w-80 bg-black border border-cyan-500 rounded-lg p-4 z-50"
  >

    <h3 class="text-cyan-300 mb-3">
      Notifications
    </h3>

    {#if notifications.length === 0}

      <p class="text-gray-400">
        No notifications
      </p>

    {:else}

      {#each notifications as notification}

        <div
          class="border-b border-cyan-500/20 py-2 text-sm text-white"
        >
          {notification.content}
        </div>

      {/each}

    {/if}

  </div>

{/if}