<!-- Fare zone explainer used next to zone names in the fare calculator. Source only; not built. -->
<template>
  <span class="zone-info">
    <button
      type="button"
      class="zone-info__trigger"
      :aria-describedby="tipId"
      @mouseenter="open = true"
      @mouseleave="open = false"
      @focus="open = true"
      @blur="open = false"
    >
      Zone {{ zone }}
    </button>
    <span v-show="open" :id="tipId" role="tooltip" class="zone-info__tip">
      {{ description }}
    </span>
  </span>
</template>

<script>
export default {
  name: 'ZoneInfoTooltip',
  props: {
    zone: { type: [String, Number], required: true },
    description: { type: String, required: true }
  },
  data() {
    return { open: false };
  },
  computed: {
    tipId() {
      return `zone-tip-${this.zone}`;
    }
  }
};
</script>

<style scoped>
.zone-info { position: relative; display: inline-block; }
.zone-info__trigger { font: inherit; min-height: 32px; padding: 4px 10px; border: 1px solid #6b7785; border-radius: 4px; background: #fff; color: #1b2a3a; }
.zone-info__tip {
  position: absolute; top: calc(100% + 10px); left: 0; z-index: 10; width: 18rem;
  padding: 10px 12px; background: #1b2a3a; color: #fff; border-radius: 4px; font-size: .9rem;
}
</style>
