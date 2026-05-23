import { supabase } from '$lib/supabaseClient';

export async function submitMission(code: string, missionId: number) {
  const session = await supabase.auth.getSession();
  const token = session.data.session?.access_token;

  console.log("TOKEN:", token);

  const res = await fetch(
    `http://127.0.0.1:8000/missions/${missionId}/submit`,
    {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        Authorization: `Bearer ${token}`
      },
      body: JSON.stringify({
        code: code,
        mission_id: missionId
      })
    }
  );

  const data = await res.json();

  console.log("BACKEND RESPONSE:", data);

  if (!res.ok) {
    throw new Error(
      `Submission failed: ${res.status} - ${JSON.stringify(data)}`
    );
  }

  return data;
}