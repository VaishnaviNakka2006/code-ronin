import { Howl } from 'howler';

class SoundManager {
  private sounds: Record<string, Howl> = {};
  private ambient: Howl | null = null;
  
  init() {
    this.sounds = {
      correct: new Howl({ src: ['/sounds/correct.mp3'], volume: 0.5 }),
      error: new Howl({ src: ['/sounds/error.mp3'], volume: 0.6 }),
      levelup: new Howl({ src: ['/sounds/levelup.mp3'], volume: 0.7 }),
      bossHit: new Howl({ src: ['/sounds/boss_hit.mp3'], volume: 0.4 }),
      bossDefeat: new Howl({ src: ['/sounds/boss_defeat.mp3'], volume: 0.8 }),
      hover: new Howl({ src: ['/sounds/hover.mp3'], volume: 0.2 }),
      click: new Howl({ src: ['/sounds/click.mp3'], volume: 0.3 }),
    };
    
    this.ambient = new Howl({
      src: ['/sounds/ambient.mp3'],
      loop: true,
      volume: 0.2,
      autoplay: true
    });
  }
  
  play(name: keyof typeof this.sounds) {
    this.sounds[name]?.play();
  }
  
  setAmbientVolume(vol: number) {
    this.ambient?.volume(vol);
  }
}

export const sound = new SoundManager();