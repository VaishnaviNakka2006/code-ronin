import { supabase } from '$lib/supabaseClient';

const API_BASE = import.meta.env.VITE_API_URL || 'http://localhost:8000';

export async function generateAIMission(difficulty: string, topic?: string) {
  const session = await supabase.auth.getSession();
  const token = session.data.session?.access_token;
  const url = `${API_BASE}/missions/generate-ai?difficulty=${difficulty}${topic ? `&topic=${topic}` : ''}`;
  const res = await fetch(url, {
    method: 'POST',
    headers: { Authorization: `Bearer ${token}` }
  });
  if (!res.ok) throw new Error('Failed to generate mission');
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