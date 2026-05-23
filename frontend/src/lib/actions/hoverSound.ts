import { sound } from '$lib/utils/soundManager';

export function hoverSound(node: HTMLElement) {

  const handleMouseEnter = () => {
    sound.play('hover');
  };

  const handleClick = () => {
    sound.play('click');
  };

  node.addEventListener('mouseenter', handleMouseEnter);
  node.addEventListener('click', handleClick);

  return {
    destroy() {
      node.removeEventListener('mouseenter', handleMouseEnter);
      node.removeEventListener('click', handleClick);
    }
  };
}