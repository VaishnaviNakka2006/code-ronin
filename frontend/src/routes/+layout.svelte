<script lang="ts">
  import '../app.css';
  import { onMount } from 'svelte';

  import AnimatedBackground
    from '$lib/components/AnimatedBackground.svelte';

  import Scanlines
    from '$lib/components/Scanlines.svelte';

  import { sound }
    from '$lib/utils/soundManager';

  import AchievementToast
    from '$lib/components/AchievementToast.svelte';

  import NotificationBell from '$lib/components/NotificationBell.svelte';

  onMount(() => {
    sound.init();
  });
</script>

<AnimatedBackground />

<Scanlines />

<AchievementToast />

<div class="fixed top-6 right-6 z-50">
  <NotificationBell />
</div>

<slot />