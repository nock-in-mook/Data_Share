// Slack Webhook 通知
import { Env, ItemData } from '../types';

const BASE_URL = 'https://data-share.yagukyou.workers.dev';

export async function notifySlack(env: Env, id: string, item: ItemData): Promise<void> {
  if (!env.SLACK_WEBHOOK_URL) return;

  let text: string;
  switch (item.type) {
    case 'text':
      text = `📝 テキストが送信されました\n>${(item.content || '').slice(0, 200)}`;
      break;
    case 'image':
      text = `🖼️ 画像が送信されました: ${item.fileName || '画像'}\n${BASE_URL}/view/${id}`;
      break;
    case 'file':
      text = `📎 ファイルが送信されました: ${item.fileName || 'ファイル'}\n${BASE_URL}/view/${id}`;
      break;
  }

  try {
    await fetch(env.SLACK_WEBHOOK_URL, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ text }),
    });
  } catch {
    // 通知失敗はログのみ、アップロードには影響させない
    console.error('Slack通知の送信に失敗');
  }
}
