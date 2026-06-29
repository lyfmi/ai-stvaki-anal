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

const MIN_SIZE = 48;
const MAX_IMAGE_HEIGHT = "42dvh";

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

function insideCrop(x: number, y: number, crop: CropRect) {
  return x >= crop.x && x <= crop.x + crop.w && y >= crop.y && y <= crop.y + crop.h;
}

export function ImageCropper({ file, t, onConfirm, onCancel }: ImageCropperProps) {
  const containerRef = useRef<HTMLDivElement>(null);
  const imgRef = useRef<HTMLImageElement>(null);
  const overlayRef = useRef<HTMLDivElement>(null);
  const cropRef = useRef<CropRect>({ x: 0, y: 0, w: 0, h: 0 });
  const displayRef = useRef({ w: 0, h: 0 });
  const naturalRef = useRef({ w: 0, h: 0 });
  const dragRef = useRef<{
    mode: "move" | "draw";
    startX: number;
    startY: number;
    startCrop: CropRect;
    moved: boolean;
  } | null>(null);

  const [src, setSrc] = useState("");
  const [display, setDisplay] = useState({ w: 0, h: 0 });
  const [crop, setCrop] = useState<CropRect>({ x: 0, y: 0, w: 0, h: 0 });
  const [confirming, setConfirming] = useState(false);

  const paintOverlay = useCallback((rect: CropRect) => {
    const node = overlayRef.current;
    if (!node) return;
    node.style.left = `${rect.x}px`;
    node.style.top = `${rect.y}px`;
    node.style.width = `${rect.w}px`;
    node.style.height = `${rect.h}px`;
  }, []);

  const commitCrop = useCallback(
    (rect: CropRect) => {
      cropRef.current = rect;
      paintOverlay(rect);
      setCrop(rect);
    },
    [paintOverlay]
  );

  const measureImage = useCallback(() => {
    const img = imgRef.current;
    if (!img || !img.naturalWidth) return;
    const rect = img.getBoundingClientRect();
    if (rect.width < 1 || rect.height < 1) return;

    naturalRef.current = { w: img.naturalWidth, h: img.naturalHeight };
    displayRef.current = { w: rect.width, h: rect.height };
    setDisplay({ w: rect.width, h: rect.height });

    if (cropRef.current.w < MIN_SIZE) {
      const margin = 0.06;
      commitCrop(
        normalizeRect(
          {
            x: rect.width * margin,
            y: rect.height * margin,
            w: rect.width * (1 - margin * 2),
            h: rect.height * (1 - margin * 2),
          },
          { w: rect.width, h: rect.height }
        )
      );
    }
  }, [commitCrop]);

  useEffect(() => {
    const url = URL.createObjectURL(file);
    setSrc(url);
    return () => URL.revokeObjectURL(url);
  }, [file]);

  useEffect(() => {
    const img = imgRef.current;
    if (!img) return;
    const observer = new ResizeObserver(() => measureImage());
    observer.observe(img);
    return () => observer.disconnect();
  }, [src, measureImage]);

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
    const current = cropRef.current;
    const bounds = displayRef.current;
    const canMove = current.w >= MIN_SIZE && insideCrop(p.x, p.y, current);

    dragRef.current = {
      mode: canMove ? "move" : "draw",
      startX: p.x,
      startY: p.y,
      startCrop: current,
      moved: false,
    };

    if (!canMove) {
      commitCrop(normalizeRect({ x: p.x, y: p.y, w: MIN_SIZE, h: MIN_SIZE }, bounds));
    }
  };

  const onPointerMove = (e: React.PointerEvent) => {
    const drag = dragRef.current;
    if (!drag || confirming) return;
    const p = pointerPos(e);
    const bounds = displayRef.current;
    const dx = p.x - drag.startX;
    const dy = p.y - drag.startY;
    if (Math.abs(dx) > 2 || Math.abs(dy) > 2) drag.moved = true;

    if (drag.mode === "move") {
      const next = normalizeRect(
        {
          x: drag.startCrop.x + dx,
          y: drag.startCrop.y + dy,
          w: drag.startCrop.w,
          h: drag.startCrop.h,
        },
        bounds
      );
      cropRef.current = next;
      paintOverlay(next);
      return;
    }

    const x = Math.min(drag.startX, p.x);
    const y = Math.min(drag.startY, p.y);
    const w = Math.abs(p.x - drag.startX);
    const h = Math.abs(p.y - drag.startY);
    const next = normalizeRect({ x, y, w, h }, bounds);
    cropRef.current = next;
    paintOverlay(next);
  };

  const onPointerUp = () => {
    const drag = dragRef.current;
    dragRef.current = null;
    if (!drag) return;
    if (!drag.moved) {
      commitCrop(drag.startCrop);
      return;
    }
    setCrop(cropRef.current);
  };

  const handleConfirm = () => {
    const img = imgRef.current;
    const current = cropRef.current;
    const natural = naturalRef.current;
    const rect = img?.getBoundingClientRect();
    if (!img || !rect || !natural.w || current.w < MIN_SIZE || current.h < MIN_SIZE) return;

    setConfirming(true);

    const sx = (current.x / rect.width) * natural.w;
    const sy = (current.y / rect.height) * natural.h;
    const sw = (current.w / rect.width) * natural.w;
    const sh = (current.h / rect.height) * natural.h;

    const canvas = document.createElement("canvas");
    canvas.width = Math.max(1, Math.round(sw));
    canvas.height = Math.max(1, Math.round(sh));
    const ctx = canvas.getContext("2d");
    if (!ctx) {
      setConfirming(false);
      return;
    }
    ctx.drawImage(img, sx, sy, sw, sh, 0, 0, canvas.width, canvas.height);

    // #region agent log
    fetch("http://127.0.0.1:7290/ingest/4031f1b2-29d6-4b82-962e-403dc72c5a73", {
      method: "POST",
      headers: { "Content-Type": "application/json", "X-Debug-Session-Id": "328e66" },
      body: JSON.stringify({
        sessionId: "328e66",
        runId: "crop-fix",
        hypothesisId: "H4",
        location: "ImageCropper.tsx:handleConfirm",
        message: "crop export dimensions",
        data: {
          naturalW: natural.w,
          naturalH: natural.h,
          renderW: Math.round(rect.width),
          renderH: Math.round(rect.height),
          outW: canvas.width,
          outH: canvas.height,
          cropPctW: Math.round((sw / natural.w) * 100),
          cropPctH: Math.round((sh / natural.h) * 100),
        },
        timestamp: Date.now(),
      }),
    }).catch(() => {});
    // #endregion

    canvas.toBlob(
      (blob) => {
        setConfirming(false);
        if (!blob) return;
        onConfirm(
          new File([blob], file.name.replace(/(\.\w+)?$/, "_crop.jpg"), { type: "image/jpeg" })
        );
      },
      "image/jpeg",
      0.92
    );
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

      <div ref={containerRef} className="flex-1 min-h-0 flex items-center justify-center px-4 py-2 overflow-hidden">
        <div
          className="relative select-none touch-none"
          style={{
            width: display.w || "100%",
            height: display.h || undefined,
            maxHeight: MAX_IMAGE_HEIGHT,
            maxWidth: "100%",
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
            className="block rounded-lg pointer-events-none w-full h-full object-contain"
            style={{ maxHeight: MAX_IMAGE_HEIGHT }}
            onLoad={measureImage}
            draggable={false}
          />
          {display.w > 0 && crop.w > 0 && (
            <div
              ref={overlayRef}
              className="absolute border-2 border-accent pointer-events-none"
              style={{
                left: crop.x,
                top: crop.y,
                width: crop.w,
                height: crop.h,
                boxShadow: "0 0 0 9999px rgba(0,0,0,0.55)",
              }}
            />
          )}
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
          onClick={handleConfirm}
          disabled={confirming || crop.w < MIN_SIZE}
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
