import { useCallback, useEffect, useRef, useState } from "react";
import { createPortal } from "react-dom";
import { Check, Loader2, X } from "lucide-react";
import type { Translations } from "../i18n";

interface ImageCropperProps {
  file: File;
  t: Translations;
  onConfirm: (cropped: File) => void;
  onCancel: () => void;
}

interface CropRect {
  x: number;
  y: number;
  w: number;
  h: number;
}

const MIN_SIZE = 40;
const MIN_CROP_LONG_EDGE = 800;
const CHROME_HEIGHT = 168;

function clamp(value: number, min: number, max: number) {
  return Math.min(max, Math.max(min, value));
}

function normalizeRect(rect: CropRect, bounds: { w: number; h: number }): CropRect {
  const w = clamp(rect.w, MIN_SIZE, bounds.w);
  const h = clamp(rect.h, MIN_SIZE, bounds.h);
  const x = clamp(rect.x, 0, bounds.w - w);
  const y = clamp(rect.y, 0, bounds.h - h);
  return { x, y, w, h };
}

function viewportHeight() {
  const tg = window.Telegram?.WebApp;
  return tg?.viewportStableHeight ?? tg?.viewportHeight ?? window.innerHeight;
}

function getWorkspaceBounds(container: HTMLElement) {
  const vh = viewportHeight();
  const rect = container.getBoundingClientRect();
  const maxW = Math.max(300, rect.width || container.clientWidth || window.innerWidth - 12);
  const measuredH = rect.height > 80 ? rect.height : vh - CHROME_HEIGHT;
  const maxH = Math.max(420, measuredH);
  return { maxW, maxH };
}

/** Maximize image inside workspace; allow upscale for small screenshots. */
function computeDisplaySize(naturalW: number, naturalH: number, maxW: number, maxH: number) {
  const scale = Math.min(maxW / naturalW, maxH / naturalH);
  return {
    w: Math.max(1, Math.round(naturalW * scale)),
    h: Math.max(1, Math.round(naturalH * scale)),
  };
}

export function ImageCropper({ file, t, onConfirm, onCancel }: ImageCropperProps) {
  const containerRef = useRef<HTMLDivElement>(null);
  const imgRef = useRef<HTMLImageElement>(null);
  const overlayRef = useRef<HTMLDivElement>(null);
  const bitmapRef = useRef<ImageBitmap | null>(null);
  const cropRef = useRef<CropRect | null>(null);
  const anchorRef = useRef<{ x: number; y: number } | null>(null);
  const displayRef = useRef({ w: 0, h: 0 });
  const naturalRef = useRef({ w: 0, h: 0 });
  const drawingRef = useRef(false);

  const [src, setSrc] = useState("");
  const [display, setDisplay] = useState({ w: 0, h: 0 });
  const [workspaceH, setWorkspaceH] = useState(0);
  const [hasCrop, setHasCrop] = useState(false);
  const [confirming, setConfirming] = useState(false);

  const updateWorkspaceHeight = useCallback(() => {
    setWorkspaceH(Math.max(420, viewportHeight() - CHROME_HEIGHT));
  }, []);

  const paintOverlay = useCallback((rect: CropRect | null) => {
    const node = overlayRef.current;
    if (!node) return;
    if (!rect || rect.w < MIN_SIZE || rect.h < MIN_SIZE) {
      node.style.display = "none";
      return;
    }
    node.style.display = "block";
    node.style.left = `${rect.x}px`;
    node.style.top = `${rect.y}px`;
    node.style.width = `${rect.w}px`;
    node.style.height = `${rect.h}px`;
  }, []);

  const clearCrop = useCallback(() => {
    cropRef.current = null;
    anchorRef.current = null;
    drawingRef.current = false;
    paintOverlay(null);
    setHasCrop(false);
  }, [paintOverlay]);

  const commitCrop = useCallback(
    (rect: CropRect) => {
      const bounds = displayRef.current;
      const normalized = normalizeRect(rect, bounds);
      cropRef.current = normalized;
      paintOverlay(normalized);
      setHasCrop(true);
    },
    [paintOverlay]
  );

  const measureImage = useCallback(() => {
    const container = containerRef.current;
    const natural = naturalRef.current;
    const img = imgRef.current;
    if (!container || !natural.w || !img) return;

    const { maxW, maxH } = getWorkspaceBounds(container);
    const { w: displayW, h: displayH } = computeDisplaySize(natural.w, natural.h, maxW, maxH);

    img.style.width = `${displayW}px`;
    img.style.height = `${displayH}px`;

    displayRef.current = { w: displayW, h: displayH };
    setDisplay({ w: displayW, h: displayH });
  }, []);

  const handleImageLoad = useCallback(() => {
    measureImage();
    requestAnimationFrame(() => measureImage());
  }, [measureImage]);

  useEffect(() => {
    updateWorkspaceHeight();
    const tg = window.Telegram?.WebApp;
    const onViewport = () => {
      updateWorkspaceHeight();
      requestAnimationFrame(() => measureImage());
    };
    tg?.onEvent?.("viewportChanged", onViewport);
    window.addEventListener("resize", onViewport);
    return () => {
      tg?.offEvent?.("viewportChanged", onViewport);
      window.removeEventListener("resize", onViewport);
    };
  }, [measureImage, updateWorkspaceHeight]);

  useEffect(() => {
    const url = URL.createObjectURL(file);
    setSrc(url);
    clearCrop();

    let cancelled = false;
    void createImageBitmap(file)
      .then((bitmap) => {
        if (cancelled) {
          bitmap.close();
          return;
        }
        bitmapRef.current?.close();
        bitmapRef.current = bitmap;
        naturalRef.current = { w: bitmap.width, h: bitmap.height };
        requestAnimationFrame(() => measureImage());
      })
      .catch(() => undefined);

    return () => {
      cancelled = true;
      URL.revokeObjectURL(url);
      bitmapRef.current?.close();
      bitmapRef.current = null;
    };
  }, [file, clearCrop, measureImage]);

  useEffect(() => {
    const container = containerRef.current;
    if (!container) return;
    const observer = new ResizeObserver(() => measureImage());
    observer.observe(container);
    return () => observer.disconnect();
  }, [src, measureImage, workspaceH]);

  const pointerPos = (e: React.PointerEvent) => {
    const rect = imgRef.current?.getBoundingClientRect();
    if (!rect) return { x: 0, y: 0 };
    return {
      x: clamp(e.clientX - rect.left, 0, rect.width),
      y: clamp(e.clientY - rect.top, 0, rect.height),
    };
  };

  const onPointerDown = (e: React.PointerEvent) => {
    if (confirming) return;
    e.preventDefault();
    (e.currentTarget as HTMLElement).setPointerCapture(e.pointerId);

    const p = pointerPos(e);
    anchorRef.current = p;
    drawingRef.current = true;
    cropRef.current = { x: p.x, y: p.y, w: MIN_SIZE, h: MIN_SIZE };
    paintOverlay(cropRef.current);
    setHasCrop(false);
  };

  const onPointerMove = (e: React.PointerEvent) => {
    if (!drawingRef.current || !anchorRef.current || confirming) return;
    const p = pointerPos(e);
    const anchor = anchorRef.current;
    const bounds = displayRef.current;

    const x = Math.min(anchor.x, p.x);
    const y = Math.min(anchor.y, p.y);
    const w = Math.abs(p.x - anchor.x);
    const h = Math.abs(p.y - anchor.y);

    const next = normalizeRect({ x, y, w: Math.max(w, 1), h: Math.max(h, 1) }, bounds);
    cropRef.current = next;
    paintOverlay(next);
  };

  const onPointerUp = () => {
    if (!drawingRef.current) return;
    drawingRef.current = false;
    const current = cropRef.current;
    if (current && current.w >= MIN_SIZE && current.h >= MIN_SIZE) {
      commitCrop(current);
    } else {
      clearCrop();
    }
    anchorRef.current = null;
  };

  const handleConfirm = async () => {
    const current = cropRef.current;
    const display = displayRef.current;
    const natural = naturalRef.current;
    const bitmap = bitmapRef.current;
    if (!bitmap || !natural.w || !current || current.w < MIN_SIZE || current.h < MIN_SIZE || !display.w) {
      return;
    }

    setConfirming(true);
    try {
      const scaleX = natural.w / display.w;
      const scaleY = natural.h / display.h;
      const sx = Math.round(current.x * scaleX);
      const sy = Math.round(current.y * scaleY);
      const sw = Math.max(1, Math.round(current.w * scaleX));
      const sh = Math.max(1, Math.round(current.h * scaleY));

      let outW = sw;
      let outH = sh;
      const longEdge = Math.max(sw, sh);
      if (longEdge < MIN_CROP_LONG_EDGE) {
        const upscale = MIN_CROP_LONG_EDGE / longEdge;
        outW = Math.max(1, Math.round(sw * upscale));
        outH = Math.max(1, Math.round(sh * upscale));
      }

      const canvas = document.createElement("canvas");
      canvas.width = outW;
      canvas.height = outH;
      const ctx = canvas.getContext("2d");
      if (!ctx) return;

      ctx.imageSmoothingEnabled = true;
      ctx.imageSmoothingQuality = "high";
      ctx.drawImage(bitmap, sx, sy, sw, sh, 0, 0, outW, outH);

      const blob = await new Promise<Blob | null>((resolve) => {
        canvas.toBlob((b) => resolve(b), "image/jpeg", 0.95);
      });
      if (!blob) return;

      onConfirm(new File([blob], file.name.replace(/(\.\w+)?$/, "_crop.jpg"), { type: "image/jpeg" }));
    } finally {
      setConfirming(false);
    }
  };

  const ui = (
    <div className="fixed inset-0 z-[100] flex flex-col bg-appBg">
      <div className="flex items-center justify-between px-4 pt-4 pb-2 shrink-0">
        <h3 className="text-sm font-semibold text-textPrimary">{t.crop_title}</h3>
        <button type="button" onClick={onCancel} className="p-2 text-textMuted" disabled={confirming}>
          <X className="w-5 h-5" />
        </button>
      </div>

      <p className="text-[11px] text-textMuted px-4 leading-snug shrink-0">{t.crop_hint_short}</p>

      <div
        ref={containerRef}
        className="flex-1 min-h-0 flex items-center justify-center px-1 py-1 overflow-hidden"
        style={{ minHeight: workspaceH || undefined }}
      >
        <div
          className="relative select-none touch-none shrink-0"
          style={{
            width: display.w || undefined,
            height: display.h || undefined,
          }}
          onPointerDown={onPointerDown}
          onPointerMove={onPointerMove}
          onPointerUp={onPointerUp}
          onPointerCancel={onPointerUp}
        >
          <img
            ref={imgRef}
            src={src}
            alt=""
            className="block rounded-lg pointer-events-none"
            onLoad={handleImageLoad}
            draggable={false}
          />
          <div
            ref={overlayRef}
            className="absolute border-2 border-accent pointer-events-none hidden"
            style={{ boxShadow: "0 0 0 9999px rgba(0,0,0,0.55)" }}
          />
        </div>
      </div>

      <div className="shrink-0 px-4 pt-2 pb-[max(1rem,env(safe-area-inset-bottom))] flex gap-3 bg-appBg border-t border-borderSubtle/50">
        <button
          type="button"
          onClick={onCancel}
          disabled={confirming}
          className="flex-1 py-3 rounded-xl border border-borderSubtle text-textMuted text-sm font-medium disabled:opacity-50"
        >
          {t.crop_cancel}
        </button>
        <button
          type="button"
          onClick={() => void handleConfirm()}
          disabled={confirming || !hasCrop}
          className="flex-1 py-3 rounded-xl bg-accent text-white text-sm font-semibold flex items-center justify-center gap-2 disabled:opacity-70"
        >
          {confirming ? <Loader2 className="w-4 h-4 animate-spin" /> : <Check className="w-4 h-4" />}
          {confirming ? t.loading : t.crop_apply}
        </button>
      </div>
    </div>
  );

  return createPortal(ui, document.body);
}
