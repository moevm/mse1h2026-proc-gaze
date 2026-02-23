<template>
  <div class="dual-video-view">
    <h2>Два видео с синхронизацией</h2>
    <div class="row">
      <div class="column">
        <UploadArea
            :fileName="video1FileName"
            @upload="handleUpload1"
            @clear="handleClear1"
        />
        <VideoPlayer
            ref="player1"
            :src="video1Src"
            @play="onPlay(1)"
            @pause="onPause(1)"
        />
      </div>
      <div class="column">
        <UploadArea
            :fileName="video2FileName"
            @upload="handleUpload2"
            @clear="handleClear2"
        />
        <VideoPlayer
            ref="player2"
            :src="video2Src"
            @play="onPlay(2)"
            @pause="onPause(2)"
        />
      </div>
    </div>

    <div class="submit-section">
      <button
          @click="submitFiles"
          :disabled="!canSubmit"
          class="submit-btn"
      >
        Загрузить видео файлы
      </button>
    </div>
  </div>
</template>

<script setup>
import { ref, computed } from 'vue'
import UploadArea from '@/components/UploadArea.vue'
import VideoPlayer from '@/components/VideoPlayer.vue'

const video1Src = ref(null)
const video1FileName = ref(null)
const video1File = ref(null)

const video2Src = ref(null)
const video2FileName = ref(null)
const video2File = ref(null)

const player1 = ref(null)
const player2 = ref(null)

let isSyncing = false

const handleUpload1 = ({ file, url, fileName }) => {
  if (video1Src.value) {
    URL.revokeObjectURL(video1Src.value)
  }
  video1Src.value = url
  video1FileName.value = fileName
  video1File.value = file
}

const handleUpload2 = ({ file, url, fileName }) => {
  if (video2Src.value) {
    URL.revokeObjectURL(video2Src.value)
  }
  video2Src.value = url
  video2FileName.value = fileName
  video2File.value = file
}

const handleClear1 = () => {
  if (video1Src.value) {
    URL.revokeObjectURL(video1Src.value)
    video1Src.value = null
  }
  video1FileName.value = null
  video1File.value = null
}

const handleClear2 = () => {
  if (video2Src.value) {
    URL.revokeObjectURL(video2Src.value)
    video2Src.value = null
  }
  video2FileName.value = null
  video2File.value = null
}

const onPlay = (sourcePlayer) => {
  if (isSyncing) return
  isSyncing = true
  if (sourcePlayer === 1 && player2.value) {
    player2.value.play()
  } else if (sourcePlayer === 2 && player1.value) {
    player1.value.play()
  }
  isSyncing = false
}

const onPause = (sourcePlayer) => {
  if (isSyncing) return
  isSyncing = true
  if (sourcePlayer === 1 && player2.value) {
    player2.value.pause()
  } else if (sourcePlayer === 2 && player1.value) {
    player1.value.pause()
  }
  isSyncing = false
}

const canSubmit = computed(() => video1File.value && video2File.value)

const submitFiles = () => {
  if (!canSubmit.value) return

  const formData = new FormData()
  formData.append('video1', video1File.value)
  formData.append('video2', video2File.value)

  console.log('Send to server:', video1File.value.name, video2File.value.name)

  //api query
}
</script>

<style scoped>
.dual-video-view {
  max-width: 1200px;
  margin: 0 auto;
  padding: 1rem;
}
.row {
  display: flex;
  gap: 2rem;
  flex-wrap: wrap;
}
.column {
  flex: 1 1 400px;
  min-width: 300px;
}
.submit-section {
  margin-top: 2rem;
  text-align: center;
}
.submit-btn {
  padding: 0.75rem 2rem;
  font-size: 1.1rem;
  background-color: #007bff;
  color: white;
  border: none;
  border-radius: 4px;
  cursor: pointer;
  transition: background-color 0.2s;
}
.submit-btn:hover:not(:disabled) {
  background-color: #0056b3;
}
.submit-btn:disabled {
  background-color: #cccccc;
  cursor: not-allowed;
}
</style>