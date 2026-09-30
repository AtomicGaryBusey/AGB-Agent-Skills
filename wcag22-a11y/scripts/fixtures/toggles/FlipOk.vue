<template>
  <label class="flip">
    <input class="flip__in" type="checkbox" role="switch" v-model="on">
    <span class="flip__track" aria-hidden="true"><span class="flip__knob"></span></span>
    <span class="flip__text">{{ label }}</span>
  </label>
</template>

<script>
export default { props: ["label"], data() { return { on: false }; } };
</script>

<style scoped>
.flip__in { position: absolute; opacity: 0; width: 1px; height: 1px; }
.flip__track { display: inline-block; width: 40px; height: 22px; border-radius: 11px; background: #f1f1f1; border: 1px solid #6b7785; }
.flip__knob { display: block; width: 18px; height: 18px; border-radius: 50%; background: #fff; box-shadow: 0 0 0 1px #e2e2e2; }
.flip__in:checked + .flip__track { background: #25613f; border-color: #25613f; }
.flip__in:focus-visible + .flip__track { outline: 2px solid #1d4ed8; outline-offset: 2px; }
</style>
