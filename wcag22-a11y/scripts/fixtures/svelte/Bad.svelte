<script>
  export let src;
  let name = '';
</script>

<img {src}>
<img src={src} alt="photo.jpg">
{#if name}
  <div on:click={() => (name = '')} class="alert">Hello {name}</div>
{/if}
<a href="/empty"></a>
<span lang="english">hello</span>
<div role="slider"></div>

<style>
  :focus { outline: 0; }
  body { width: 1024px; }
  p { line-height: 1.2 !important; }
  .muted { color: rgba(0, 0, 0, 0.3); background-color: white; font-size: 12px; }
</style>
