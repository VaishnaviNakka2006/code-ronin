<script lang="ts">
  export let href: string = '';
  export let small: boolean = false;
</script>

<a
  href={href}
  class={`inline-block bg-transparent border border-neon-cyan text-neon-cyan rounded hover:bg-neon-cyan hover:text-black transition-all ${
    small ? 'text-sm px-3 py-1' : 'px-4 py-2'
  }`}
>
  <slot />
</a>