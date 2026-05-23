export const triggerGlitch = (element: HTMLElement) => {
  element.classList.add('animate-glitch');

  setTimeout(() => {
    element.classList.remove('animate-glitch');
  }, 300);
};