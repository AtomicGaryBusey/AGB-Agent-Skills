<script>
  export let src;
  export let alt = '';
  let name = '';
</script>

<img {src} {alt}>
{#if name}
  <div role="alert" class="alert">Hello {name}</div>
{/if}
<a href="/home">Home</a>
<a href="/x" {...$$restProps}></a>
<label for="nm">Name</label>
<input id="nm" bind:value={name} autocomplete="name">
<button on:click={() => (name = '')}>Clear</button>
<span lang="mi">kia ora</span>

<style>
  :focus-visible { outline: 2px solid #000; }
  main { max-width: 60rem; }
  .muted { color: #595959; background-color: white; }
</style>
