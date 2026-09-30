<template>
  <div class="opts">
    <label class="tick">
      <input class="tick-native" type="checkbox" v-model="pickup">
      <span class="tick-box"></span>
      Collect from the depot
    </label>
    <label class="plain">
      <input type="checkbox" v-model="gift">
      Gift wrap
    </label>
    <label class="radio">
      <input class="radio-native" type="radio" name="speed" value="std">
      <span class="radio-dot"></span>
      Standard
    </label>
  </div>
</template>

<script>
export default { data() { return { pickup: false, gift: false }; } };
</script>

<style scoped>
.opts { background: #fafafa; }
.tick-native { clip: rect(0 0 0 0); clip-path: inset(50%); position: absolute; width: 1px; height: 1px; overflow: hidden; }
.tick-box { display: inline-block; width: 18px; height: 18px; border: 2px solid #6e6e6e; border-radius: 3px; }
/* only the checked state is pale; the default state above is fine */
.tick-native:checked ~ .tick-box { background: #eeeeee; border-color: #eeeeee; }
/* a native checkbox that is not hidden */
.plain input { margin-right: 6px; }
.radio-native { opacity: 0; position: absolute; }
.radio-native + .radio-dot { width: 16px; height: 16px; border-radius: 50%; background: #ffffff; border: 1px solid #e3e3e3; box-shadow: 0 0 0 2px #595959; }
</style>
