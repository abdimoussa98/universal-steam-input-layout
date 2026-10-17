// Observe real Web Audio scheduling; keep Chrome's gesture gate and sound graph.
window.demoAudio = {events: [], cancellations: 0};
const NativeAudioContext = window.AudioContext;
window.AudioContext = class extends NativeAudioContext {
  createOscillator() {
    const oscillator = super.createOscillator();
    const start = oscillator.start.bind(oscillator);
    const stop = oscillator.stop.bind(oscillator);
    oscillator.start = time => {
      demoAudio.events.push({time, frequency: oscillator.frequency.value});
      start(time);
    };
    oscillator.stop = time => {
      if (time === undefined) demoAudio.cancellations++;
      stop(time);
    };
    return oscillator;
  }
};
