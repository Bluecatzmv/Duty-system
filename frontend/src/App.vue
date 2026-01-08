<script setup>
// App.vue 不需要任何逻辑，只负责渲染路由
import { NMessageProvider, NDialogProvider } from 'naive-ui'
</script>

<template>
  <n-message-provider>
    <n-dialog-provider>
      <router-view />
    </n-dialog-provider>
  </n-message-provider>
</template>

<style>
/* 这里的 style 必须是空的，或者直接删除，防止干扰 */
</style>
