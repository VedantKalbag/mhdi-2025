<template>
    <div class="waveforms-container">
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
import { ref, onMounted, onUnmounted } from 'vue';
import Multitrack from 'wavesurfer-multitrack';

interface Track {
    id: number;
    name: string;
    volume: number;
    muted: boolean;
    filename: string;
}

const isPlaying = ref(false);
const zoom = ref(30);
let multitrack: any = null;

const tracks = ref<Track[]>([
    { id: 1, name: 'Vocals', volume: 1, muted: false, filename: 'LIFAFA_Jaago.mp3_vocals.ogg' },
    { id: 2, name: 'Bass', volume: 1, muted: false, filename: 'LIFAFA_Jaago.mp3_bass.ogg' },
    { id: 3, name: 'Drums', volume: 1, muted: false, filename: 'LIFAFA_Jaago.mp3_drums.ogg' },
    { id: 4, name: 'Piano', volume: 1, muted: false, filename: 'LIFAFA_Jaago.mp3_piano.ogg' },
    { id: 5, name: 'Other', volume: 1, muted: false, filename: 'LIFAFA_Jaago.mp3_other.ogg' },
]);

onMounted(() => {
    const trackConfigs = tracks.value.map(track => ({
        id: track.id,
        draggable: false,
        url: `http://localhost:8080/${track.filename}`,
        volume: track.volume,
        options: {
            waveColor: getTrackColor(track.name),
            progressColor: getProgressColor(track.name),
            height: 80,
        },
    }));

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
});

const getTrackColor = (name: string) => {
    const colors = {
        Vocals: 'hsl(46, 87%, 49%)',
        Bass: 'hsl(161, 87%, 49%)',
        Drums: 'hsl(200, 87%, 49%)',
        Piano: 'hsl(270, 87%, 49%)',
        Other: 'hsl(320, 87%, 49%)',
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