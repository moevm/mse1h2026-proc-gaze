<template>
  <div class="upload-view">
    <div class="content-card">
      <h1 class="title">Загрузка видео</h1>

      <div class="blocks">
        <div class="block">
          <h3 class="block-label">Добавить видео с камеры</h3>
          <UploadArea
              :fileName="cameraFileName"
              @upload="handleCameraUpload"
              @clear="handleCameraClear"
          />
          <VideoPlayer
              v-if="cameraVideoSrc"
              ref="cameraPlayer"
              :src="cameraVideoSrc"
              @play="onPlay('camera')"
              @pause="onPause('camera')"
              @seek="handleCameraSeek"
              @duration="handleCameraDuration"
              @timeupdate="handleCameraTimeUpdate"
          />
        </div>

        <div class="block">
          <h3 class="block-label">Добавить видео с экрана</h3>
          <UploadArea
              :fileName="screenFileName"
              @upload="handleScreenUpload"
              @clear="handleScreenClear"
          />
          <VideoPlayer
              v-if="screenVideoSrc"
              ref="screenPlayer"
              :src="screenVideoSrc"
              @play="onPlay('screen')"
              @pause="onPause('screen')"
              @seek="handleScreenSeek"
              @duration="handleScreenDuration"
              @timeupdate="handleScreenTimeUpdate"
          />
        </div>
      </div>

      <div class="submit-section">
        <button class="submit-btn" :disabled="!canSubmit" @click="submit">
          Отправить
        </button>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed } from 'vue'
import { useRouter } from 'vue-router'
import UploadArea from '@/components/UploadArea.vue'
import VideoPlayer from '@/components/VideoPlayer.vue'

const router = useRouter()

const cameraFileName = ref(null)
const cameraVideoSrc = ref(null)
const cameraVideoFile = ref(null)
const cameraPlayer = ref(null)
const cameraDuration = ref(null)
const cameraCurrentTime = ref(0)
const cameraIsPlaying = ref(false)

const screenFileName = ref(null)
const screenVideoSrc = ref(null)
const screenVideoFile = ref(null)
const screenPlayer = ref(null)
const screenDuration = ref(null)
const screenCurrentTime = ref(0)
const screenIsPlaying = ref(false)

const isSyncing = ref(false)
const cameraProgrammaticSeek = ref(false)
const screenProgrammaticSeek = ref(false)

const EPS = 0.1

const handleCameraUpload = ({ file, url, fileName }) => {
  if (cameraVideoSrc.value) URL.revokeObjectURL(cameraVideoSrc.value)
  cameraVideoSrc.value = url
  cameraFileName.value = fileName
  cameraVideoFile.value = file
  cameraDuration.value = null
  cameraCurrentTime.value = 0
  cameraIsPlaying.value = false

  if (screenPlayer.value) {
    screenProgrammaticSeek.value = true
    screenPlayer.value.setCurrentTime(0)
    screenCurrentTime.value = 0
    isSyncing.value = true
    screenPlayer.value.pause()
    isSyncing.value = false
  }
}
const handleCameraClear = () => {
  if (cameraVideoSrc.value) {
    URL.revokeObjectURL(cameraVideoSrc.value)
    cameraVideoSrc.value = null
  }
  cameraFileName.value = null
  cameraVideoFile.value = null
  cameraDuration.value = null
  cameraCurrentTime.value = 0
  cameraIsPlaying.value = false
}

const handleScreenUpload = ({ file, url, fileName }) => {
  if (screenVideoSrc.value) URL.revokeObjectURL(screenVideoSrc.value)
  screenVideoSrc.value = url
  screenFileName.value = fileName
  screenVideoFile.value = file
  screenDuration.value = null
  screenCurrentTime.value = 0
  screenIsPlaying.value = false

  if (cameraPlayer.value) {
    cameraProgrammaticSeek.value = true
    cameraPlayer.value.setCurrentTime(0)
    cameraCurrentTime.value = 0
    isSyncing.value = true
    cameraPlayer.value.pause()
    isSyncing.value = false
  }
}
const handleScreenClear = () => {
  if (screenVideoSrc.value) {
    URL.revokeObjectURL(screenVideoSrc.value)
    screenVideoSrc.value = null
  }
  screenFileName.value = null
  screenVideoFile.value = null
  screenDuration.value = null
  screenCurrentTime.value = 0
  screenIsPlaying.value = false
}

const handleCameraDuration = (dur) => { cameraDuration.value = dur }
const handleCameraTimeUpdate = (time) => { cameraCurrentTime.value = time }
const handleScreenDuration = (dur) => { screenDuration.value = dur }
const handleScreenTimeUpdate = (time) => { screenCurrentTime.value = time }

const handleCameraSeek = (time) => {
  if (cameraProgrammaticSeek.value) {
    cameraProgrammaticSeek.value = false
    return
  }

  if (screenPlayer.value && screenDuration.value !== null) {
    screenProgrammaticSeek.value = true
    const newTime = Math.min(time, screenDuration.value)
    screenPlayer.value.setCurrentTime(newTime)

    isSyncing.value = true
    screenPlayer.value.pause()
    isSyncing.value = false
  }
}

const handleScreenSeek = (time) => {
  if (screenProgrammaticSeek.value) {
    screenProgrammaticSeek.value = false
    return
  }

  if (cameraPlayer.value && cameraDuration.value !== null) {
    cameraProgrammaticSeek.value = true
    const newTime = Math.min(time, cameraDuration.value)
    cameraPlayer.value.setCurrentTime(newTime)

    isSyncing.value = true
    cameraPlayer.value.pause()
    isSyncing.value = false
  }
}

const handleCameraPlay = () => {
  if (isSyncing.value) return

  const wasCameraAtEnd = cameraDuration.value !== null && cameraCurrentTime.value >= cameraDuration.value - EPS

  if (wasCameraAtEnd) {
    if (screenDuration.value !== null && screenCurrentTime.value >= screenDuration.value - EPS) {
      screenProgrammaticSeek.value = true
      screenPlayer.value.setCurrentTime(0)
      isSyncing.value = true
      screenPlayer.value.play()
      isSyncing.value = false
    }
  } else {
    if (screenPlayer.value && screenDuration.value !== null &&
        screenCurrentTime.value < screenDuration.value - EPS && !screenIsPlaying.value) {
      isSyncing.value = true
      screenPlayer.value.play()
      isSyncing.value = false
    }
  }
}

const handleScreenPlay = () => {
  if (isSyncing.value) return

  const wasScreenAtEnd = screenDuration.value !== null && screenCurrentTime.value >= screenDuration.value - EPS

  if (wasScreenAtEnd) {
    if (cameraDuration.value !== null && cameraCurrentTime.value >= cameraDuration.value - EPS) {
      cameraProgrammaticSeek.value = true
      cameraPlayer.value.setCurrentTime(0)
      isSyncing.value = true
      cameraPlayer.value.play()
      isSyncing.value = false
    }
  } else {
    if (cameraPlayer.value && cameraDuration.value !== null &&
        cameraCurrentTime.value < cameraDuration.value - EPS && !cameraIsPlaying.value) {
      isSyncing.value = true
      cameraPlayer.value.play()
      isSyncing.value = false
    }
  }
}

const handleCameraPause = () => {
  if (isSyncing.value) return
  if (cameraDuration.value !== null && cameraCurrentTime.value >= cameraDuration.value - EPS) return

  isSyncing.value = true
  if (screenPlayer.value && screenIsPlaying.value) {
    screenPlayer.value.pause()
  }
  isSyncing.value = false
}

const handleScreenPause = () => {
  if (isSyncing.value) return
  if (screenDuration.value !== null && screenCurrentTime.value >= screenDuration.value - EPS) return

  isSyncing.value = true
  if (cameraPlayer.value && cameraIsPlaying.value) {
    cameraPlayer.value.pause()
  }
  isSyncing.value = false
}

const onPlay = (source) => {
  if (source === 'camera') {
    cameraIsPlaying.value = true
    handleCameraPlay()
  } else {
    screenIsPlaying.value = true
    handleScreenPlay()
  }
}
const onPause = (source) => {
  if (source === 'camera') {
    cameraIsPlaying.value = false
    handleCameraPause()
  } else {
    screenIsPlaying.value = false
    handleScreenPause()
  }
}

const canSubmit = computed(() => cameraVideoFile.value && screenVideoFile.value)
const submit = () => {
  if (!canSubmit.value) return
  // API запрос
  router.push({ name: 'MainView' })
}
</script>

<style scoped>
.upload-view {
  min-height: 100vh;
  background-color: #e6f0fa;
  display: flex;
  align-items: center;
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

.submit-section {
  margin-top: 3rem;
  text-align: center;
}

.submit-btn {
  padding: 0.75rem 2rem;
  font-size: 1.2rem;
  background-color: #007bff;
  color: white;
  border: none;
  border-radius: 40px;
  cursor: pointer;
  transition: background-color 0.2s, transform 0.1s;
  box-shadow: 0 2px 8px rgba(0, 123, 255, 0.3);
}

.submit-btn:hover:not(:disabled) {
  background-color: #0056b3;
  transform: scale(1.02);
}

.submit-btn:disabled {
  background-color: #cccccc;
  cursor: not-allowed;
  box-shadow: none;
}

@media (max-width: 768px) {
  .blocks {
    grid-template-columns: 1fr;
  }
}
</style>