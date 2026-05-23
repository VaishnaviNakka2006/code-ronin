import anime from 'animejs';
export function glitchTransition(
  onComplete: () => void
) {

  const overlay = document.createElement('div');

  overlay.style.position = 'fixed';
  overlay.style.top = '0';
  overlay.style.left = '0';
  overlay.style.width = '100%';
  overlay.style.height = '100%';

  overlay.style.backgroundColor = '#00ffff';

  overlay.style.zIndex = '9999';
  overlay.style.pointerEvents = 'none';

  overlay.style.opacity = '0';

  document.body.appendChild(overlay);

  anime({
    targets: overlay,

    opacity: [0, 1, 1, 0],

    duration: 700,

    easing: 'easeInOutQuad',

    update: (anim) => {

      if (
        anim.progress > 30 &&
        anim.progress < 70
      ) {

        overlay.style.backgroundColor =
          `hsl(${Math.random() * 360}, 100%, 50%)`;

      } else {

        overlay.style.backgroundColor = '#00ffff';
      }
    },

    complete: () => {

      overlay.remove();

      onComplete();
    }
  });
}