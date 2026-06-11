export async function getAIHint(
  errorMessage: string,
  codeSnippet: string
) {

  try {

    const res = await fetch(
      `${import.meta.env.VITE_API_URL}/ai/hint`,
      {
        method: 'POST',

        headers: {
          'Content-Type':
            'application/json'
        },

        body: JSON.stringify({
          error_message: errorMessage,
          code_snippet: codeSnippet
        })
      }
    );

    return await res.json();

  } catch (err) {

    console.error(err);

    return {
      hint:
        'AI mentor connection failed.'
    };
  }
}