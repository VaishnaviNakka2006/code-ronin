import { supabase } from '$lib/supabaseClient';

const API_BASE = import.meta.env.VITE_API_URL || 'http://localhost:8000';

export async function generateAIMission(
  params: {
    difficulty: string;
    topic?: string;
    adaptive?: boolean;
  }
) {

  const session =
    await supabase.auth.getSession();

  const token =
    session.data.session?.access_token;

  const url = new URL(
    `${API_BASE}/missions/generate-ai`
  );

  url.searchParams.set(
    'difficulty',
    params.difficulty
  );

  if (params.topic) {
    url.searchParams.set(
      'topic',
      params.topic
    );
  }

  if (params.adaptive) {
    url.searchParams.set(
      'adaptive',
      'true'
    );
  }

  const res = await fetch(
    url.toString(),
    {
      method: 'POST',
      headers: {
        Authorization: `Bearer ${token}`
      }
    }
  );

  if (!res.ok) {
    throw new Error(
      'Failed to generate mission'
    );
  }

  return res.json();
}

export async function submitAIMission(mission: any, code: string) {
  const session = await supabase.auth.getSession();
  const token = session.data.session?.access_token;
  const res = await fetch(`${API_BASE}/missions/ai/submit`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      Authorization: `Bearer ${token}`
    },
    body: JSON.stringify({ mission, code })
  });
  if (!res.ok) throw new Error('Submission failed');
  return res.json();
}