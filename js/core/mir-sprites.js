window.G = window.G || {};

G.MirSprites = (() => {
  const sets = new Map();

  class SpriteSet {
    constructor(manifest, manifestUrl) {
      this.manifest = manifest;
      this.baseUrl = new URL('.', manifestUrl);
      this.frames = new Map();
      this.atlas = null;
      this.atlasFrames = new Map();

      const cfg = this.manifest.frames || {};
      if (cfg.mode === 'atlas' && Array.isArray(cfg.order)) {
        const cellWidth = cfg.cellWidth || 0;
        const cellHeight = cfg.cellHeight || 0;
        const columns = cfg.columns || 1;
        cfg.order.forEach((logicalFrame, index) => {
          this.atlasFrames.set(logicalFrame, {
            x: (index % columns) * cellWidth,
            y: Math.floor(index / columns) * cellHeight,
            w: cellWidth,
            h: cellHeight
          });
        });
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

    requestAtlas() {
      if (this.atlas) return this.atlas;

      const cfg = this.manifest.frames || {};
      const image = cfg.image;
      const record = { image: new Image(), state: image ? 'loading' : 'missing' };
      if (!image) {
        this.atlas = record;
        return record;
      }

      record.image.decoding = 'async';
      record.image.onload = () => { record.state = 'ready'; };
      record.image.onerror = () => { record.state = 'missing'; };
      record.image.src = new URL(image, this.baseUrl).href;
      this.atlas = record;
      return record;
    }

    request(logicalFrame) {
      if (this.frameMode() === 'atlas') {
        if (!this.atlasFrame(logicalFrame)) return { image: null, state: 'missing' };
        return this.requestAtlas();
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
      const record = this.request(logicalFrame);
      if (record.state !== 'ready') return false;

      const offset = this.frameOffset(logicalFrame);
      const scale = (this.manifest.render && this.manifest.render.scale) || 1;
      const dx = Math.round(x + offset.x);
      const dy = Math.round(y + offset.y);

      if (this.frameMode() === 'atlas') {
        const frame = this.atlasFrame(logicalFrame);
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

  async function load(manifestPath) {
    if (sets.has(manifestPath)) return sets.get(manifestPath);

    const promise = fetch(manifestPath).then(async response => {
      if (!response.ok) throw new Error(`Unable to load MIR sprite manifest: ${manifestPath}`);
      const manifest = await response.json();
      if (!manifest.id || !manifest.frames) throw new Error(`Invalid MIR sprite manifest: ${manifestPath}`);
      return new SpriteSet(manifest, response.url);
    });

    sets.set(manifestPath, promise);
    return promise;
  }

  return Object.freeze({ load });
})();
