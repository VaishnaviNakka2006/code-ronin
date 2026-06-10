<script lang="ts">
  import { onMount } from 'svelte';
  import { generateAIMission, submitAIMission } from '$lib/api/aiMissions';
  import CodeEditor from '$lib/components/CodeEditor.svelte';
  import AnimatedMentor from '$lib/components/AnimatedMentor.svelte';
  import { user, updateXP } from '$lib/stores/userStore';
  import { toast } from 'svelte-sonner';
  import { supabase } from '$lib/supabaseClient';

  let difficulty = 'easy';
  let topic = '';
  let loading = false;
  let mission: any = null;
  let userCode = '';
  let resultOutput = '';
  let mentorMsg = 'Generate an AI mission to start.';
  let adaptive = false;

  let recommendations: {
    topic: string;
    proficiency: number;
  }[] = [];

  async function generate() {
    loading = true;
    try {
      mission = await generateAIMission({
        difficulty,
        topic,
        adaptive
      });
      userCode = mission.code_stub || '';
      mentorMsg = `New mission: ${mission.title}. Write your code and submit.`;
      resultOutput = '';
    } catch (err) {
      toast.error('Failed to generate mission');
    } finally {
      loading = false;
    }
  }

  async function submit() {
    console.log("SUBMIT CLICKED");
    if (!mission) return;

    console.log("MISSION:", mission);
    console.log("CODE:", userCode);

    loading = true;
    try {
      const result = await submitAIMission(mission, userCode);
      resultOutput = result.output;
      if (result.success) {
        // Update XP in store and show popup
        updateXP($user.xp + result.xp_gained);
        toast.success(`+${result.xp_gained} XP!`);
        mentorMsg = `Mission complete! +${result.xp_gained} XP. Generate another mission.`;
      } else {
        mentorMsg = `Tests failed: ${result.tests_passed}/${result.total_tests} passed. Try again.`;
        toast.error('Mission failed');
      }
    } catch (err) {
      toast.error('Submission error');
    } finally {
      loading = false;
    }
  }

  async function loadRecommendations() {
    try {
      const session = await supabase.auth.getSession();
      const API_BASE =
        import.meta.env.VITE_API_URL ||
        'https://code-ronin.onrender.com';
      const token =
        session.data.session?.access_token;

      const res = await fetch(
        `${API_BASE}/user/recommendations`,
        {
          headers: {
            Authorization: `Bearer ${token}`
          }
        }
      );

      if (!res.ok) {
        throw new Error(
          'Failed to load recommendations'
        );
      }

      const data = await res.json();

      recommendations =
        data.recommendations || [];
    } catch (err) {
      console.error(
        'Failed to load recommendations',
        err
      );
    }
  }

  function useRecommendation(topicName: string) {
    topic = topicName;
    adaptive = true;
    generate();
  }

  onMount(async () => {
    await loadRecommendations();
  });
</script>

<div class="min-h-screen bg-neon-dark p-8">
  <div class="max-w-6xl mx-auto">
    <h1 class="text-4xl font-mono glow-text mb-6">⚡ INFINITE DOJO ⚡</h1>
    {#if recommendations.length > 0}
      <div class="mb-6 p-4 bg-black/40 rounded-lg border border-neon-cyan">
        <h3 class="text-neon-cyan font-mono mb-2">
          📈 RECOMMENDED FOR YOU
        </h3>

        <div class="flex flex-wrap gap-2">
          {#each recommendations as rec}
            <button
              on:click={() => useRecommendation(rec.topic)}
              class="px-3 py-1 bg-black/60 border border-neon-magenta rounded-full text-sm hover:bg-neon-magenta/20"
            >
              {rec.topic}
              ({Math.round(rec.proficiency * 100)}%)
            </button>
          {/each}
        </div>
      </div>
    {/if}

    <!-- Mission generation controls -->
    <div class="flex gap-4 items-end mb-8">
      <div>
        <label class="block text-sm text-neon-cyan">Difficulty</label>
        <select
          bind:value={difficulty}
          disabled={adaptive} class="bg-black/60 border border-neon-cyan rounded p-2">
          <option value="easy">Easy</option>
          <option value="medium">Medium</option>
          <option value="hard">Hard</option>
        </select>
      </div>
      <div class="flex-1">
        <label class="block text-sm text-neon-cyan">Topic (optional)</label>
        <input
          bind:value={topic}
          disabled={adaptive} placeholder="e.g., loops, recursion, lists" class="w-full bg-black/60 border border-neon-cyan rounded p-2" />
      </div>

      <div>
        <label class="flex items-center gap-2 text-sm text-neon-cyan">
          <input
            type="checkbox"
            bind:checked={adaptive}
          />
          🧠 Adaptive Mode
        </label>
      </div>

      {#if adaptive}
        <p class="text-xs text-gray-400 mt-1">
          Adaptive mode automatically chooses topic and difficulty based on your weakest skill.
        </p>
      {/if}

      <button on:click={generate} disabled={loading} class="px-4 py-2 bg-neon-cyan text-black font-bold rounded hover:shadow-[0_0_20px_#00f3ff]">
        {loading ? 'GENERATING...' : '🎲 GENERATE MISSION'}
      </button>
    </div>

    {#if mission}
      <div class="grid lg:grid-cols-3 gap-6">
        <div class="lg:col-span-2">
          <div class="bg-black/40 p-4 rounded-lg border border-neon-cyan mb-4">
            <h2 class="text-2xl font-mono text-neon-cyan">{mission.title}</h2>
            <p class="text-gray-300 mt-2">{mission.description}</p>
          </div>
          <CodeEditor bind:code={userCode} onExecute={submit} />
          <div class="mt-4 p-3 bg-black/70 rounded border border-gray-700 font-mono text-sm">
            <span class="text-neon-cyan">> </span> {resultOutput || 'Ready'}
          </div>
        </div>
        <div>
          <AnimatedMentor message={mentorMsg} />
          <button on:click={submit} disabled={loading} class="w-full mt-4 px-4 py-2 bg-neon-magenta text-black font-bold rounded hover:shadow-[0_0_20px_#ff00e5]">
            ⚡ SUBMIT SOLUTION ⚡
          </button>
        </div>
      </div>
    {:else}
      <div class="text-center text-gray-400 py-20">
        Click "Generate Mission" to start your training.
      </div>
    {/if}
  </div>
</div>