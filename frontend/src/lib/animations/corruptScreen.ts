export function corruptScreen(
  intensity = 0.5
) {

  const overlay =
    document.createElement('div');

  overlay.style.position =
    'fixed';

  overlay.style.top = '0';
  overlay.style.left = '0';

  overlay.style.width = '100%';
  overlay.style.height = '100%';

  overlay.style.backgroundColor =
    `rgba(255, 0, 255, ${intensity * 0.4})`;

  overlay.style.zIndex = '9998';

  overlay.style.pointerEvents =
    'none';

  overlay.style.mixBlendMode =
    'difference';

  overlay.style.backdropFilter =
    'blur(1px)';

  overlay.style.animation =
    'glitchFlash 150ms ease';

  document.body.appendChild(
    overlay
  );

  setTimeout(() => {
    overlay.remove();
  }, 150);
}