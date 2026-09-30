<!-- Account dashboard: saved trips, reorderable. Source only; not built. -->
<template>
  <section aria-labelledby="dash-saved-heading">
    <h2 id="dash-saved-heading">Your saved trips</h2>
    <p>Drag a trip to change the order it appears in the app.</p>
    <ul class="saved-trips">
      <li
        v-for="(trip, index) in trips"
        :key="trip.id"
        class="saved-trips__item"
        draggable="true"
        @dragstart="onDragStart(index)"
        @dragover.prevent
        @drop="onDrop(index)"
      >
        <span class="saved-trips__grip" aria-hidden="true">&#x2807;</span>
        <a :href="`planner.html?from=${encodeURIComponent(trip.from)}&to=${encodeURIComponent(trip.to)}`">{{ trip.name }}</a>
      </li>
    </ul>
  </section>
</template>

<script>
export default {
  name: 'SavedTrips',
  props: { initialTrips: { type: Array, default: () => [] } },
  data() {
    return { trips: [...this.initialTrips], dragIndex: null };
  },
  methods: {
    onDragStart(index) {
      this.dragIndex = index;
    },
    onDrop(index) {
      if (this.dragIndex === null || this.dragIndex === index) return;
      const [moved] = this.trips.splice(this.dragIndex, 1);
      this.trips.splice(index, 0, moved);
      this.dragIndex = null;
      this.$emit('reorder', this.trips.map(t => t.id));
    }
  }
};
</script>

<style scoped>
.saved-trips { list-style: none; padding: 0; }
.saved-trips__item { display: flex; gap: 12px; align-items: center; padding: 10px 12px; border: 1px solid #d0d7de; border-radius: 4px; margin-bottom: 8px; cursor: grab; }
.saved-trips__grip { color: #6b7785; font-size: 1.2rem; }
</style>
