let voiceState = 'idle';
let mediaRecorder = null;
let audioChunks = [];

function resetVoice() {
  voiceState = 'idle';
  const btn = document.getElementById('btn-voice');
  btn.textContent = 'Start recording';
  btn.style.background = '';
  btn.disabled = false;
  document.getElementById('voice-visual').innerHTML =
    '<div class="big-icon">🎤</div><div class="visual-label">Ready to record</div>';
  document.getElementById('voice-progress-wrap').style.display = 'none';
  document.getElementById('voice-progress').style.width = '0%';
}

document.getElementById('btn-voice').addEventListener('click', async () => {
  if (voiceState === 'idle') {
    try {
      const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
      audioChunks = [];
      mediaRecorder = new MediaRecorder(stream);
      mediaRecorder.ondataavailable = e => audioChunks.push(e.data);
      mediaRecorder.start();
      voiceState = 'recording';
      const btn = document.getElementById('btn-voice');
      btn.textContent = 'Stop & analyse';
      btn.style.background = 'var(--red)';
      document.getElementById('voice-progress-wrap').style.display = 'block';
      document.getElementById('voice-visual').innerHTML = `
        <div class="recording-ring"><div class="recording-dot"></div></div>
        <div class="waveform">
          <div class="wave-bar"></div><div class="wave-bar"></div>
          <div class="wave-bar"></div><div class="wave-bar"></div>
          <div class="wave-bar"></div><div class="wave-bar"></div>
          <div class="wave-bar"></div><div class="wave-bar"></div>
          <div class="wave-bar"></div>
        </div>
        <div class="visual-label" style="color:var(--red)">Recording — say "aaah"</div>`;
      let pct = 0;
      mediaRecorder._prog = setInterval(() => {
        pct = Math.min(pct + 1.2, 100);
        document.getElementById('voice-progress').style.width = pct + '%';
      }, 100);
    } catch(e) {
      showToast('Microphone access denied: ' + e.message);
    }

  } else if (voiceState === 'recording') {
    clearInterval(mediaRecorder._prog);
    voiceState = 'analysing';
    const btn = document.getElementById('btn-voice');
    btn.textContent = 'Analysing...';
    btn.disabled = true;
    document.getElementById('voice-visual').innerHTML =
      '<div class="spinner"></div><div class="visual-label">Analysing voice patterns...</div>';
    mediaRecorder.stop();
    mediaRecorder.stream.getTracks().forEach(t => t.stop());
    mediaRecorder.onstop = async () => {
      const blob = new Blob(audioChunks, { type: 'audio/wav' });
      try {
        const data = await apiPredictVoice(blob);
        scores.voice = data.probability;
      } catch(e) {
        showToast('Voice API error — skipping');
        scores.voice = null;
      }
      showScreen('tremor');
    };
  }
});

document.getElementById('btn-voice-skip').addEventListener('click', () => {
  scores.voice = null;
  showScreen('tremor');
});