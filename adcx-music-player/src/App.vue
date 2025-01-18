<template>
  <v-app>
    <v-app-bar>
      <v-app-bar-title>
        ADCx India 🇮🇳 25 Music Player
      </v-app-bar-title>
    </v-app-bar>
    <v-main>
      <div class="content-wrapper" v-if="stage === 'input'">
        <div class="youtube-address-input">
          <v-icon size="large">mdi-youtube</v-icon>
          <v-text-field label="YouTube Address" v-model="address" style="width: 500px;"
            :disabled="isProcessingAudio" />
          <v-text-field label="Target BPM" v-model="targetBpm" style="width: 100px;"
            :disabled="isProcessingAudio" />
          <v-btn @click="submit" :loading="isProcessingAudio" :disabled="isProcessingAudio">
            Submit
          </v-btn>
        </div>
      </div>
      <MultiTrackWavesurfer 
        v-else-if="stage === 'player'" 
        :audioBasePath="audioStore.audioBasePath" 
      />
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
const stage = ref('input');

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

  audioStore.setAudioBasePath('hoge');
  stage.value = 'player';
  } catch (e: unknown) {
  error.value = `Error: ${e instanceof Error ? e.message : 'Unknown error'}`;
  console.error('Error:', e);
  } finally {
  isProcessingAudio.value = false;
  }
}
</script>

<style scoped>
.content-wrapper {
  height: 100vh;
  display: flex;
  align-items: center;
  justify-content: center;
}

.youtube-address-input {
  display: flex;
  flex-direction: row;
  align-items: center;
  justify-content: center;
  gap: 16px;
  width: 100%;
  max-width: 1000px;
  padding: 0 16px;
}

.error-message {
  color: red;
  margin-top: 16px;
  text-align: center;
}
</style>
