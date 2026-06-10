import { supabase } from '$lib/supabaseClient';
import type { Achievement } from '$lib/types/achievement';

const API_BASE = import.meta.env.VITE_API_URL || 'https://code-ronin.onrender.com';

export async function fetchAchievements(): Promise<Achievement[]> {
  const session = await supabase.auth.getSession();

  const token = session.data.session?.access_token;

  const res = await fetch(`${API_BASE}/achievements/`, {
    headers: {
      Authorization: `Bearer ${token}`
    }
  });

  if (!res.ok) {
    throw new Error('Failed to fetch achievements');
  }

  return res.json();
}