import { defineStore } from 'pinia';

interface BeatStore {
  beatTimes: number[];
}

export const useBeatsStore = defineStore('beats', {
  state: (): BeatStore => ({
    beatTimes: [0, 5, 10, 15, 20],
  }),

  actions: {
    setBeatTimes(times: number[]) {
      this.beatTimes = times;
    },
    addBeatTime(time: number) {
      this.beatTimes.push(time);
      this.beatTimes.sort((a, b) => a - b);
    },
    removeBeatTime(time: number) {
      this.beatTimes = this.beatTimes.filter(t => t !== time);
    },
  },
}); 