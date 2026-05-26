export interface Achievement {
  id: number;
  name: string;
  description: string;
  xp_reward: number;
  trigger_type: string;
  icon_name: string;
  unlocked: boolean;
  unlocked_at?: string;
}