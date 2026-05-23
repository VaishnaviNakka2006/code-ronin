import { writable } from 'svelte/store';
import { supabase } from '$lib/supabaseClient';
import type { User } from '@supabase/supabase-js';

export const user = writable<User | null>(null);
export const session = writable<any>(null);

export const signInWithGoogle = async () => {
  const { data, error } = await supabase.auth.signInWithOAuth({
    provider: 'google',
    options: {
      redirectTo: 'http://localhost:5173/dashboard'
    }
  });

  if (error) {
    console.error('Google login error:', error);
  }

  return data;
};

export const signInWithDiscord = async () => {
  const { data, error } = await supabase.auth.signInWithOAuth({
    provider: 'discord',
    options: {
      redirectTo: 'http://localhost:5173/dashboard'
    }
  });

  if (error) {
    console.error('Discord login error:', error);
  }

  return data;
};

export const signOut = async () => {
  await supabase.auth.signOut();
};

supabase.auth.onAuthStateChange((event, sess) => {
  console.log('Auth event:', event);

  session.set(sess);
  user.set(sess?.user ?? null);

  if (sess?.user) {
    console.log('Logged in user:', sess.user);
  }
});