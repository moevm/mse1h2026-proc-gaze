<template>
  <div class="video-player-container">
    <div v-if="src" class="video-wrapper">
      <video
          ref="videoElement"
          :src="src"
          controls
          @play="onPlay"
          @pause="onPause"
          @loadedmetadata="onLoadedMetadata"
          @seeked="onSeeked"
          @timeupdate="onTimeUpdate"
      ></video>
      <div v-if="duration" class="video-info">
        Длительность: {{ formatDuration(duration) }}
      </div>
    </div>
    <div v-else class="no-video">
      <p>Видео не загружено</p>
    </div>
  </div>
</template>

<script setup>
import { ref, watch } from 'vue'

const props = defineProps({
  src: { type: String, default: null }
})
const emit = defineEmits(['play', 'pause', 'seek', 'duration', 'timeupdate'])

const videoElement = ref(null)
const duration = ref(null)

watch(() => props.src, (newSrc) => {
  if (!newSrc) duration.value = null
})

const onPlay = () => emit('play')
const onPause = () => emit('pause')
const onLoadedMetadata = (e) => {
  duration.value = e.target.duration
  emit('duration', e.target.duration)
}
const onSeeked = () => emit('seek', videoElement.value.currentTime)
const onTimeUpdate = () => emit('timeupdate', videoElement.value.currentTime)

const formatDuration = (seconds) => {
  const h = Math.floor(seconds / 3600)
  const m = Math.floor((seconds % 3600) / 60)
  const s = Math.floor(seconds % 60)
  return [h, m, s]
      .map(v => v.toString().padStart(2, '0'))
      .join(':')
      .replace(/^00:/, '')
}

defineExpose({
  play: () => videoElement.value?.play(),
  pause: () => videoElement.value?.pause(),
  setCurrentTime: (time) => { if (videoElement.value) videoElement.value.currentTime = time; }
})
</script>

<style scoped>
.video-player-container {
  width: 100%;
  margin-top: 1rem;
}
.video-wrapper video {
  width: 100%;
  max-height: 300px;
  background: #000;
}
.no-video {
  padding: 2rem;
  text-align: center;
  background: #f0f0f0;
  border-radius: 4px;
  color: #666;
}
.video-info {
  margin-top: 0.5rem;
  font-size: 0.9rem;
  color: #333;
}
</style>