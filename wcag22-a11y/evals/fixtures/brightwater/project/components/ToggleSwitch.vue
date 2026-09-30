<!-- Account settings switch (e.g. "Avoid stairs", "Large-print tickets"). Source only; not built. -->
<template>
  <label class="toggle">
    <input
      class="toggle__input"
      type="checkbox"
      role="switch"
      :checked="modelValue"
      @change="$emit('update:modelValue', $event.target.checked)"
    />
    <span class="toggle__track" aria-hidden="true">
      <span class="toggle__thumb"></span>
    </span>
    <span class="toggle__label">{{ label }}</span>
  </label>
</template>

<script>
export default {
  name: 'ToggleSwitch',
  props: {
    modelValue: { type: Boolean, default: false },
    label: { type: String, required: true }
  },
  emits: ['update:modelValue']
};
</script>

<style scoped>
.toggle { display: inline-flex; align-items: center; gap: 10px; min-height: 32px; cursor: pointer; }
.toggle__input { position: absolute; opacity: 0; width: 1px; height: 1px; }
.toggle__track {
  position: relative; width: 44px; height: 24px; border-radius: 12px;
  background: #f1f1f1; border: 1px solid #dddddd; transition: background .2s;
}
.toggle__thumb {
  position: absolute; top: 2px; left: 2px; width: 18px; height: 18px; border-radius: 50%;
  background: #ffffff; box-shadow: 0 0 0 1px #e2e2e2; transition: left .2s;
}
.toggle__input:checked + .toggle__track { background: #0b5cad; border-color: #0b5cad; }
.toggle__input:checked + .toggle__track .toggle__thumb { left: 22px; }
.toggle__input:focus-visible + .toggle__track { outline: 3px solid #0b5cad; outline-offset: 2px; }
</style>
