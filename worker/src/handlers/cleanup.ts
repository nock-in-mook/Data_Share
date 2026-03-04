// cron: 期限切れ R2 オブジェクトの削除
import { Env } from '../types';

export async function handleCleanup(env: Env): Promise<void> {
  if (!env.R2) return;

  // cleanup: プレフィックスのキーを列挙
  const list = await env.KV.list({ prefix: 'cleanup:' });

  for (const key of list.keys) {
    const raw = await env.KV.get(key.name);
    if (!raw) continue;

    const { r2Key, createdAt } = JSON.parse(raw) as { r2Key: string; createdAt: number };

    // 5分超過していたら R2 からも削除
    if (Date.now() - createdAt > 300_000) {
      await env.R2.delete(r2Key);
      await env.KV.delete(key.name);
    }
  }
}
