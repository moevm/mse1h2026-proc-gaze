<template>
  <div class="suspicious-item" @click="onClick">
    <div class="suspicious-time">{{ time }}</div>
    <div class="suspicious-duration">{{ formattedDuration }}</div>
    <div class="suspicious-description">{{ description }}</div>
  </div>
</template>

<script setup>
import { computed } from 'vue';

const props = defineProps({
  time: {
    type: String,
    required: true,
  },
  duration: {
    type: Number,
    required: true,
  },
  description: {
    type: String,
    required: true,
  },
});

const emit = defineEmits(['click']);

const formatDuration = (seconds) => {
  if (seconds === undefined || seconds === null) return '--:--';
  const mins = Math.floor(seconds / 60);
  const secs = Math.floor(seconds % 60);
  return `${mins.toString().padStart(2, '0')}:${secs.toString().padStart(2, '0')}`;
};

const formattedDuration = computed(() => formatDuration(props.duration));

const onClick = () => {
  const parts = props.time.split(':').map(Number);
  let totalSeconds = 0;
  if (parts.length === 3) {
    totalSeconds = parts[0] * 3600 + parts[1] * 60 + parts[2];
  } else if (parts.length === 2) {
    totalSeconds = parts[0] * 60 + parts[1];
  } else {
    totalSeconds = Number(props.time) || 0;
  }
  emit('click', totalSeconds);
};

</script>

<style scoped>
.suspicious-item {
  display: grid;
  grid-template-columns: 100px 100px 1fr;
  gap: 1rem;
  padding: 0.75rem 1rem;
  background-color: #f8fafc;
  border-radius: 12px;
  cursor: pointer;
  transition: background-color 0.2s;
  border: 1px solid #e2e8f0;
}

.suspicious-item:hover {
  background-color: #e6f0fa;
  border-color: #007bff;
}

.suspicious-time,
.suspicious-duration {
  font-family: monospace;
  font-weight: 500;
  color: #2d3748;
}

.suspicious-description {
  color: #4a5568;
}

@media (max-width: 768px) {
  .suspicious-item {
    grid-template-columns: 1fr;
    gap: 0.5rem;
  }
}
</style>