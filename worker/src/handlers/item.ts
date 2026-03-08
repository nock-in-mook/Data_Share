// データ取得API
import { Env, ItemData } from '../types';

export async function handleGetItem(id: string, env: Env, raw: boolean): Promise<Response> {
  const data = await env.KV.get(`item:${id}`);
  if (!data) {
    if (raw) {
      return new Response('Not Found', { status: 404 });
    }
    return jsonResponse({ ok: false, error: 'not_found' }, 404);
  }

  const item: ItemData = JSON.parse(data);

  // /api/item/:id/raw → バイナリデータ直接返却（画像用）
  if (raw) {
    if (item.type === 'text') {
      return new Response(item.content, {
        headers: { 'Content-Type': 'text/plain; charset=utf-8' },
      });
    }
    // 画像: R2から取得
    if (!env.R2 || !item.r2Key) {
      return new Response('画像データなし', { status: 404 });
    }
    const obj = await env.R2.get(item.r2Key);
    if (!obj) {
      return new Response('画像データなし', { status: 404 });
    }
    return new Response(obj.body, {
      headers: {
        'Content-Type': item.mimeType || 'application/octet-stream',
        'Cache-Control': 'private, max-age=300',
      },
    });
  }

  // JSON レスポンス
  if (item.type === 'text') {
    return jsonResponse({ ok: true, type: 'text', content: item.content, createdAt: item.createdAt });
  }
  return jsonResponse({
    ok: true,
    type: item.type,
    mimeType: item.mimeType,
    fileName: item.fileName,
    rawUrl: `/api/item/${id}/raw`,
    createdAt: item.createdAt,
  });
}

function jsonResponse(data: unknown, status = 200): Response {
  return new Response(JSON.stringify(data), {
    status,
    headers: { 'Content-Type': 'application/json; charset=utf-8' },
  });
}
