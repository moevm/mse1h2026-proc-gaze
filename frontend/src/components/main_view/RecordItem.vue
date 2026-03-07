<template>
  <div class="record-item" :class="{ expanded: props.record.expanded }">
    <div class="record-row main-row">
      <div class="info-group">
        <span class="info-item"><strong>UUID студента:</strong> {{ props.record.student_id }}</span>
        <span class="info-item"><strong>UUID записи:</strong> {{ props.record.recording_id }}</span>
        <span class="info-item">
          <strong>Статус:</strong>
          <span class="status-badge" :style="{ backgroundColor: STATUS_COLORS[record.status]}">
            {{ props.record.status }}
          </span>
        </span>
        <span v-if="showSuspicions" class="info-item">
          <strong>Подозрений:</strong> {{ props.record.count_suspicions }}
        </span>
      </div>

      <div class="actions-group">
        <button class="results-link" @click="goToResult">Просмотр результатов</button>
        <button class="expand-btn" @click="toggle">
          <span v-if="!props.record.expanded">▼</span>
          <span v-else>▲</span>
        </button>
      </div>
    </div>

    <div v-if="props.record.expanded" class="record-row expanded-row">
      <div class="info-group expanded-info">
        <span class="info-item"><strong>Видео с камеры:</strong> {{ props.record.camera_video_name }}</span>
        <span class="info-item"><strong>Видео с экрана:</strong> {{ props.record.screen_video_name }}</span>
        <span class="info-item"><strong>Дата создания:</strong> {{ props.record.created_date }}</span>
        <span class="info-item"><strong>Дата проверки:</strong> {{ props.record.processed_date || '—' }}</span>
      </div>
      <div class="actions-group"></div>
    </div>
  </div>
</template>

<script setup>
import { computed } from 'vue';
import router from "@/router/index.js";
import { STATUS_COLORS } from "@/constants/statusColor.js";

const props = defineProps({
  record: {
    type: Object,
    required: true,
  },
});


const emit = defineEmits(['toggleExpand']);

const showSuspicions = computed(() => {
  return props.record.status === 'DONE' && props.record.count_suspicions !== null;
});

const toggle = () => {
  emit('toggleExpand');
};

const goToResult = () => {
  router.push({
    name: 'ResultView',
    params: { id: props.record.recording_id }
  });
};

</script>

<style scoped>
.record-item {
  background-color: #f8fafc;
  border-radius: 16px;
  border: 1px solid #e2e8f0;
  overflow: hidden;
  transition: all 0.2s ease;
}

.record-item.expanded {
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.05);
}

.record-row {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 1rem 1.5rem;
  flex-wrap: wrap;
  gap: 1rem;
}

.main-row {
  background-color: #ffffff;
  border-bottom: 1px solid #e2e8f0;
}

.expanded-row {
  background-color: #f1f5f9;
  border-top: 1px dashed #cbd5e1;
}

.info-group {
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  gap: 1.5rem;
  flex: 1;
}

.info-item {
  font-size: 0.95rem;
  color: #2d3748;
  white-space: nowrap;
}

.status-badge {
  display: inline-block;
  padding: 0.25rem 0.75rem;
  border-radius: 20px;
  color: white;
  font-weight: 500;
  font-size: 0.85rem;
  text-transform: uppercase;
  margin-left: 0.25rem;
}

.actions-group {
  display: flex;
  align-items: center;
  gap: 1.5rem;
  flex-shrink: 0;
}

.results-link {
  color: #007bff;
  text-decoration: none;
  font-weight: 500;
  transition: color 0.2s;
  white-space: nowrap;
}

.results-link:hover {
  color: #0056b3;
  text-decoration: underline;
}

.expand-btn {
  background: none;
  border: none;
  font-size: 1.5rem;
  line-height: 1;
  cursor: pointer;
  color: #4a5568;
  padding: 0 0.5rem;
  transition: color 0.2s;
}

.expand-btn:hover {
  color: #1a202c;
}

@media (max-width: 768px) {
  .record-row {
    flex-direction: column;
    align-items: stretch;
  }

  .info-group {
    justify-content: space-between;
  }

  .actions-group {
    justify-content: flex-end;
  }

  .expanded-info {
    flex-direction: column;
    align-items: flex-start;
    gap: 0.5rem;
  }
}
</style>