// 閲覧ページ表示
import { Env, ItemData } from '../types';
import { viewerPageHtml, notFoundHtml } from '../templates/viewer';

export async function handleView(id: string, env: Env): Promise<Response> {
  const data = await env.KV.get(`item:${id}`);
  if (!data) {
    return new Response(notFoundHtml(), {
      status: 404,
      headers: { 'Content-Type': 'text/html; charset=utf-8' },
    });
  }

  const item: ItemData = JSON.parse(data);
  return new Response(viewerPageHtml(item, id), {
    headers: { 'Content-Type': 'text/html; charset=utf-8' },
  });
}
