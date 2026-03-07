<template>
  <div class="record-item" :class="{ expanded: record.expanded }">
    <div class="record-row main-row">
      <div class="info-group">
        <!-- up info-->
      </div>

      <div class="actions-group">
        <!--buttons-->
      </div>
    </div>

    <div v-if="props.record.expanded" class="record-row expanded-row">
      <div class="info-group expanded-info">
        <!--down info-->
      </div>
      <div class="actions-group"></div>
    </div>
  </div>
</template>

<script setup>

const props = defineProps({
  record: {
    type: Object,
    required: true,
  },
});

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

/* Адаптивность для узких экранов */
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