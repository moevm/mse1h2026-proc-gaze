<template>
  <div class="main-view">
    <div class="content-card">
      <div class="upload-button-container">
        <button class="upload-btn" @click="goToUpload">
          + Загрузить видео
        </button>
      </div>

      <h2 class="list-title">Загруженные видео</h2>

      <div class="records-container" v-if="records.length > 0">
        <!--RecordItem-->
      </div>

      <div v-else class="empty-placeholder">
        Пока нет загруженных видео
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref } from 'vue';
import router from "@/router/index.js";

const records = ref([]);

const goToUpload = () => {
  router.push({ name: 'UploadPlayerView' });
};

</script>

<style scoped>
.main-view {
  min-height: 100vh;
  background-color: #e6f0fa;
  display: flex;
  align-items: flex-start;
  justify-content: center;
  padding: 2rem;
}

.content-card {
  max-width: 1200px;
  width: 100%;
  background-color: #ffffff;
  border-radius: 24px;
  box-shadow: 0 8px 30px rgba(0, 0, 0, 0.1);
  padding: 2rem;
  display: flex;
  flex-direction: column;
  max-height: calc(100vh - 4rem);
}

.upload-button-container {
  text-align: center;
  margin-bottom: 1.5rem;
}

.upload-btn {
  display: inline-block;
  padding: 0.75rem 2rem;
  font-size: 1.2rem;
  background-color: #007bff;
  color: white;
  border: none;
  border-radius: 40px;
  cursor: pointer;
  text-decoration: none;
  transition: background-color 0.2s, transform 0.1s;
  box-shadow: 0 2px 8px rgba(0, 123, 255, 0.3);
}

.upload-btn:hover {
  background-color: #0056b3;
  transform: scale(1.02);
}

.list-title {
  text-align: center;
  margin-bottom: 1.5rem;
  color: #1a2b3c;
  font-size: 1.8rem;
  font-weight: 500;
}

.records-container {
  flex: 1;
  overflow-y: auto;
  padding-right: 0.5rem;
  display: flex;
  flex-direction: column;
  gap: 1rem;
}

.empty-placeholder {
  flex: 1;
  display: flex;
  align-items: center;
  justify-content: center;
  color: #7f8c8d;
  font-size: 1.2rem;
  text-align: center;
  padding: 2rem;
}
</style>