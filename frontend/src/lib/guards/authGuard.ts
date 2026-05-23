import { supabase } from '$lib/supabaseClient';
import { goto } from '$app/navigation';

export async function requireAuth() {
  const { data } = await supabase.auth.getSession();

  if (!data.session) {
    goto('/login');
    return false;
  }

  return true;
}