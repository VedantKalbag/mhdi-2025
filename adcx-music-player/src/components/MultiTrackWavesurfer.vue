<template>
  <div v-if="audioStore.isReady" class="waveforms-container">
    <div v-show="!isWaveformReady" class="loading-overlay">
      <v-progress-circular
        indeterminate
        size="50"
        width="3"
        color="primary"
      />
    </div>
    <div class="controls">
      <v-btn @click="playPause" :disabled="!isWaveformReady">
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

    <div class="tracks-wrapper">
      <div class="track-controls">
        <div v-for="track in tracks" :key="track.name" class="track-control">
          <div class="track-control-rows">
            <div class="track-name-container">
              <span class="track-name" style="font-size: 1.2rem;">{{ track.name }}</span>
            </div>
            <div class="track-controls-row">
              <div class="track-buttons">
                <v-btn
                  size="small"
                  variant="text"
                  :disabled="!isWaveformReady"
                  :class="{ 'solo-active': track.solo }"
                  @click="handleSoloChange(track, !track.solo)"
                  class="control-btn"
                >
                  S
                </v-btn>
                <v-btn
                  size="small"
                  variant="text"
                  :disabled="!isWaveformReady"
                  :class="{ 'mute-active': track.muted }"
                  @click="handleMuteChange(track, !track.muted)"
                  class="control-btn"
                >
                  M
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
                style="max-width: 180px;"
              />
            </div>
          </div>
        </div>
      </div>
      <div ref="multitrackContainer" class="multitrack-container" />
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
  { id: 0, name: '🎤 Vocals', volume: 1, muted: false, solo: false, trackname: 'vocals.wav' },
  { id: 1, name: '🎸 Guitar', volume: 1, muted: false, solo: false, trackname: 'guitar.wav' },
  { id: 2, name: '🎸 Bass', volume: 1, muted: false, solo: false, trackname: 'bass.wav' },
  { id: 3, name: '🎹 Piano', volume: 1, muted: false, solo: false, trackname: 'piano.wav' },
  { id: 4, name: '🥁 Drums', volume: 1, muted: false, solo: false, trackname: 'drums.wav' },
  { id: 5, name: '🎼 Other', volume: 1, muted: false, solo: false, trackname: 'other.wav' },
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

  // Calculate track height based on container height
  const containerHeight = multitrackContainer.value.clientHeight;
  const timelineHeight = 30;
  const trackHeight = Math.floor((containerHeight - timelineHeight) / tracks.value.length);

  // Update CSS variable for track control height
  const trackControlsElement = document.querySelector('.track-controls');
  if (trackControlsElement) {
    trackControlsElement.style.setProperty('--track-height', `${trackHeight}px`);
  }

  const trackConfigs = tracks.value.map(track => ({
    id: track.id,
    draggable: false,
    url: `${basePath}${track.trackname}`,
    volume: track.muted ? 0 : track.volume,
    options: {
      waveColor: getTrackColor(track.id, false),
      progressColor: getTrackColor(track.id, true),
      height: trackHeight,
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

// Handle window resize
const handleResize = () => {
  if (audioStore.isReady) {
    initializeMultitrack();
  }
};

// Add resize listener
window.addEventListener('resize', handleResize);

// Clean up
onUnmounted(() => {
  window.removeEventListener('resize', handleResize);
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
  display: flex;
  flex-direction: column;
  gap: 12px;
  background: #1E1E1E;
  color: white;
  position: relative;
  height: 100%;
  padding: 12px 20px;
}

.loading-overlay {
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: rgba(30, 30, 30, 0.8);
  display: flex;
  justify-content: center;
  align-items: center;
  z-index: 100;
  backdrop-filter: blur(2px);
}

.controls {
  display: flex;
  align-items: center;
  gap: 16px;
  padding: 8px;
}

.zoom-slider {
  width: 200px;
}

.tracks-wrapper {
  display: flex;
  gap: 8px;
  flex: 1;
  min-height: 0;
  overflow: hidden;
}

.track-controls {
  display: flex;
  flex-direction: column;
  gap: 0;
  padding: 10px;
  top: 10px;
  background: #2D2D2D;
  border-radius: 8px 0px 0px 8px;
  width: 300px;
  min-width: 300px;
  padding-top: 8px;
  overflow: hidden;
  height: 100%;
}

.track-control {
  align-items: center;
  height: calc(var(--track-height, 60px) + 2px);
  padding-right: 8px;
  border-bottom: solid 1px #7C7C7C;
}

.track-control-rows {
  display: flex;
  flex-direction: column;
  justify-content: space-evenly;
  height: 100%;
  width: 100%;
}

.track-name-container {
  padding: 0 4px;
  width: 100%;
  overflow: hidden;
}

.track-controls-row {
  display: flex;
  align-items: center;
  gap: 4px;
  padding: 0 4px;
}

.track-name {
  font-weight: bold;
  color: white;
  text-align: left;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
  display: block;
  font-size: 0.9rem;
}

.track-buttons {
  display: flex;
  gap: 2px;
  justify-content: flex-start;
  min-width: 80px;
}

.control-btn {
  min-width: 36px !important;
  width: 36px;
  padding: 0 !important;
  font-weight: bold;
  font-size: 1rem;
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
  margin: 0;
  flex-shrink: 0;
  justify-self: stretch;
  padding: 0 2px;
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

.multitrack-container {
  width: 100%;
  background: #2D2D2D;
  border-radius: 0px 8px 8px 0px;
  flex-grow: 1;
  position: relative;
  padding-top: 8px;
  padding-bottom: 8px;
  padding-left: 0;
  padding-right: 0;
  overflow: hidden;
}
</style>