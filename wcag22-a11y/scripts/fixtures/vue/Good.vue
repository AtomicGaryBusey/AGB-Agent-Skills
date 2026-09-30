<template>
  <div class="panel">
    <img :src="avatar" :alt="name">
    <button type="button" aria-label="Close" @click="close"><i class="fa fa-times" aria-hidden="true"></i></button>
    <button type="button" @click="toggle">Toggle</button>
    <label for="country">Country</label>
    <select id="country" v-model="country" autocomplete="country"><option>NZ</option></select>
    <h2>{{ title }}</h2>
    <h3>Sub</h3>
    <router-link to="/home">Home</router-link>
    <MyWidget v-bind="attrs" />
    <input v-model="zip" name="postcode" aria-label="Postcode" autocomplete="postal-code">
    <p v-html="body"></p>
  </div>
</template>

<script setup>
const props = defineProps({ avatar: String, name: String })
</script>

<style scoped>
.panel { color: #1f1f1f; background-color: #ffffff; }
.panel button:focus-visible { outline: 2px solid #1f1f1f; }
.close-btn { width: 24px; height: 24px; }
</style>
