<template>
  <v-app>
    <v-main>
      <div class="header-container">
        <div class="header">
          <h1>Mewt</h1>
          <v-text-field label="YouTube Address" v-model="address" style="width: 500px;" hide-details
            :disabled="isProcessingAudio" />
          <v-text-field label="Target BPM" v-model="targetBpm" style="width: 100px;" hide-details
            :disabled="isProcessingAudio" />
          <v-btn @click="submit" :loading="isProcessingAudio" :disabled="isProcessingAudio"
            :prepend-icon="isFirstTime ? 'mdi-play' : 'mdi-refresh'" color="primary">
            {{ isFirstTime ? 'Start' : 'Refresh' }}
          </v-btn>
        </div>
      </div>
      <MultiTrackWavesurfer class="content" :audioBasePath="audioStore.audioBasePath" v-show="!isFirstTime" />
    </v-main>
  </v-app>
</template>

<script setup lang="ts">
import { ref } from 'vue';
import MultiTrackWavesurfer from './components/MultiTrackWavesurfer.vue';
import { useAudioStore } from './stores/audio';

const address = ref('https://www.youtube.com/watch?v=M3B_TrJe9EI');
const targetBpm = ref(120);
const isProcessingAudio = ref(false);
const error = ref('');
const isFirstTime = ref(true);

const audioStore = useAudioStore();

const submit = async () => {
  error.value = '';
  isProcessingAudio.value = true;

  try {
    /*
    const response = await fetch('http://192.168.243.23:9000/separate-stems', {
    method: 'POST',
    headers: {
    'Content-Type': 'application/json',
    },
    body: JSON.stringify({
    youtube_url: address.value,
    timestretch_ratio: targetBpm.value,
    })
    });
  
    if (!response.ok) {
    throw new Error(`HTTP error! status: ${response.status}`);
    }
  
    const text = await response.text();
    let data;
    try {
    data = JSON.parse(text);
    } catch (e: unknown) {
    console.error('Error parsing JSON:', e);
    console.error('Response text:', text);
    throw new Error('Invalid JSON response from server');
    }
  
    console.log(data);
  
  
    let data = ['resources/tmp/htdemucs_6s/M3B_TrJe9EI/drums.wav', 'resources/tmp/htdemucs_6s/M3B_TrJe9EI/piano.wav', 'resources/tmp/htdemucs_6s/M3B_TrJe9EI/vocals.wav', 'resources/tmp/htdemucs_6s/M3B_TrJe9EI/guitar.wav', 'resources/tmp/htdemucs_6s/M3B_TrJe9EI/other.wav', 'resources/tmp/htdemucs_6s/M3B_TrJe9EI/bass.wav'];
  
    const firstFile = data[0];
    const match = firstFile.match(/^(resources\/tmp\/htdemucs_6s\/[^/]+\/)/);
    if (!match) {
    throw new Error('Invalid file path format');
    }
      audioStore.setAudioBasePath(match[1]);
      */

    audioStore.setAudioBasePath(`${Math.random()}`);
  } catch (e: unknown) {
    error.value = `Error: ${e instanceof Error ? e.message : 'Unknown error'}`;
    console.error('Error:', e);
  } finally {
    isProcessingAudio.value = false;
    isFirstTime.value = false;
  }
}
</script>

<style scoped>
.content-wrapper {
  height: 100vh;
  display: flex;
}

.header-container {
  display: flex;
  justify-content: center;
  width: 100%;
  height: 100px;
  background: #1E1E1E;
}

.header {
  display: flex;
  flex-direction: row;
  align-items: center;
  gap: 16px;
  width: 100%;
  max-width: 1000px;
  padding: 0 16px;
}

.header h1 {
  color: white;
  margin: 0;
  font-size: 2rem;
  min-width: 120px;
}

.content {
  height: calc(100vh - 100px);
  width: 100%;
}
</style>