// アップロード処理（テキスト + 画像）
import { Env, ItemData, LatestItem, UploadResponse } from '../types';
import { generateId } from '../utils/id';

const TEXT_MAX = 100 * 1024;   // 100KB
const FILE_MAX = 50 * 1024 * 1024; // 50MB（画像・ファイル共通）
const TTL = 300; // 5分

export async function handleUpload(request: Request, env: Env): Promise<Response> {
  const contentType = request.headers.get('content-type') || '';

  try {
    let item: ItemData;
    let preview: string;
    const id = generateId();

    if (contentType.includes('application/json')) {
      // テキストアップロード
      const body = await request.json() as { type: string; content: string };
      if (body.type !== 'text' || !body.content) {
        return jsonResponse({ ok: false, error: 'テキストが空です' }, 400);
      }
      if (new TextEncoder().encode(body.content).length > TEXT_MAX) {
        return jsonResponse({ ok: false, error: 'テキストが大きすぎます (上限100KB)' }, 400);
      }

      item = {
        type: 'text',
        content: body.content,
        createdAt: Date.now(),
      };
      preview = body.content.slice(0, 50);

    } else if (contentType.includes('multipart/form-data')) {
      // ファイルアップロード（画像・その他ファイル）
      const formData = await request.formData();
      const file = formData.get('file') as File | null;
      if (!file) {
        return jsonResponse({ ok: false, error: 'ファイルが選択されていません' }, 400);
      }
      if (file.size > FILE_MAX) {
        return jsonResponse({ ok: false, error: 'ファイルが大きすぎます (上限50MB)' }, 400);
      }

      // R2に保存
      const r2Key = `uploads/${id}`;
      if (!env.R2) {
        return jsonResponse({ ok: false, error: 'ファイル機能は準備中です' }, 503);
      }
      await env.R2.put(r2Key, file.stream(), {
        httpMetadata: { contentType: file.type || 'application/octet-stream' },
      });

      // 画像かファイルかを判定
      const fileType = file.type.startsWith('image/') ? 'image' as const : 'file' as const;

      item = {
        type: fileType,
        r2Key,
        mimeType: file.type || 'application/octet-stream',
        fileName: file.name,
        createdAt: Date.now(),
      };
      preview = file.name || (fileType === 'image' ? '画像' : 'ファイル');

      // R2クリーンアップ用キー
      await env.KV.put(`cleanup:${id}`, JSON.stringify({ r2Key, createdAt: Date.now() }), {
        expirationTtl: TTL + 60, // 本体より少し長めに残す
      });

    } else {
      return jsonResponse({ ok: false, error: '不正なリクエスト形式です' }, 400);
    }

    // KV にアイテム保存
    await env.KV.put(`item:${id}`, JSON.stringify(item), { expirationTtl: TTL });

    // 最新アイテム情報を更新（ポーリング用）
    const latest: LatestItem = { id, type: item.type, preview, createdAt: item.createdAt };
    await env.KV.put('latest', JSON.stringify(latest), { expirationTtl: TTL });

    const resp: UploadResponse = { ok: true, id, url: `/view/${id}` };
    return jsonResponse(resp);

  } catch (err) {
    const msg = err instanceof Error ? err.message : '不明なエラー';
    return jsonResponse({ ok: false, error: msg }, 500);
  }
}

function jsonResponse(data: unknown, status = 200): Response {
  return new Response(JSON.stringify(data), {
    status,
    headers: { 'Content-Type': 'application/json; charset=utf-8' },
  });
}
