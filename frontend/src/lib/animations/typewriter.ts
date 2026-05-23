export async function typewriter(
  element: HTMLElement,
  text: string,
  speed = 25
) {
  element.textContent = '';

  for (let i = 0; i < text.length; i++) {
    element.textContent += text[i];

    await new Promise((resolve) =>
      setTimeout(resolve, speed)
    );
  }
}