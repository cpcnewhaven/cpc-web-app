(function () {
  const audio = new Audio();
  let playerEl = null;
  let currentUrl = null;

  function getPlayer() {
    if (!playerEl) playerEl = document.getElementById('cpc-player');
    return playerEl;
  }

  window.playEpisode = function (title, audioUrl, imageUrl, subtitle) {
    if (!audioUrl) return;
    const player = getPlayer();
    if (!player) return;

    if (currentUrl !== audioUrl) {
      audio.src = audioUrl;
      audio.load();
      currentUrl = audioUrl;
    }
    audio.play();

    player.querySelector('#cpc-player-title').textContent = title || 'Now Playing';
    player.querySelector('#cpc-player-subtitle').textContent = subtitle || '';

    const img = player.querySelector('#cpc-player-img');
    if (imageUrl) {
      img.src = imageUrl;
      img.style.display = 'block';
    } else {
      img.style.display = 'none';
    }

    player.classList.add('active');
    document.body.classList.add('player-open');
    updateBtn();
  };

  function updateBtn() {
    const btn = document.querySelector('#cpc-player-playpause');
    if (!btn) return;
    btn.innerHTML = audio.paused
      ? '<i class="fas fa-play"></i>'
      : '<i class="fas fa-pause"></i>';
  }

  function fmt(s) {
    if (!isFinite(s) || s < 0) return '0:00';
    const m = Math.floor(s / 60);
    const sec = Math.floor(s % 60).toString().padStart(2, '0');
    return `${m}:${sec}`;
  }

  document.addEventListener('DOMContentLoaded', function () {
    const player = getPlayer();
    if (!player) return;

    const playpause = player.querySelector('#cpc-player-playpause');
    const scrubber  = player.querySelector('#cpc-player-scrubber');
    const elapsed   = player.querySelector('#cpc-player-elapsed');
    const duration  = player.querySelector('#cpc-player-duration');
    const closeBtn  = player.querySelector('#cpc-player-close');

    playpause?.addEventListener('click', () => {
      audio.paused ? audio.play() : audio.pause();
    });

    audio.addEventListener('play', updateBtn);
    audio.addEventListener('pause', updateBtn);
    audio.addEventListener('ended', updateBtn);

    audio.addEventListener('timeupdate', () => {
      if (!audio.duration) return;
      const pct = (audio.currentTime / audio.duration) * 100;
      scrubber.value = pct;
      // Update scrubber fill via CSS variable
      scrubber.style.setProperty('--pct', pct + '%');
      elapsed.textContent = fmt(audio.currentTime);
    });

    audio.addEventListener('durationchange', () => {
      duration.textContent = fmt(audio.duration);
    });

    scrubber?.addEventListener('input', () => {
      if (audio.duration) {
        audio.currentTime = (scrubber.value / 100) * audio.duration;
      }
    });

    closeBtn?.addEventListener('click', () => {
      audio.pause();
      player.classList.remove('active');
      document.body.classList.remove('player-open');
    });
  });
})();
