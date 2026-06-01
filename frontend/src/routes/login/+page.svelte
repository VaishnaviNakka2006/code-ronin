<script lang="ts">
  import { signInWithGoogle, signInWithDiscord } from '$lib/stores/authStore';
  import { onMount } from 'svelte';
  import { supabase } from '$lib/supabaseClient';

  onMount(async () => {

    const {
      data: { session }
    } = await supabase.auth.getSession();

    if (session) {
      window.location.href = '/dashboard';
    }

  });
</script>

<div class="min-h-screen flex items-center justify-center bg-neon-dark">
  <div class="bg-neon-gray/40 p-8 rounded-lg cyber-border text-center">
    <h1 class="text-3xl font-mono glow-text mb-6">
      AUTHENTICATE
    </h1>

    <div class="space-y-4 flex flex-col">
      <button
        on:click={signInWithGoogle}
        class="px-6 py-3 border border-neon-cyan text-neon-cyan rounded hover:bg-neon-cyan hover:text-black transition-all"
      >
        🔐 Sign in with Google
      </button>

      <button
        on:click={signInWithDiscord}
        class="px-6 py-3 border border-neon-magenta text-neon-magenta rounded hover:bg-neon-magenta hover:text-black transition-all"
      >
        🎮 Sign in with Discord
      </button>
    </div>
  </div>
</div>