<template>
  <v-app>
    <v-app-bar>
      <v-app-bar-title>ADCx India 25 Music Player</v-app-bar-title>
    </v-app-bar>
    <v-main>
      <MultiTrackWavesurfer v-if="stage === 'player'" />
      
      <div class="content-wrapper" v-if="stage === 'input'">
        <div class="youtube-address-input">
          <v-icon size="large">mdi-youtube</v-icon>
          <v-text-field label="YouTube Address" v-model="address" style="width: 500px;" :disabled="isProcessingAudio" />
          <v-text-field label="Target BPM" v-model="targetBpm" style="width: 100px;" :disabled="isProcessingAudio" />
          <v-btn @click="submit" :loading="isProcessingAudio" :disabled="isProcessingAudio">
            Submit
          </v-btn>
        </div>
      </div>
    </v-main>
    <v-footer>
      <div v-if="error" class="error-message">{{ error }}</div>
    </v-footer>
  </v-app>
</template>

<script setup lang="ts">
import { ref } from 'vue';
import MultiTrackWavesurfer from './components/MultiTrackWavesurfer.vue';

const address = ref('https://www.youtube.com/watch?v=n-AjbS1cyvQ');
const targetBpm = ref(120);
const isProcessingAudio = ref(false);
const error = ref('');
const stage = ref('input');

const submit = async () => {
  error.value = '';
  isProcessingAudio.value = true;
  
  try {
    const response = await fetch('http://localhost:5000/api/separateStems', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({
        youtube_url: address.value,
        target_bpm: targetBpm.value,
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
      console.error('Response text:', text);
      throw new Error('Invalid JSON response from server');
    }

    console.log(data);
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
