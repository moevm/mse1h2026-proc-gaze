<template>
  <div class="result-view">
    <div class="back-button" @click="goToMain">Вернуться на главную</div>

    <div class="content-card">
      <h1 class="title">Результаты проверки</h1>

      <div class="blocks">
        <div class="block">
          <h3 class="block-label">Видео с камеры</h3>
          <VideoPlayer
              v-if="webcamSrc"
              ref="webcamPlayer"
              :src="webcamSrc"
              @play="onPlay('webcam')"
              @pause="onPause('webcam')"
              @seek="handleWebcamSeek"
              @duration="handleWebcamDuration"
              @timeupdate="handleWebcamTimeUpdate"
          />
          <div v-else class="loading-placeholder">Загрузка видео...</div>
        </div>

        <div class="block">
          <h3 class="block-label">Видео с экрана</h3>
          <VideoPlayer
              v-if="screenSrc"
              ref="screenPlayer"
              :src="screenSrc"
              @play="onPlay('screen')"
              @pause="onPause('screen')"
              @seek="handleScreenSeek"
              @duration="handleScreenDuration"
              @timeupdate="handleScreenTimeUpdate"
          />
          <div v-else class="loading-placeholder">Загрузка видео...</div>
        </div>
      </div>

      <div class="suspicious-section">
        <h3 class="suspicious-title">Подозрительные моменты</h3>

        <div class="suspicious-content">
          <div class="suspicious-list-wrapper">
            <div v-if="suspiciousList.length === 0" class="empty-suspicious">
              Нет подозрительных моментов
            </div>
            <div v-else class="suspicious-list">
              <SuspiciousItem
                  v-for="item in suspiciousList"
                  :key="item.sus_id"
                  :time="item.time"
                  :duration="item.duration"
                  :description="item.description"
                  @click="seekTo"
              />
            </div>
          </div>

          <button class="download-button" @click="downloadResult">
            Загрузить результат
          </button>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted, onBeforeUnmount } from 'vue';
import { useRoute, useRouter } from 'vue-router';
import VideoPlayer from '@/components/VideoPlayer.vue';
import SuspiciousItem from '@/components/result_view/SuspiciousItem.vue';
import { recordingApi } from '@/api';

const route = useRoute();
const router = useRouter();

const recordingId = route.params.recording_id;

const webcamSrc = ref(null);
const screenSrc = ref(null);
const webcamPlayer = ref(null);
const screenPlayer = ref(null);

const webcamDuration = ref(null);
const screenDuration = ref(null);
const webcamCurrentTime = ref(0);
const screenCurrentTime = ref(0);
const webcamIsPlaying = ref(false);
const screenIsPlaying = ref(false);

const isSyncing = ref(false);
const webcamProgrammaticSeek = ref(false);
const screenProgrammaticSeek = ref(false);

const suspiciousList = ref([]);

const EPS = 0.1;


onMounted(async () => {
  if (!recordingId) {
    goToMain();
    return;
  }

  try {
    const [webcamBlob, screenBlob] = await Promise.all([
      recordingApi.getWebcamVideo(recordingId),
      recordingApi.getScreenVideo(recordingId),
    ]);
    webcamSrc.value = URL.createObjectURL(webcamBlob);
    screenSrc.value = URL.createObjectURL(screenBlob);

    const suspicious = await recordingApi.getSuspicious(recordingId);
    suspiciousList.value = suspicious;
  } catch (error) {
    console.error('Ошибка загрузки данных:', error);
  }
});


onBeforeUnmount(() => {
  if (webcamSrc.value) URL.revokeObjectURL(webcamSrc.value);
  if (screenSrc.value) URL.revokeObjectURL(screenSrc.value);
});


const goToMain = () => {
  router.push({ name: 'MainView' });
};


const handleWebcamDuration = (dur) => { webcamDuration.value = dur; };
const handleWebcamTimeUpdate = (time) => { webcamCurrentTime.value = time; };
const handleScreenDuration = (dur) => { screenDuration.value = dur; };
const handleScreenTimeUpdate = (time) => { screenCurrentTime.value = time; };

const handleWebcamSeek = (time) => {
  if (webcamProgrammaticSeek.value) {
    webcamProgrammaticSeek.value = false;
    return;
  }
  if (screenPlayer.value && screenDuration.value !== null) {
    screenProgrammaticSeek.value = true;
    const newTime = Math.min(time, screenDuration.value);
    screenPlayer.value.setCurrentTime(newTime);
    if (screenIsPlaying.value) {
      isSyncing.value = true;
      screenPlayer.value.pause();
      isSyncing.value = false;
    }
  }
};


const handleScreenSeek = (time) => {
  if (screenProgrammaticSeek.value) {
    screenProgrammaticSeek.value = false;
    return;
  }
  if (webcamPlayer.value && webcamDuration.value !== null) {
    webcamProgrammaticSeek.value = true;
    const newTime = Math.min(time, webcamDuration.value);
    webcamPlayer.value.setCurrentTime(newTime);
    if (webcamIsPlaying.value) {
      isSyncing.value = true;
      webcamPlayer.value.pause();
      isSyncing.value = false;
    }
  }
};


const onPlay = (source) => {
  if (isSyncing.value) return;

  if (source === 'webcam') {
    webcamIsPlaying.value = true;
    if (
        screenPlayer.value &&
        screenDuration.value !== null &&
        !screenIsPlaying.value
    ) {
      const isScreenAtEnd = screenCurrentTime.value >= screenDuration.value - EPS;
      if (!isScreenAtEnd) {
        isSyncing.value = true;
        screenPlayer.value.play();
        isSyncing.value = false;
      }
    }
  } else {
    screenIsPlaying.value = true;
    if (
        webcamPlayer.value &&
        webcamDuration.value !== null &&
        !webcamIsPlaying.value
    ) {
      const isWebcamAtEnd = webcamCurrentTime.value >= webcamDuration.value - EPS;
      if (!isWebcamAtEnd) {
        isSyncing.value = true;
        webcamPlayer.value.play();
        isSyncing.value = false;
      }
    }
  }
};


const onPause = (source) => {
  if (isSyncing.value) return;

  if (source === 'webcam') {
    webcamIsPlaying.value = false;
    if (screenPlayer.value && screenIsPlaying.value) {
      isSyncing.value = true;
      screenPlayer.value.pause();
      isSyncing.value = false;
    }
  } else {
    screenIsPlaying.value = false;
    if (webcamPlayer.value && webcamIsPlaying.value) {
      isSyncing.value = true;
      webcamPlayer.value.pause();
      isSyncing.value = false;
    }
  }
};


const seekTo = (time) => {
  if (webcamPlayer.value && webcamDuration.value !== null) {
    webcamProgrammaticSeek.value = true;
    const newTime = Math.min(time, webcamDuration.value);
    webcamPlayer.value.setCurrentTime(newTime);
    if (webcamIsPlaying.value) {
      isSyncing.value = true;
      webcamPlayer.value.pause();
      isSyncing.value = false;
    }
  }
  if (screenPlayer.value && screenDuration.value !== null) {
    screenProgrammaticSeek.value = true;
    const newTime = Math.min(time, screenDuration.value);
    screenPlayer.value.setCurrentTime(newTime);
    if (screenIsPlaying.value) {
      isSyncing.value = true;
      screenPlayer.value.pause();
      isSyncing.value = false;
    }
  }
};


const downloadResult = () => {
  const dataStr = JSON.stringify(suspiciousList.value, null, 2);
  const blob = new Blob([dataStr], { type: 'application/json' });
  const url = URL.createObjectURL(blob);
  const link = document.createElement('a');
  link.href = url;
  link.download = `recording_${recordingId}_suspicious.json`;
  link.click();
  URL.revokeObjectURL(url);
};
</script>

<style scoped>
.result-view {
  min-height: 100vh;
  background-color: #e6f0fa;
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 2rem;
  position: relative;
}

.back-button {
  position: absolute;
  top: 2rem;
  left: 2rem;
  padding: 0.5rem 1rem;
  background-color: rgba(255, 255, 255, 0.9);
  color: #007bff;
  border: 1px solid #007bff;
  border-radius: 30px;
  cursor: pointer;
  font-size: 1rem;
  font-weight: 500;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
  transition: background-color 0.2s, color 0.2s;
  z-index: 10;
}

.back-button:hover {
  background-color: #007bff;
  color: white;
  border-color: #007bff;
}

.content-card {
  max-width: 1200px;
  width: 100%;
  background-color: #ffffff;
  border-radius: 24px;
  box-shadow: 0 8px 30px rgba(0, 0, 0, 0.1);
  padding: 2rem;
}

.title {
  text-align: center;
  margin-bottom: 2rem;
  color: #1a2b3c;
}

.blocks {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 2rem;
  margin-bottom: 2rem;
}

.block {
  display: flex;
  flex-direction: column;
  align-items: stretch;
}

.block-label {
  margin-bottom: 1rem;
  font-size: 1.2rem;
  font-weight: 500;
  text-align: center;
  color: #2c3e50;
}

.loading-placeholder {
  padding: 2rem;
  text-align: center;
  background-color: #f0f0f0;
  border-radius: 8px;
  color: #666;
}

.suspicious-section {
  margin-top: 2rem;
  border-top: 1px solid #e2e8f0;
  padding-top: 1.5rem;
}

.suspicious-title {
  margin-bottom: 1rem;
  font-size: 1.4rem;
  font-weight: 500;
  color: #2c3e50;
}

.suspicious-content {
  display: flex;
  gap: 2rem;
  align-items: flex-start;
}

.suspicious-list-wrapper {
  flex: 1;
  min-width: 0;
}

.empty-suspicious {
  text-align: center;
  padding: 2rem;
  color: #7f8c8d;
  background-color: #f8fafc;
  border-radius: 12px;
}

.suspicious-list {
  display: flex;
  flex-direction: column;
  gap: 0.75rem;
}

.download-button {
  flex-shrink: 0;
  width: 200px;
  padding: 1rem 1.5rem;
  background-color: #007bff;
  color: white;
  border: none;
  border-radius: 12px;
  font-size: 1rem;
  font-weight: 500;
  cursor: pointer;
  box-shadow: 0 4px 8px rgba(0, 123, 255, 0.2);
  transition: background-color 0.2s, transform 0.1s;
  white-space: nowrap;
}

.download-button:hover {
  background-color: #0056b3;
}

.download-button:active {
  transform: scale(0.98);
}
</style>