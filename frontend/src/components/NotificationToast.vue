<template>
  <Teleport to="body">
    <div class="notification-container">
      <TransitionGroup name="notif">
        <div
            v-for="notif in notifications"
            :key="notif.notification_id"
            class="notification-item"
        >
          <span>Запись {{ notif.recording_id }} обработана</span>
          <button class="close-btn" @click="$emit('remove', notif.notification_id)">✕</button>
        </div>
      </TransitionGroup>
    </div>
  </Teleport>
</template>

<script setup>
defineProps({
  notifications: {
    type: Array,
    required: true,
  },
});
defineEmits(['remove']);
</script>

<style scoped>
.notification-container {
  position: fixed;
  top: 1rem;
  right: 1rem;
  z-index: 10000;
  display: flex;
  flex-direction: column;
  gap: 0.75rem;
  width: 320px;
  max-width: 100%;
  pointer-events: none;
}

.notification-item {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 0.75rem 1rem;
  background: #ffffff;
  border-radius: 12px;
  box-shadow: 0 4px 15px rgba(0, 0, 0, 0.15);
  border-left: 4px solid #28a745;
  pointer-events: auto;
  font-size: 0.95rem;
  color: #2d3748;
}

.close-btn {
  background: none;
  border: none;
  font-size: 1.2rem;
  cursor: pointer;
  color: #718096;
  padding: 0 0.25rem;
  line-height: 1;
}

.close-btn:hover {
  color: #1a202c;
}

.notif-enter-active,
.notif-leave-active {
  transition: all 0.3s ease;
}
.notif-enter-from {
  opacity: 0;
  transform: translateX(30px);
}
.notif-leave-to {
  opacity: 0;
  transform: translateX(30px);
}
</style>