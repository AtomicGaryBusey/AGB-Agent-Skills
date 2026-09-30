<template>
  <div class="panel">
    <img :src="avatar">
    <button @click="close"><i class="fa fa-times"></i></button>
    <div @click.stop="toggle">Toggle</div>
    <select @change="$router.push($event.target.value)"><option>One</option></select>
    <h2></h2>
    <h4>Deep</h4>
    <router-link to="/home"><svg><use href="#home" /></svg></router-link>
    <span aria-hidden="true" tabindex="0">x</span>
    <input v-model="zip" name="postcode" aria-label="Postcode">
  </div>
</template>

<script setup>
import draggable from 'vuedraggable'
</script>

<style scoped lang="scss">
$muted: #b0b0b0;
.panel {
  color: $muted;
  background-color: #ffffff;
  button:focus { outline: none; }
  .close-btn { width: 16px; height: 16px; }
}
</style>
