<template>
  <NotificationToast
      :notifications="pendingNotifications"
      @remove="removeNotification"
  />
  <router-view />
</template>

<script setup>
import { onMounted } from 'vue';
import { useNotifications } from '@/composables/useNotifications';
import NotificationToast from '@/components/NotificationToast.vue';

const { pendingNotifications, startPolling, removeNotification } = useNotifications();

onMounted(() => {
  startPolling(10000);
});
</script>