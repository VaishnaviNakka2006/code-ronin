import { supabase } from '$lib/supabaseClient';

const API_BASE =
    import.meta.env.VITE_API_URL || 'http://localhost:8000';

export async function getBattleRoom(roomId: string) {
    const session = await supabase.auth.getSession();

    const token = session.data.session?.access_token;

    const res = await fetch(
        `${API_BASE}/battle/room/${roomId}`,
        {
            headers: {
                Authorization: `Bearer ${token}`
            }
        }
    );

    if (!res.ok) {
        throw new Error('Room not found');
    }

    return res.json();
}