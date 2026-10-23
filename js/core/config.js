window.G = window.G || {};

const configuredRuntimeBase = typeof window.ORIGINS_RUNTIME_BASE_URL === 'string'
  ? window.ORIGINS_RUNTIME_BASE_URL.trim()
  : '';

const debugEnabled = new URLSearchParams(window.location.search).get('debug') === '1';

G.Config = Object.freeze({
  viewWidth: 768,
  minViewHeight: 420,
  maxDpr: 1.5,
  maxDelta: 1 / 30,
  playerSpeed: 150,
  cameraFollow: 12,
  mirCellWidth: 48,
  mirCellHeight: 32,
  runtimeBaseUrl: configuredRuntimeBase,
  debug: debugEnabled
});

G.runtimeAssetUrl = function runtimeAssetUrl(path) {
  if (!path || !G.Config.runtimeBaseUrl) return null;

  const base = G.Config.runtimeBaseUrl.endsWith('/')
    ? G.Config.runtimeBaseUrl
    : `${G.Config.runtimeBaseUrl}/`;
  const absoluteBase = new URL(base, document.baseURI);
  return new URL(String(path).replace(/^\/+/, ''), absoluteBase).href;
};
