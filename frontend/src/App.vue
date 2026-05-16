<template>
  <NotificationToast
      :notifications="pendingNotifications"
      @remove="removeNotification"
  />
  <router-view />
</template>

<script setup>
import { useNotifications } from '@/composables/useNotifications';
import NotificationToast from '@/components/NotificationToast.vue';

const { pendingNotifications, removeNotification } = useNotifications();
</script>