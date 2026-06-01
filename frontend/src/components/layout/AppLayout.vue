<template>
  <div class="flex h-screen overflow-hidden">
    <SideNav />
    <main class="flex-1 overflow-auto bg-[var(--color-bg)]">
      <router-view v-slot="{ Component }">
        <transition name="fade" mode="out-in">
          <component :is="Component" />
        </transition>
      </router-view>
    </main>
  </div>
</template>

<script setup lang="ts">
import SideNav from './SideNav.vue'
</script>
