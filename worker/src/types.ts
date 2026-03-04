// Cloudflare Workers バインディング
export interface Env {
  KV: KVNamespace;
  R2?: R2Bucket;
}

// KV に保存するアイテムデータ
export interface ItemData {
  type: 'text' | 'image';
  content?: string;       // テキストの場合
  r2Key?: string;         // 画像の場合
  mimeType?: string;      // 画像の場合
  fileName?: string;      // 画像の元ファイル名
  createdAt: number;
}

// ポーリング用の最新アイテム情報
export interface LatestItem {
  id: string;
  type: 'text' | 'image';
  preview: string;        // テキスト先頭50文字 or ファイル名
  createdAt: number;
}

// アップロードレスポンス
export interface UploadResponse {
  ok: boolean;
  id?: string;
  url?: string;
  error?: string;
}
