<script setup>
import { useRoute } from 'vue-router'

const route = useRoute()

const navItems = [
  { path: '/', label: '概览' },
  { path: '/products', label: '产品' },
  { path: '/reports', label: '报告' },
]
</script>

<template>
  <div class="app-shell">
    <nav class="top-nav">
      <router-link to="/" class="brand">Scope<span>Lens</span></router-link>
      <div class="nav-links">
        <router-link
          v-for="item in navItems"
          :key="item.path"
          :to="item.path"
          :class="{ active: route.path === item.path }"
        >
          {{ item.label }}
        </router-link>
      </div>
    </nav>
    <main class="main">
      <router-view />
    </main>
  </div>
</template>

<style scoped>
.app-shell { min-height:100vh; background:var(--bg); }

.top-nav {
  background:#fff; border-bottom:1px solid var(--border);
  padding:0 32px; height:56px;
  display:flex; align-items:center; justify-content:space-between;
  position:sticky; top:0; z-index:100;
}
.brand {
  font-size:18px; font-weight:700; color:var(--text);
  letter-spacing:-.5px; text-decoration:none;
}
.brand span { color:var(--accent); }

.nav-links { display:flex; gap:2px; }
.nav-links a {
  text-decoration:none; color:var(--text-secondary);
  padding:6px 16px; border-radius:8px; font-size:13px; font-weight:500;
  transition:all .15s;
}
.nav-links a:hover { color:var(--text); background:var(--accent-light); }
.nav-links a.active,
.nav-links a.router-link-exact-active {
  color:var(--accent); background:var(--accent-light); font-weight:600;
}

.main { padding:28px 32px; max-width:1200px; margin:0 auto; }
</style>
