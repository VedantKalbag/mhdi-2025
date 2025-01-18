<template>
  <div v-if="audioStore.isReady" class="waveforms-container">
    <div class="controls">
      <v-btn @click="playPause">
        <v-icon>{{ isPlaying ? 'mdi-pause' : 'mdi-play' }}</v-icon>
      </v-btn>
      <v-slider
        v-model="zoom"
        :min="10"
        :max="100"
        :step="1"
        label="Zoom"
        hide-details
        class="zoom-slider"
        @update:model-value="updateZoom"
      />
    </div>

    <div ref="multitrackContainer" class="multitrack-container" />

    <div class="track-controls">
      <div v-for="track in tracks" :key="track.name" class="track-control">
        <span class="track-name">{{ track.name }}</span>
        <v-switch 
          :model-value="track.muted"
          :label="track.muted ? 'Muted' : 'Unmuted'" 
          @update:model-value="(value) => handleMuteChange(track, value)"
        />
        <v-slider
          :model-value="track.volume"
          :min="0"
          :max="1"
          :step="0.01"
          @update:model-value="(value) => handleVolumeChange(track, value)"
          hide-details
          class="volume-slider"
        />
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, onUnmounted, watch } from 'vue';
import Multitrack from 'wavesurfer-multitrack';
import { useAudioStore } from '../stores/audio';

const audioStore = useAudioStore();
const multitrackContainer = ref<HTMLElement | null>(null);
let multitrack: Multitrack | null = null;

interface Track {
  id: number;
  name: string;
  volume: number;
  muted: boolean;
  trackname: string;
}

const isPlaying = ref(false);
const zoom = ref(30);

const tracks = ref<Track[]>([
  { id: 0, name: 'Vocals', volume: 1, muted: false, trackname: 'vocals.wav' },
  { id: 1, name: 'Guitar', volume: 1, muted: false, trackname: 'guitar.wav' },
  { id: 2, name: 'Bass', volume: 1, muted: false, trackname: 'bass.wav' },
  { id: 3, name: 'Piano', volume: 1, muted: false, trackname: 'piano.wav' },
  { id: 4, name: 'Drums', volume: 1, muted: false, trackname: 'drums.wav' },
  { id: 5, name: 'Other', volume: 1, muted: false, trackname: 'other.wav' },
]);

const initializeMultitrack = () => {
  if (!audioStore.isReady || !multitrackContainer.value) return;

  const debugMode = true;
  const baseUrl = 'http://192.168.243.23:9000/audio/';
  const basePath = debugMode ? 'http://localhost:8080/' : `${baseUrl}${audioStore.audioBasePath}`;

  const trackConfigs = tracks.value.map(track => ({
    id: track.id,
    draggable: false,
    url: `${basePath}${track.trackname}`,
    volume: track.muted ? 0 : track.volume,
    options: {
      waveColor: getTrackColor(track.id, false),
      progressColor: getTrackColor(track.id, true),
      height: 60,
    },
  }));

  if (multitrack) {
    multitrack.destroy();
  }

  multitrack = Multitrack.create(trackConfigs, {
    container: multitrackContainer.value,
    minPxPerSec: zoom.value,
    cursorWidth: 2,
    cursorColor: '#D72F21',
    trackBackground: '#2D2D2D',
    trackBorderColor: '#7C7C7C',
  });

  multitrack.on('ready', () => {
    console.log('Tracks initialized:', trackConfigs.map(t => ({
      id: t.id,
      volume: t.volume
    })));
  });
};

watch(
  () => audioStore.isReady,
  (newValue) => {
    if (newValue) {
      initializeMultitrack();
    }
  }
);

onMounted(() => {
  if (audioStore.isReady) {
    initializeMultitrack();
  }
});

const getTrackColor = (index: number, progressColor: boolean) => {
  const hue = index * (360 / tracks.value.length);
  const saturation = 100;
  const lightness = progressColor ? 75 : 60;
  return `hsl(${hue}, ${saturation}%, ${lightness}%)`;
};

const playPause = () => {
  if (multitrack) {
    if (multitrack.isPlaying()) {
      multitrack.pause();
      isPlaying.value = false;
    } else {
      multitrack.play();
      isPlaying.value = true;
    }
  }
};

const handleVolumeChange = (track: Track, newVolume: number) => {
  console.log(track, newVolume);
  track.volume = newVolume;
  if (multitrack) {
    multitrack.setTrackVolume(track.id, newVolume);
  }
};

const handleMuteChange = (track: Track, muted: boolean) => {
  console.log(track, muted);
  track.muted = muted;
  if (multitrack) {
    const volume = muted ? 0 : track.volume;
    multitrack.setTrackVolume(track.id, volume);
  }
};

const updateZoom = (value: number) => {
  if (multitrack) {
    try {
      multitrack.zoom(value);
    } catch (error) {
      console.error('Error updating zoom:', error);
    }
  }
};

onUnmounted(() => {
  if (multitrack) {
    multitrack.destroy();
  }
  audioStore.reset();
});
</script>

<style scoped>
.waveforms-container {
  padding: 20px;
  display: flex;
  flex-direction: column;
  gap: 20px;
  max-width: 1200px;
  margin: 0 auto;
  background: #1E1E1E;
  color: white;
}

.controls {
  display: flex;
  align-items: center;
  gap: 16px;
  padding: 16px;
}

.zoom-slider {
  width: 200px;
}

.multitrack-container {
  width: 100%;
  background: #2D2D2D;
  border-radius: 8px;
  padding: 16px;
  min-height: 400px;
}

.track-controls {
  display: flex;
  flex-direction: column;
  gap: 16px;
  padding: 16px;
  background: #2D2D2D;
  border-radius: 8px;
}

.track-control {
  display: flex;
  align-items: center;
  gap: 16px;
}

.track-name {
  min-width: 80px;
  font-weight: bold;
  color: white;
}

.volume-slider {
  width: 200px;
  flex-shrink: 0;
}

.waveforms, .waveform-container {
  display: none;
}
</style>