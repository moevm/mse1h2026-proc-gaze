<template>
  <div class="calibration-view">

    <div class="content-card">
      <h1 class="title">Калибровка взгляда</h1>

      <div v-if="stage === 'description'" class="description-stage">
        <p class="description-text">
          Для калибровки потребуется доступ к вашей камере и экрану.
          После начала записи в углах экрана будут последовательно появляться красные круги.
          Наведите курсор на круг и нажмите левую кнопку мыши.
          После нажатия на последний круг запись автоматически остановится.
        </p>
        <div class="button-container">
          <button class="start-btn" @click="startRecording">Начать запись</button>
        </div>
      </div>

      <div v-else-if="stage === 'recording'" class="recording-stage">
        <p class="recording-hint">
          Идёт запись... Нажимайте на красные круги в углах экрана.
        </p>
        <Teleport to="body">
          <div class="calibration-overlay">
            <div
                v-for="circle in circles"
                :key="circle.id"
                class="calibration-circle"
                :class="{ active: circle.active }"
                :style="{ left: circle.x + 'px', top: circle.y + 'px' }"
                @click="onCircleClick(circle)"
            ></div>
          </div>
        </Teleport>
      </div>

      <div v-else-if="stage === 'preview'" class="preview-stage">
        <div class="blocks">
          <div class="block">
            <h3 class="block-label">Видео с камеры</h3>
            <VideoPlayer
                v-if="cameraVideoUrl"
                ref="cameraPlayer"
                :src="cameraVideoUrl"
            />
            <div v-else class="loading-placeholder">Видео камеры не доступно</div>
          </div>
          <div class="block">
            <h3 class="block-label">Видео с экрана</h3>
            <VideoPlayer
                v-if="screenVideoUrl"
                ref="screenPlayer"
                :src="screenVideoUrl"
            />
            <div v-else class="loading-placeholder">Видео экрана не доступно</div>
          </div>
        </div>

        <div class="uuid-section">
          <label for="studentUuid" class="uuid-label">UUID студента</label>
          <input
              id="studentUuid"
              type="text"
              v-model="studentUuid"
              placeholder="xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx"
              :class="['uuid-input', { 'invalid': studentUuid && !isValidUuid }]"
          />
          <p v-if="studentUuid && !isValidUuid" class="error-message">
            Введите корректный UUID (формат: 8-4-4-4-12 шестнадцатеричных цифр)
          </p>
        </div>

        <div class="submit-section">
          <button
              class="submit-btn"
              :disabled="!canSubmit || isUploading"
              @click="uploadCalibration"
          >
            {{ isUploading ? 'Загрузка...' : 'Загрузить' }}
          </button>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onBeforeUnmount } from 'vue'
import { useRouter } from 'vue-router'
import VideoPlayer from '@/components/VideoPlayer.vue'

const stage = ref('description')

const cameraStream = ref(null)
const screenStream = ref(null)
const cameraRecorder = ref(null)
const screenRecorder = ref(null)
const cameraChunks = ref([])
const screenChunks = ref([])

const cameraVideoBlob = ref(null)
const screenVideoBlob = ref(null)
const cameraVideoUrl = ref(null)
const screenVideoUrl = ref(null)

const studentUuid = ref('')
const isValidUuid = computed(() => {
  const uuidRegex = /^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$/i
  return uuidRegex.test(studentUuid.value)
})

const isUploading = ref(false)

const circles = ref([])

const recordingStartTime = ref(null)

const calibrationData = ref({
  windowWidth: 0,
  windowHeight: 0,
  clicks: []
})

const currentCircleIndex = ref(0)

const isProcessingClick = ref(false)

const cameraPlayer = ref(null)
const screenPlayer = ref(null)


const canSubmit = computed(() => {
  return cameraVideoBlob.value && screenVideoBlob.value && isValidUuid.value
})


const onCircleClick = (circle) => {
  if (!circle.active || isProcessingClick.value) return

  isProcessingClick.value = true

  const elapsedSeconds = (Date.now() - recordingStartTime.value) / 1000

  calibrationData.value.clicks.push({
    time: elapsedSeconds,
    x: circle.x + 20,
    y: circle.y + 20
  })

  circle.active = false

  currentCircleIndex.value++
  if (currentCircleIndex.value < circles.value.length) {
    circles.value[currentCircleIndex.value].active = true
  } else {
    stopRecordingAndProceed()
  }

  isProcessingClick.value = false
}


const startRecording = async () => {
  try {
    screenStream.value = await navigator.mediaDevices.getDisplayMedia({
      video: true,
      audio: false
    })
    cameraStream.value = await navigator.mediaDevices.getUserMedia({
      video: true,
      audio: false
    })

    cameraChunks.value = []
    screenChunks.value = []

    cameraRecorder.value = new MediaRecorder(cameraStream.value, {
      mimeType: 'video/webm;codecs=vp9'
    })
    cameraRecorder.value.ondataavailable = (e) => {
      if (e.data.size > 0) cameraChunks.value.push(e.data)
    }
    cameraRecorder.value.onstop = () => {
      cameraVideoBlob.value = new Blob(cameraChunks.value, { type: 'video/webm' })
      cameraVideoUrl.value = URL.createObjectURL(cameraVideoBlob.value)
      cameraStream.value.getTracks().forEach(track => track.stop())
    }

    screenRecorder.value = new MediaRecorder(screenStream.value, {
      mimeType: 'video/webm;codecs=vp9'
    })
    screenRecorder.value.ondataavailable = (e) => {
      if (e.data.size > 0) screenChunks.value.push(e.data)
    }
    screenRecorder.value.onstop = () => {
      screenVideoBlob.value = new Blob(screenChunks.value, { type: 'video/webm' })
      screenVideoUrl.value = URL.createObjectURL(screenVideoBlob.value)
      screenStream.value.getTracks().forEach(track => track.stop())
    }

    cameraRecorder.value.start()
    screenRecorder.value.start()

    recordingStartTime.value = Date.now()

    const winW = window.innerWidth
    const winH = window.innerHeight

    calibrationData.value = {
      windowWidth: winW,
      windowHeight: winH,
      clicks: []
    }

    const padding = 20
    const circleSize = 40
    circles.value = [
      { id: 1, x: padding, y: padding, active: true },
      { id: 2, x: winW - circleSize - padding, y: padding, active: false },
      { id: 3, x: padding, y: winH - circleSize - padding, active: false },
      { id: 4, x: winW - circleSize - padding, y: winH - circleSize - padding, active: false }
    ]

    currentCircleIndex.value = 0
    stage.value = 'recording'
  } catch (error) {
    console.error('Error accessing devices:', error)
    alert('Не удалось получить доступ к камере или экрану. Пожалуйста, разрешите доступ.')
  }
}

const stopRecordingAndProceed = () => {
  if (cameraRecorder.value && cameraRecorder.value.state !== 'inactive') {
    cameraRecorder.value.stop()
  }
  if (screenRecorder.value && screenRecorder.value.state !== 'inactive') {
    screenRecorder.value.stop()
  }

  stage.value = 'preview'
}

const uploadCalibration = async () => {
  if (!canSubmit.value) return

  isUploading.value = true
  try {
  //   API query
  } catch (error) {
    console.error('Error with upload calibration:', error)
  } finally {
    isUploading.value = false
  }
}

onBeforeUnmount(() => {
  if (cameraRecorder.value && cameraRecorder.value.state !== 'inactive') {
    cameraRecorder.value.stop()
  }
  if (screenRecorder.value && screenRecorder.value.state !== 'inactive') {
    screenRecorder.value.stop()
  }
  if (cameraStream.value) {
    cameraStream.value.getTracks().forEach(track => track.stop())
  }
  if (screenStream.value) {
    screenStream.value.getTracks().forEach(track => track.stop())
  }
  if (cameraVideoUrl.value) URL.revokeObjectURL(cameraVideoUrl.value)
  if (screenVideoUrl.value) URL.revokeObjectURL(screenVideoUrl.value)
})
</script>

<style scoped>
.calibration-view {
  min-height: 100vh;
  background-color: #e6f0fa;
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 2rem;
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

.description-stage {
  text-align: center;
}

.description-text {
  font-size: 1.1rem;
  line-height: 1.6;
  color: #2d3748;
  margin-bottom: 2rem;
}

.start-btn {
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

.start-btn:hover {
  background-color: #0056b3;
  transform: scale(1.02);
}

.recording-stage {
  text-align: center;
}

.recording-hint {
  font-size: 1.2rem;
  color: #2d3748;
  padding: 1rem;
  background-color: #fef9c3;
  border-radius: 12px;
  margin-bottom: 1rem;
}

.preview-stage .blocks {
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

.uuid-section {
  margin: 2rem auto;
  max-width: 500px;
  text-align: left;
}

.uuid-label {
  display: block;
  margin-bottom: 0.5rem;
  font-weight: 500;
  color: #2c3e50;
}

.uuid-input {
  width: 100%;
  padding: 0.75rem 1rem;
  font-size: 1rem;
  border: 2px solid #d1d9e6;
  border-radius: 12px;
  transition: border-color 0.2s, box-shadow 0.2s;
  outline: none;
  box-sizing: border-box;
}

.uuid-input:focus {
  border-color: #007bff;
  box-shadow: 0 0 0 3px rgba(0, 123, 255, 0.1);
}

.uuid-input.invalid {
  border-color: #dc3545;
  background-color: #fff8f8;
}

.error-message {
  margin-top: 0.5rem;
  color: #dc3545;
  font-size: 0.9rem;
}

.submit-section {
  margin-top: 2rem;
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
  .preview-stage .blocks {
    grid-template-columns: 1fr;
  }
}
</style>


<style>
.calibration-overlay {
  position: fixed;
  top: 0;
  left: 0;
  width: 100%;
  height: 100%;
  pointer-events: none;
  z-index: 9999;
}

.calibration-circle {
  position: absolute;
  width: 40px;
  height: 40px;
  border-radius: 50%;
  background-color: red;
  border: 3px solid white;
  box-shadow: 0 0 10px rgba(0,0,0,0.5);
  pointer-events: auto;
  cursor: pointer;
  transition: opacity 0.2s;
  opacity: 0;
}

.calibration-circle.active {
  opacity: 1;
}
</style>