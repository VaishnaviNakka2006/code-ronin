<script lang="ts">
  import { onMount } from 'svelte';
  import loader from '@monaco-editor/loader';

  export let code: string;
  export let language = 'python';
  export let onExecute: () => void;

  let editorContainer: HTMLDivElement;
  let editor: any;

  onMount(async () => {
    const monaco = await loader.init();
    editor = monaco.editor.create(editorContainer, {
      value: code,
      language: language,
      theme: 'vs-dark',
      fontSize: 14,
      fontFamily: 'Fira Code, monospace',
      minimap: { enabled: false },
      automaticLayout: true,
      lineNumbers: 'on',
      glyphMargin: false,
      folding: false,
      scrollBeyondLastLine: false,
    });
    editor.onDidChangeModelContent(() => {
      code = editor.getValue();
    });
  });

  function runCode() {
    onExecute();
  }
</script>

<div class="relative w-full h-full">
  <div bind:this={editorContainer} class="w-full h-[400px] border border-neon-cyan rounded"></div>
  <button
    on:click={runCode}
    class="mt-4 px-6 py-2 bg-neon-cyan text-black font-bold rounded-md hover:shadow-[0_0_20px_#00f3ff] transition-all"
  >
    ⚡ EXECUTE ⚡
  </button>
</div>