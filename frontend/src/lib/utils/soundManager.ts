import { Howl } from 'howler';
import { browser } from '$app/environment';

const DEFAULTS = {
  musicEnabled: true,
  sfxEnabled: true,
  musicVolume: 0.2,
  sfxVolume: 0.5,
};

// Used to prevent double init
let initialized = false;

class SoundManager {
  private sounds: Record<string, Howl> = {};
  private ambient: Howl | null = null;
  private ambientStarted = false;

  // Preferences (only used client‑side)
  private musicEnabled: boolean = DEFAULTS.musicEnabled;
  private sfxEnabled: boolean = DEFAULTS.sfxEnabled;
  private musicVolume: number = DEFAULTS.musicVolume;
  private sfxVolume: number = DEFAULTS.sfxVolume;

  constructor() {
    // We cannot load preferences here because 'browser' is not yet defined at top-level.
    // We'll load them inside init().
  }

  private loadPreferences() {
    if (!browser) return;
    try {
      const stored = localStorage.getItem('code_ronin_sound_prefs');
      if (stored) {
        const prefs = JSON.parse(stored);
        this.musicEnabled = prefs.musicEnabled ?? DEFAULTS.musicEnabled;
        this.sfxEnabled = prefs.sfxEnabled ?? DEFAULTS.sfxEnabled;
        this.musicVolume = prefs.musicVolume ?? DEFAULTS.musicVolume;
        this.sfxVolume = prefs.sfxVolume ?? DEFAULTS.sfxVolume;
        return;
      }
    } catch {}
    // Fallback to defaults
    this.musicEnabled = DEFAULTS.musicEnabled;
    this.sfxEnabled = DEFAULTS.sfxEnabled;
    this.musicVolume = DEFAULTS.musicVolume;
    this.sfxVolume = DEFAULTS.sfxVolume;
  }

  private savePreferences() {
    if (!browser) return;
    localStorage.setItem('code_ronin_sound_prefs', JSON.stringify({
      musicEnabled: this.musicEnabled,
      sfxEnabled: this.sfxEnabled,
      musicVolume: this.musicVolume,
      sfxVolume: this.sfxVolume,
    }));
  }

  init() {
    if (!browser) return;
    if (initialized) return;
    initialized = true;

    this.loadPreferences();

    // Initialize all sound effects with current sfx volume
    this.sounds = {
      correct: new Howl({ src: ['/sounds/correct.mp3'], volume: this.sfxVolume }),
      error: new Howl({ src: ['/sounds/error.mp3'], volume: this.sfxVolume }),
      levelup: new Howl({ src: ['/sounds/levelup.mp3'], volume: this.sfxVolume }),
      bossHit: new Howl({ src: ['/sounds/boss_hit.mp3'], volume: this.sfxVolume }),
      bossDefeat: new Howl({ src: ['/sounds/boss_defeat.mp3'], volume: this.sfxVolume }),
      hover: new Howl({ src: ['/sounds/hover.mp3'], volume: this.sfxVolume * 0.4 }),
      click: new Howl({ src: ['/sounds/click.mp3'], volume: this.sfxVolume * 0.6 }),
      missionStart: new Howl({ src: ['/sounds/intro.mp3'], volume: this.sfxVolume }),
      combo: new Howl({ src: ['/sounds/correct.mp3'], volume: this.sfxVolume * 0.8 }),
      submit: new Howl({ src: ['/sounds/click.mp3'], volume: this.sfxVolume * 0.7 }),
    };

    // Set up ambient music (do NOT autoplay)
    this.ambient = new Howl({
      src: ['/sounds/ambient.mp3'],
      loop: true,
      volume: this.musicVolume,
      autoplay: false,
    });

    // Add one‑time interaction listener to start ambient
    const startAmbient = () => {
      if (!this.ambientStarted && this.musicEnabled && this.ambient) {
        this.ambient.play();
        this.ambientStarted = true;
      }
      document.removeEventListener('click', startAmbient);
      document.removeEventListener('keydown', startAmbient);
      document.removeEventListener('touchstart', startAmbient);
    };

    document.addEventListener('click', startAmbient, { once: true });
    document.addEventListener('keydown', startAmbient, { once: true });
    document.addEventListener('touchstart', startAmbient, { once: true });
  }

  // --- Playback methods ---
  play(name: keyof typeof this.sounds) {
    if (!browser) return;
    if (!this.sfxEnabled) return;
    const sound = this.sounds[name];
    if (sound) {
      // Update volume in case it changed (handles hover/click scaling)
      if (name === 'hover') sound.volume(this.sfxVolume * 0.4);
      else if (name === 'click') sound.volume(this.sfxVolume * 0.6);
      else if (name === 'combo') sound.volume(this.sfxVolume * 0.8);
      else if (name === 'submit') sound.volume(this.sfxVolume * 0.7);
      else sound.volume(this.sfxVolume);
      sound.play();
    }
  }

  // --- Convenience methods ---
  playSuccess() {
    this.play('correct');
  }

  playFailure() {
    this.play('error');
  }

  playSubmit() {
    this.play('submit');
  }

  playMissionStart() {
    this.play('missionStart');
  }

  playCombo() {
    this.play('combo');
  }

  playLevelUp() {
    this.play('levelup');
  }

  // --- Ambient control ---
  startAmbient() {
    if (!browser) return;
    if (!this.ambientStarted && this.musicEnabled && this.ambient) {
      this.ambient.play();
      this.ambientStarted = true;
    }
  }

  stopAmbient() {
    if (!browser) return;
    if (this.ambient) {
      this.ambient.stop();
      this.ambientStarted = false;
    }
  }

  // --- Toggles ---
  toggleMusic() {
    if (!browser) return;
    this.musicEnabled = !this.musicEnabled;
    this.savePreferences();
    if (this.musicEnabled) {
      if (!this.ambientStarted && this.ambient) {
        this.ambient.play();
        this.ambientStarted = true;
      } else if (this.ambient) {
        this.ambient.play();
      }
    } else {
      if (this.ambient) {
        this.ambient.pause();
      }
    }
  }

  toggleSfx() {
    if (!browser) return;
    this.sfxEnabled = !this.sfxEnabled;
    this.savePreferences();
  }

  // --- Volume setters ---
  setMusicVolume(vol: number) {
    if (!browser) return;
    this.musicVolume = Math.min(1, Math.max(0, vol));
    if (this.ambient) {
      this.ambient.volume(this.musicVolume);
    }
    this.savePreferences();
  }

  setSfxVolume(vol: number) {
    if (!browser) return;
    this.sfxVolume = Math.min(1, Math.max(0, vol));
    // Update all existing sounds (volumes with scaling are applied during play)
    // Also update the base volume for Howl objects (they will be overridden on play)
    for (const key in this.sounds) {
      if (key === 'hover') this.sounds[key].volume(this.sfxVolume * 0.4);
      else if (key === 'click') this.sounds[key].volume(this.sfxVolume * 0.6);
      else if (key === 'combo') this.sounds[key].volume(this.sfxVolume * 0.8);
      else if (key === 'submit') this.sounds[key].volume(this.sfxVolume * 0.7);
      else this.sounds[key].volume(this.sfxVolume);
    }
    this.savePreferences();
  }

  // --- Getters (safe for SSR) ---
  getMusicEnabled() { return this.musicEnabled; }
  getSfxEnabled() { return this.sfxEnabled; }
  getMusicVolume() { return this.musicVolume; }
  getSfxVolume() { return this.sfxVolume; }

  // Legacy method (kept for compatibility)
  setAmbientVolume(vol: number) {
    this.setMusicVolume(vol);
  }
}

// Export a singleton instance
export const sound = new SoundManager();