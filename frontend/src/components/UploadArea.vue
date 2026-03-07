<template>
  <div
      class="upload-area"
      @dragover.prevent
      @drop.prevent="onDrop"
      @click="triggerFileInput"
      :class="{ 'has-file': fileName }"
  >
    <input
        type="file"
        ref="fileInput"
        accept="video/*"
        @change="onFileChange"
        hidden
    />
    <div v-if="!fileName" class="placeholder">
      <p>Перетащите видео сюда или нажмите для выбора</p>
    </div>
    <div v-else class="file-info">
      <span class="file-name">{{ fileName }}</span>
      <button @click.stop="clearFile" class="clear-btn">✕</button>
    </div>
  </div>
</template>

<script setup>
import { ref } from 'vue'

const props = defineProps({
  fileName: {
    type: String,
    default: null
  }
})

const emit = defineEmits(['upload', 'clear'])

const fileInput = ref(null)

const triggerFileInput = () => {
  if (!props.fileName) {
    fileInput.value.click()
  }
}

const onFileChange = (event) => {
  const file = event.target.files[0]
  if (file) {
    processFile(file)
  }
}

const onDrop = (event) => {
  const file = event.dataTransfer.files[0]
  if (file && file.type.startsWith('video/')) {
    processFile(file)
  }
}

const processFile = (file) => {
  const url = URL.createObjectURL(file)
  emit('upload', { file, url, fileName: file.name })
}

const clearFile = () => {
  emit('clear')
  if (fileInput.value) {
    fileInput.value.value = ''
  }
}
</script>

<style scoped>
.upload-area {
  border: 2px dashed #ccc;
  border-radius: 8px;
  padding: 2rem;
  text-align: center;
  cursor: pointer;
  transition: background-color 0.2s;
  min-height: 150px;
  display: flex;
  align-items: center;
  justify-content: center;
}
.upload-area:hover {
  background-color: #f9f9f9;
}
.upload-area.has-file {
  border-style: solid;
  border-color: #007bff;
  background-color: #e6f2ff;
  color: black;
  min-height: 15px;
}
.placeholder {
  color: #666;
}
.file-info {
  display: flex;
  align-items: center;
  gap: 0.5rem;
}
.file-name {
  font-weight: bold;
  word-break: break-all;
}
.clear-btn {
  background: none;
  border: none;
  color: #ff4444;
  font-size: 1.2rem;
  cursor: pointer;
  padding: 0 0.5rem;
}
.clear-btn:hover {
  color: #cc0000;
}
</style>