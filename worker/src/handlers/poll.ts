// ポーリングAPI: 最新アイテムの確認
import { Env, LatestItem } from '../types';

export async function handlePoll(env: Env, request: Request): Promise<Response> {
  // クライアントが前回見た ID を送ってきたら差分判定に使う
  const url = new URL(request.url);
  const lastSeenId = url.searchParams.get('lastId') || '';

  const raw = await env.KV.get('latest');
  if (!raw) {
    return jsonResponse({ hasNew: false });
  }

  const latest: LatestItem = JSON.parse(raw);

  // 前回と同じ ID なら「新着なし」
  if (latest.id === lastSeenId) {
    return jsonResponse({ hasNew: false });
  }

  return jsonResponse({
    hasNew: true,
    id: latest.id,
    type: latest.type,
    preview: latest.preview,
    createdAt: latest.createdAt,
  });
}

function jsonResponse(data: unknown): Response {
  return new Response(JSON.stringify(data), {
    headers: {
      'Content-Type': 'application/json; charset=utf-8',
      'Cache-Control': 'no-cache',
    },
  });
}
