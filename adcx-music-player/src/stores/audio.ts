import { defineStore } from 'pinia';
import { ref } from 'vue';

export const useAudioStore = defineStore('audio', () => {
  const audioBasePath = ref('');
  const isReady = ref(false);

  function setAudioBasePath(path: string) {
    audioBasePath.value = path;
    isReady.value = true;
  }

  function reset() {
    audioBasePath.value = '';
    isReady.value = false;
  }

  return {
    audioBasePath,
    isReady,
    setAudioBasePath,
    reset
  };
}); 