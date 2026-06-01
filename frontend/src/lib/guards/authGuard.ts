import { supabase } from '$lib/supabaseClient';
import { goto } from '$app/navigation';
import { user } from '$lib/stores/userStore';

export async function requireAuth() {

  const { data } = await supabase.auth.getSession();

  if (!data.session) {
    goto('/login');
    return false;
  }

  const authUser = data.session.user;

  let { data: profile, error } =
    await supabase
      .from('profiles')
      .select('*')
      .eq('id', authUser.id)
      .maybeSingle();

  console.log('PROFILE LOAD:', profile);
  console.log('PROFILE ERROR:', error);

  if (!profile) {

    console.log('NO PROFILE FOUND - CREATING');

    const username =
      authUser.user_metadata?.full_name ||
      authUser.email?.split('@')[0] ||
      'Player';

    const { data: newProfile, error: insertError } =
      await supabase
        .from('profiles')
        .insert({
          id: authUser.id,
          username,
          xp: 0,
          rank: 'Scavenger',
          streak_days: 0
        })
        .select()
        .single();

    console.log('PROFILE CREATE RESULT:', newProfile);
    console.log('PROFILE CREATE ERROR:', insertError);

    profile = newProfile;
  }

  if (profile) {
    user.set({
      id: profile.id,
      username: profile.username,
      xp: profile.xp,
      rank: profile.rank,
      streak: profile.streak_days
    });
  }

  return true;
}