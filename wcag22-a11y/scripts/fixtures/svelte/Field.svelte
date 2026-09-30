<script>
  let value = '';
</script>

<div class="panel">
  <label for="city">City</label>
  <input id="city" class="city-input" bind:value autocomplete="address-level2">
</div>

<style>
  .panel { background: #ffffff; }
  .city-input { border: 1px solid #dddddd; }
</style>
