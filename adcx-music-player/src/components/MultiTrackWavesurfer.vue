<template>
  <div v-if="audioStore.isReady" class="waveforms-container">
    <div class="controls">
      <v-btn @click="playPause" :disabled="!isWaveformReady">
        <v-progress-circular
          v-show="!isWaveformReady"
          indeterminate
          size="20"
          width="2"
          color="primary"
          class="mr-2"
        />
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
        :disabled="!isWaveformReady"
      />
    </div>

    <div ref="multitrackContainer" class="multitrack-container" />

    <div class="track-controls">
      <div v-for="track in tracks" :key="track.name" class="track-control">
        <span class="track-name">{{ track.name }}</span>
        <div class="track-buttons">
          <v-btn
            size="small"
            variant="text"
            :disabled="!isWaveformReady"
            :class="{ 'mute-active': track.muted }"
            @click="handleMuteChange(track, !track.muted)"
          >
            M
          </v-btn>
          <v-btn
            size="small"
            variant="text"
            :disabled="!isWaveformReady"
            :class="{ 'solo-active': track.solo }"
            @click="handleSoloChange(track, !track.solo)"
          >
            S
          </v-btn>
        </div>
        <v-slider
          density="compact"
          :model-value="track.volume"
          :min="0"
          :max="1"
          :step="0.01"
          @update:model-value="(value) => handleVolumeChange(track, value)"
          hide-details
          class="volume-slider"
          :disabled="!isWaveformReady"
        />
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, onUnmounted, watch } from 'vue';
import Multitrack from 'wavesurfer-multitrack';
import WaveSurfer from 'wavesurfer.js';
import RegionsPlugin from 'wavesurfer.js/dist/plugins/regions';
import * as Tone from 'tone';
import { useAudioStore } from '../stores/audio';
import { useBeatsStore } from '../stores/beats';

const audioStore = useAudioStore();
const beatsStore = useBeatsStore();
const multitrackContainer = ref<HTMLElement | null>(null);
let multitrack: Multitrack | null = null;

interface Track {
  id: number;
  name: string;
  volume: number;
  muted: boolean;
  solo: boolean;
  trackname: string;
}

interface Marker {
  time: number;
  label: string;
  color?: string;
  position?: 'top' | 'bottom';
}

const isPlaying = ref(false);
const zoom = ref(30);

const tracks = ref<Track[]>([
  { id: 0, name: 'Vocals', volume: 1, muted: false, solo: false, trackname: 'vocals.wav' },
  { id: 1, name: 'Guitar', volume: 1, muted: false, solo: false, trackname: 'guitar.wav' },
  { id: 2, name: 'Bass', volume: 1, muted: false, solo: false, trackname: 'bass.wav' },
  { id: 3, name: 'Piano', volume: 1, muted: false, solo: false, trackname: 'piano.wav' },
  { id: 4, name: 'Drums', volume: 1, muted: false, solo: false, trackname: 'drums.wav' },
  { id: 5, name: 'Other', volume: 1, muted: false, solo: false, trackname: 'other.wav' },
]);

const markerDefaults = {
  label: '',
  color: 'white',
  position: 'top' as const
};

const markers = ref<Marker[]>(
  beatsStore.beatTimes.map(time => ({
    time,
    ...markerDefaults
  }))
);

watch(
  () => beatsStore.beatTimes,
  (newBeatTimes) => {
    markers.value = newBeatTimes.map(time => ({
      time,
      ...markerDefaults
    }));
    if (audioStore.isReady) {
      initializeMultitrack();
    }
  }
);

// Update Tone.js settings
const synth = new Tone.Synth({
  oscillator: {
    type: "triangle"
  },
  envelope: {
    attack: 0,
    decay: 0.1,
    sustain: 0,
    release: 0.1
  }
}).toDestination();

synth.volume.value = 0;

let scheduledPulses: number[] = [];

// Schedule sound playback at marker positions
const schedulePulses = async () => {
  if (!multitrack) return;

  // Clear existing schedules
  clearScheduledPulses();

  // Ensure Tone.js is ready
  await Tone.start();
  
  const currentTime = multitrack.getCurrentTime();
  
  // Schedule markers after current position
  markers.value.forEach(marker => {
    if (marker.time >= currentTime) {
      const timeOffset = marker.time - currentTime;
      // Function to play sound immediately
      const playSound = () => {
        synth.triggerAttackRelease("A5", "32n");
      };

      // Schedule
      const id = setTimeout(playSound, timeOffset * 1000);
      scheduledPulses.push(id);
    }
  });
};

// Clear scheduled metronome sounds
const clearScheduledPulses = () => {
  scheduledPulses.forEach(id => {
    clearTimeout(id);
  });
  scheduledPulses = [];
};

const isWaveformReady = ref(false);

const initializeMultitrack = () => {
  if (!audioStore.isReady || !multitrackContainer.value) return;

  isWaveformReady.value = false;

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
    markers: markers.value
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
    timelineOptions: {
      height: 30,
    },
  });

  // Wait for all tracks to be ready
  multitrack.once('canplay', () => {
    console.log('All tracks loaded and ready to play');
    isWaveformReady.value = true;
  });

  // Error handling
  multitrack.on('error', (error) => {
    console.error('Error loading tracks:', error);
    isWaveformReady.value = false;
  });

  // Handle marker click
  multitrack.on('marker-click', async (marker: any) => {
    console.log('Marker clicked:', marker);
    multitrack?.setTime(marker.time);
    
    try {
      await Tone.start();
      synth.triggerAttackRelease("A5", "32n", undefined, 1);
    } catch (error) {
      console.error('Error playing marker sound:', error);
    }
  });

  // Update handling of playback position changes
  multitrack.on('timeupdate', async () => {
    const currentTime = multitrack?.getCurrentTime() || 0;
    
    markers.value.forEach(async marker => {
      if (Math.abs(currentTime - marker.time) < 0.1) {
        try {
          await Tone.start();
          synth.triggerAttackRelease("A5", "32n", undefined, 1);
        } catch (error) {
          console.error('Error playing timeupdate sound:', error);
        }
      }
    });
  });

  // Handle playback finish
  multitrack.on('finish', () => {
    clearScheduledPulses();
    Tone.Transport.stop();
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
  const lightness = progressColor ? 75 : 80;
  return `hsl(${hue}, ${saturation}%, ${lightness}%)`;
};

const playPause = async () => {
  if (multitrack) {
    if (multitrack.isPlaying()) {
      multitrack.pause();
      isPlaying.value = false;
      clearScheduledPulses();
    } else {
      try {
        // Initialize Tone.js
        await Tone.start();
        // Play test sound
        synth.triggerAttackRelease("A5", "32n");
        
        multitrack.play();
        isPlaying.value = true;
        schedulePulses();
      } catch (error) {
        console.error('Error starting audio:', error);
      }
    }
  }
};

const handleVolumeChange = (track: Track, newVolume: number) => {
  track.volume = newVolume;
  updateTrackVolumes();
};

const handleMuteChange = (track: Track, muted: boolean) => {
  track.muted = muted;
  updateTrackVolumes();
};

const handleSoloChange = (track: Track, solo: boolean) => {
  track.solo = solo;
  updateTrackVolumes();
};

// Update all track volumes based on mute and solo states
const updateTrackVolumes = () => {
  if (!multitrack) return;

  const hasSoloTracks = tracks.value.some(t => t.solo);

  tracks.value.forEach(track => {
    let volume = track.volume;
    
    // If any track is soloed, only play soloed tracks
    if (hasSoloTracks) {
      volume = track.solo ? track.volume : 0;
    } else {
      volume = track.muted ? 0 : track.volume;
    }

    multitrack?.setTrackVolume(track.id, volume);
  });
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
  clearScheduledPulses();
  Tone.Transport.stop();
  Tone.Transport.cancel();
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
  position: relative;
}

.track-controls {
  display: flex;
  flex-direction: column;
  gap: 4px;
  padding: 16px;
  background: #2D2D2D;
  border-radius: 8px;
}

.track-control {
  display: grid;
  grid-template-columns: 80px 120px 1fr;
  align-items: center;
  gap: 16px;
  height: 40px;
}

.track-name {
  font-weight: bold;
  color: white;
  text-align: left;
}

.track-buttons {
  display: flex;
  gap: 8px;
}

.mute-active {
  color: #FFD700 !important;
  font-weight: bold;
}

.solo-active {
  color: #00BFFF !important;
  font-weight: bold;
}

.volume-slider {
  width: 100%;
  margin: 5px;
  min-width: 100px;
  flex-shrink: 0;
  margin-top: 0;
  margin-bottom: 0;
  justify-self: stretch;
}

.waveforms, .waveform-container {
  display: none;
}

:deep(.wavesurfer-region) {
  opacity: 0.7;
}

:deep(.wavesurfer-region:hover) {
  opacity: 1;
}

:deep(.wavesurfer-handle) {
  display: none;
}
</style>