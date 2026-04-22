<template>
  <div class="dump-view">
    <div class="back-button" @click="goToMain">Вернуться на главную</div>

    <div class="content-card">
      <h1 class="title">Выгрузка студентов</h1>

      <div class="upload-section">
        <h3 class="block-label">Загрузите CSV файл со студентами</h3>
        <CsvUploadArea
            :fileName="csvFileName"
            @upload="handleUpload"
            @clear="handleClear"
        />
      </div>

      <div class="submit-section">
        <button class="submit-btn" :disabled="!csvFile" @click="submit">
          Отправить
        </button>
      </div>

      <div v-if="errorMessage" class="error-message-block">
        {{ errorMessage }}
      </div>

      <div v-if="resultJson" class="result-section">
        <p class="success-message">Файл успешно обработан. Скачайте результат:</p>
        <button class="download-btn" @click="downloadJson">Скачать JSON</button>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref } from 'vue'
import { useRouter } from 'vue-router'
import CsvUploadArea from '@/components/dump_student_view/CsvUploadArea.vue'
import { dumpApi } from '@/api'

const router = useRouter()

const csvFile = ref(null)
const csvFileName = ref(null)
const resultJson = ref(null)
const errorMessage = ref('')

const handleUpload = ({ file, fileName }) => {
  csvFile.value = file
  csvFileName.value = fileName
  errorMessage.value = ''
  resultJson.value = null
}

const handleClear = () => {
  csvFile.value = null
  csvFileName.value = null
  errorMessage.value = ''
  resultJson.value = null
}

const submit = async () => {
  if (!csvFile.value) return
  try {
    const data = await dumpApi.upload(csvFile.value)
    resultJson.value = data
    errorMessage.value = ''
  } catch (error) {
    console.error('Upload failed:', error)
    errorMessage.value = error.message || 'Ошибка при отправке файла'
    resultJson.value = null
  }
}

const downloadJson = () => {
  if (!resultJson.value) return
  const jsonStr = JSON.stringify(resultJson.value, null, 2)
  const blob = new Blob([jsonStr], { type: 'application/json' })
  const url = URL.createObjectURL(blob)
  const a = document.createElement('a')
  a.href = url
  a.download = 'students_dump.json'
  document.body.appendChild(a)
  a.click()
  document.body.removeChild(a)
  URL.revokeObjectURL(url)
}

const goToMain = () => {
  router.push({ name: 'MainView' })
}
</script>

<style scoped>
.dump-view {
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
  max-width: 800px;
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

.upload-section {
  margin-bottom: 2rem;
}

.block-label {
  margin-bottom: 1rem;
  font-size: 1.2rem;
  font-weight: 500;
  text-align: center;
  color: #2c3e50;
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

.error-message-block {
  margin-top: 1rem;
  padding: 1rem;
  background-color: #fff0f0;
  border-left: 4px solid #dc3545;
  color: #dc3545;
  border-radius: 8px;
}

.result-section {
  margin-top: 1.5rem;
  padding: 1rem;
  background-color: #f0f9f0;
  border-left: 4px solid #28a745;
  border-radius: 8px;
  text-align: center;
}

.success-message {
  margin-bottom: 1rem;
  color: #155724;
}

.download-btn {
  padding: 0.5rem 1.5rem;
  background-color: #28a745;
  color: white;
  border: none;
  border-radius: 30px;
  cursor: pointer;
  transition: background-color 0.2s;
}

.download-btn:hover {
  background-color: #218838;
}
</style>