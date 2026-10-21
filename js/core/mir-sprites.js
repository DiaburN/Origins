window.G = window.G || {};

G.MirSprites = (() => {
  const sets = new Map();

  class SpriteSet {
    constructor(manifest, manifestUrl) {
      this.manifest = manifest;
      this.baseUrl = new URL('.', manifestUrl);
      this.frames = new Map();
      this.atlasPages = new Map();
      this.atlasFrames = new Map();

      const cfg = this.manifest.frames || {};
      if (cfg.mode === 'atlas') {
        if (cfg.rects && typeof cfg.rects === 'object') {
          const multiPage = Array.isArray(cfg.images);
          for (const [logicalFrame, rect] of Object.entries(cfg.rects)) {
            if (!Array.isArray(rect)) continue;

            if (multiPage && rect.length >= 5) {
              this.atlasFrames.set(Number(logicalFrame), {
                page: rect[0],
                x: rect[1],
                y: rect[2],
                w: rect[3],
                h: rect[4]
              });
            } else if (rect.length >= 4) {
              this.atlasFrames.set(Number(logicalFrame), {
                page: 0,
                x: rect[0],
                y: rect[1],
                w: rect[2],
                h: rect[3]
              });
            }
          }
        } else if (Array.isArray(cfg.order)) {
          const cellWidth = cfg.cellWidth || 0;
          const cellHeight = cfg.cellHeight || 0;
          const columns = cfg.columns || 1;
          cfg.order.forEach((logicalFrame, index) => {
            this.atlasFrames.set(logicalFrame, {
              page: 0,
              x: (index % columns) * cellWidth,
              y: Math.floor(index / columns) * cellHeight,
              w: cellWidth,
              h: cellHeight
            });
          });
        }
      }
    }

    frameMode() {
      return (this.manifest.frames && this.manifest.frames.mode) || 'individual';
    }

    frameFile(logicalFrame) {
      const cfg = this.manifest.frames || {};
      const pad = cfg.pad ?? 4;
      const ext = cfg.extension || 'png';
      const dir = cfg.directory || 'frames';
      return `${dir}/${String(logicalFrame).padStart(pad, '0')}.${ext}`;
    }

    frameUrl(logicalFrame) {
      return new URL(this.frameFile(logicalFrame), this.baseUrl).href;
    }

    atlasFrame(logicalFrame) {
      return this.atlasFrames.get(logicalFrame);
    }

    frameOffset(logicalFrame) {
      const key = String(logicalFrame);
      const specific = this.manifest.frameOffsets && this.manifest.frameOffsets[key];
      const fallback = this.manifest.render && this.manifest.render.defaultOffset;
      return specific || fallback || { x: 0, y: 0 };
    }

    sourceFrame(logicalFrame) {
      const source = this.manifest.source || {};
      return (source.frameBase || 0) + logicalFrame;
    }

    atlasPagePath(pageIndex) {
      const cfg = this.manifest.frames || {};
      if (Array.isArray(cfg.images)) return cfg.images[pageIndex] || null;
      return pageIndex === 0 ? (cfg.image || null) : null;
    }

    requestAtlasPage(pageIndex) {
      if (this.atlasPages.has(pageIndex)) return this.atlasPages.get(pageIndex);

      const path = this.atlasPagePath(pageIndex);
      const record = { image: new Image(), state: path ? 'loading' : 'missing' };
      this.atlasPages.set(pageIndex, record);
      if (!path) return record;

      record.image.decoding = 'async';
      record.image.onload = () => { record.state = 'ready'; };
      record.image.onerror = () => { record.state = 'missing'; };
      record.image.src = new URL(path, this.baseUrl).href;
      return record;
    }

    request(logicalFrame) {
      if (this.frameMode() === 'atlas') {
        const frame = this.atlasFrame(logicalFrame);
        if (!frame) return { image: null, state: 'missing' };
        return this.requestAtlasPage(frame.page || 0);
      }

      if (this.frames.has(logicalFrame)) return this.frames.get(logicalFrame);

      const record = { image: new Image(), state: 'loading' };
      record.image.decoding = 'async';
      record.image.onload = () => { record.state = 'ready'; };
      record.image.onerror = () => { record.state = 'missing'; };
      record.image.src = this.frameUrl(logicalFrame);
      this.frames.set(logicalFrame, record);
      return record;
    }

    preloadAction(action, definitions = G.MirPlayerFrames) {
      const def = definitions[action];
      if (!def) return;
      for (let dir = 0; dir < 8; dir++) {
        for (let i = 0; i < def.count; i++) {
          this.request(def.start + def.offset * dir + i);
        }
      }
    }

    draw(ctx, logicalFrame, x, y) {
      const frame = this.frameMode() === 'atlas' ? this.atlasFrame(logicalFrame) : null;
      const record = this.request(logicalFrame);
      if (record.state !== 'ready') return false;

      const offset = this.frameOffset(logicalFrame);
      const scale = (this.manifest.render && this.manifest.render.scale) || 1;
      const dx = Math.round(x + offset.x);
      const dy = Math.round(y + offset.y);

      if (this.frameMode() === 'atlas') {
        if (!frame) return false;
        ctx.drawImage(
          record.image,
          frame.x, frame.y, frame.w, frame.h,
          dx, dy, frame.w * scale, frame.h * scale
        );
        return true;
      }

      if (scale === 1) {
        ctx.drawImage(record.image, dx, dy);
      } else {
        ctx.drawImage(record.image, dx, dy, record.image.width * scale, record.image.height * scale);
      }
      return true;
    }
  }

  async function fetchManifest(url) {
    const response = await fetch(url);
    if (!response.ok) throw new Error(`Unable to load MIR sprite manifest: ${url}`);
    const manifest = await response.json();
    if (!manifest.id || !manifest.frames) throw new Error(`Invalid MIR sprite manifest: ${url}`);
    return { manifest, url: response.url };
  }

  async function resolveManifest(manifestPath) {
    const source = await fetchManifest(manifestPath);
    const runtime = source.manifest.runtime || {};

    if (source.manifest.ready === false && G.Config.runtimeBaseUrl && runtime.root && runtime.manifest) {
      const runtimeUrl = G.runtimeAssetUrl(`${runtime.root}${runtime.manifest}`);
      if (runtimeUrl) {
        try {
          return await fetchManifest(runtimeUrl);
        } catch (runtimeError) {
          console.warn(`MIR runtime unavailable, using source manifest: ${runtimeUrl}`, runtimeError);
        }
      }
    }

    return source;
  }

  async function load(manifestPath) {
    if (sets.has(manifestPath)) return sets.get(manifestPath);

    const promise = resolveManifest(manifestPath).then(
      resolved => new SpriteSet(resolved.manifest, resolved.url)
    );

    sets.set(manifestPath, promise);
    return promise;
  }

  return Object.freeze({ load });
})();
