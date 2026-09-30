<!-- Stop finder used on the app home screen. Source only; not built. -->
<template>
  <div class="stop-search">
    <label for="stop-search-input">Find a stop</label>
    <input id="stop-search-input" v-model="query" type="search" autocomplete="off" aria-describedby="stop-search-count" />
    <p id="stop-search-count" role="status">{{ countText }}</p>
    <ul class="stop-search__results">
      <li v-for="stop in results" :key="stop.id">
        <a :href="`map.html#${stop.id}`">{{ stop.name }}</a>
      </li>
    </ul>
  </div>
</template>

<script>
export default {
  name: 'StopSearch',
  props: { stops: { type: Array, default: () => [] } },
  data() {
    return { query: '' };
  },
  computed: {
    results() {
      const q = this.query.trim().toLowerCase();
      return q ? this.stops.filter(s => s.name.toLowerCase().includes(q)) : [];
    },
    countText() {
      if (!this.query.trim()) return '';
      const n = this.results.length;
      return n === 1 ? '1 stop found' : `${n} stops found`;
    }
  }
};
</script>

<style scoped>
.stop-search input { font: inherit; min-height: 44px; padding: 8px 10px; border: 1px solid #6b7785; border-radius: 4px; }
.stop-search__results a { display: inline-block; padding: 6px 0; }
</style>
