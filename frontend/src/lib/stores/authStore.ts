import { writable } from 'svelte/store';
console.log('AUTH STORE VERSION 5555');
console.log('AUTH STORE LOADED');

import { supabase } from '$lib/supabaseClient';
import type { User, Session } from '@supabase/supabase-js';

export const user = writable<User | null>(null);
export const session = writable<Session | null>(null);

export const signInWithGoogle = async () => {
  const { data, error } =
    await supabase.auth.signInWithOAuth({
      provider: 'google',
      options: {
        redirectTo: `${window.location.origin}/dashboard`
      }
    });

  if (error) {
    console.error('Google login error:', error);
  }

  return data;
};

export const signInWithDiscord = async () => {
  const { data, error } =
    await supabase.auth.signInWithOAuth({
      provider: 'discord',
      options: {
        redirectTo: `${window.location.origin}/dashboard`
      }
    });

  if (error) {
    console.error('Discord login error:', error);
  }

  return data;
};

export const signOut = async () => {
  await supabase.auth.signOut();

  window.location.href = '/login';
};

supabase.auth.onAuthStateChange(async (event, sess) => {
  console.log('Auth event:', event);

  session.set(sess);
  user.set(sess?.user ?? null);

  if (!sess?.user) {
    return;
  }

  console.log('Logged in user:', sess.user);

  const userId = sess.user.id;

  try {
    const { data: existingProfile, error: profileError } =
      await supabase
        .from('profiles')
        .select('*')
        .eq('id', userId)
        .maybeSingle();

    console.log('PROFILE CHECK:', existingProfile);
    console.log('PROFILE CHECK ERROR:', profileError);

    if (profileError) {
      console.error('PROFILE QUERY FAILED:', profileError);
      return;
    }

    if (!existingProfile) {

      console.log('NO PROFILE FOUND');

      const emailName =
        sess.user.email?.split('@')[0] || 'Player';

      const username =
        `${emailName}_${Math.floor(
          Math.random() * 10000
        )}`;

      console.log('TRYING TO INSERT PROFILE');

      console.log({
        id: userId,
        username,
        xp: 0,
        rank: 'Scavenger',
        streak_days: 0
      });

      const result =
        await supabase
          .from('profiles')
          .insert({
            id: userId,
            username,
            xp: 0,
            rank: 'Scavenger',
            streak_days: 0
          })
          .select();

      console.log('INSERT RESULT:', result);

    } else {
      console.log(
        'Profile already exists'
      );
    }
  } catch (err) {
    console.error(
      'UNEXPECTED PROFILE ERROR:',
      err
    );
  }
});

supabase.auth.getSession().then(({ data }) => {
  session.set(data.session);
  user.set(data.session?.user ?? null);

  console.log(
    'Current session:',
    data.session
  );
});