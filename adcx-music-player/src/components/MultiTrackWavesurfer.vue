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
                @change="updateZoom"
            />
        </div>

        <div id="multitrack-container" class="multitrack-container"></div>

        <div class="track-controls">
            <div v-for="track in tracks" :key="track.name" class="track-control">
                <span class="track-name">{{ track.name }}</span>
                <v-switch v-model="track.muted" :label="track.muted ? 'Muted' : 'Unmuted'" @change="toggleMute(track)" />
                <v-slider
                    v-model="track.volume"
                    :min="0"
                    :max="1"
                    :step="0.01"
                    @change="updateVolume(track)"
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

interface Track {
    id: number;
    name: string;
    volume: number;
    muted: boolean;
    trackname: string;
    color: string;
}

const isPlaying = ref(false);
const zoom = ref(30);
let multitrack: any = null;

const tracks = ref<Track[]>([
    { id: 1, name: 'Vocals', volume: 1, muted: false, trackname: 'vocals.wav', color: '#0000FF' },
    { id: 2, name: 'Bass', volume: 1, muted: false, trackname: 'bass.wav', color: '#00FF00' },
    { id: 3, name: 'Drums', volume: 1, muted: false, trackname: 'drums.wav', color: '#FF0000' },
    { id: 4, name: 'Piano', volume: 1, muted: false, trackname: 'piano.wav', color: '#FFA500' },
    { id: 5, name: 'Other', volume: 1, muted: false, trackname: 'other.wav', color: '#FFA500' },
    { id: 6, name: 'Guitar', volume: 1, muted: false, trackname: 'guitar.wav', color: '#0000FF' },
]);

const baseUrl = 'http://192.168.243.23:9000/audio/';

const wavesurfers = ref<Multitrack[]>([]);

const initializeMultitrack = () => {
    if (!audioStore.isReady) return;

    const trackConfigs = tracks.value.map(track => ({
        id: track.id,
        draggable: false,
        url: `${baseUrl}${audioStore.audioBasePath}${track.trackname}`,
        volume: track.volume,
        options: {
            waveColor: getTrackColor(track.name),
            progressColor: getProgressColor(track.name),
            height: 60,
        },
    }));

    // Destroy existing multitrack instance
    if (multitrack) {
        multitrack.destroy();
    }

    multitrack = Multitrack.create(trackConfigs, {
        container: document.querySelector('#multitrack-container'),
        minPxPerSec: zoom.value,
        cursorWidth: 2,
        cursorColor: '#D72F21',
        trackBackground: '#2D2D2D',
        trackBorderColor: '#7C7C7C',
    });

    multitrack.on('volume-change', ({ id, volume }) => {
        const track = tracks.value.find(t => t.id === id);
        if (track) {
            track.volume = volume;
        }
    });

    multitrack.once('canplay', () => {
        console.log('Ready to play');
    });

    // Create waveform for each track
    tracks.value.forEach((track) => {
        const container = document.createElement('div');
        container.id = `waveform-${track.name.toLowerCase()}`;
        document.querySelector('.waveforms-container')?.appendChild(container);

        const wavesurfer = Multitrack.create([{
            id: track.id,
            draggable: false,
            url: `${baseUrl}${audioStore.audioBasePath}${track.trackname}`,
            options: {
                waveColor: track.color,
                progressColor: track.color,
                height: 100,
                normalize: true,
            }
        }], {
            container: container,
            minPxPerSec: zoom.value,
        });

        wavesurfers.value.push(wavesurfer);
    });
};

// Check if audioStore.isReady is changed
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

const getTrackColor = (name: string) => {
    const colors = {
        Vocals: 'hsl(46, 87%, 49%)',
        Bass: 'hsl(161, 87%, 49%)',
        Drums: 'hsl(200, 87%, 49%)',
        Piano: 'hsl(270, 87%, 49%)',
        Other: 'hsl(320, 87%, 49%)',
        Guitar: 'hsl(320, 87%, 49%)',
    };
    return colors[name as keyof typeof colors];
};

const getProgressColor = (name: string) => {
    const colors = {
        Vocals: 'hsl(46, 87%, 20%)',
        Bass: 'hsl(161, 87%, 20%)',
        Drums: 'hsl(200, 87%, 20%)',
        Piano: 'hsl(270, 87%, 20%)',
        Other: 'hsl(320, 87%, 20%)',
        Guitar: 'hsl(320, 87%, 20%)',
    };
    return colors[name as keyof typeof colors];
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

const updateVolume = (track: Track) => {
    if (multitrack) {
        multitrack.setTrackVolume(track.id, track.volume);
    }
};

const toggleMute = (track: Track) => {
    if (multitrack) {
        console.log(track.id, track.muted ? 0 : track.volume);
        multitrack.setTrackVolume(track.id, track.muted ? 0 : track.volume);
    }
};

const updateZoom = () => {
    if (multitrack) {
        multitrack.zoom(zoom.value);
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
</style>