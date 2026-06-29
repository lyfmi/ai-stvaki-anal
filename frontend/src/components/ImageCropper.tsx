import { useCallback, useEffect, useRef, useState } from "react";
import { Check, X } from "lucide-react";
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

const MIN_SIZE = 32;
const MAX_IMAGE_HEIGHT = "min(52vh, calc(100dvh - 12rem))";

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
  const cropRef = useRef<CropRect>({ x: 0, y: 0, w: 0, h: 0 });
  const dragRef = useRef<{
    mode: "move" | "draw";
    startX: number;
    startY: number;
    startCrop: CropRect;
    moved: boolean;
  } | null>(null);

  const [src, setSrc] = useState("");
  const [natural, setNatural] = useState({ w: 0, h: 0 });
  const [display, setDisplay] = useState({ w: 0, h: 0 });
  const [crop, setCrop] = useState<CropRect>({ x: 0, y: 0, w: 0, h: 0 });

  useEffect(() => {
    cropRef.current = crop;
  }, [crop]);

  useEffect(() => {
    const url = URL.createObjectURL(file);
    setSrc(url);
    return () => URL.revokeObjectURL(url);
  }, [file]);

  const initCrop = useCallback((dw: number, dh: number) => {
    const margin = 0.08;
    setCrop(
      normalizeRect(
        {
          x: dw * margin,
          y: dh * margin,
          w: dw * (1 - margin * 2),
          h: dh * (1 - margin * 2),
        },
        { w: dw, h: dh }
      )
    );
  }, []);

  const onImageLoad = () => {
    const img = imgRef.current;
    const container = containerRef.current;
    if (!img || !container) return;
    setNatural({ w: img.naturalWidth, h: img.naturalHeight });
    const maxW = container.clientWidth;
    const ratio = img.naturalHeight / img.naturalWidth;
    const dw = maxW;
    const dh = maxW * ratio;
    setDisplay({ w: dw, h: dh });
    initCrop(dw, dh);
  };

  const pointerPos = (e: React.PointerEvent) => {
    const rect = imgRef.current?.getBoundingClientRect();
    if (!rect) return { x: 0, y: 0 };
    return { x: e.clientX - rect.left, y: e.clientY - rect.top };
  };

  const onPointerDown = (e: React.PointerEvent) => {
    e.preventDefault();
    (e.currentTarget as HTMLElement).setPointerCapture(e.pointerId);
    const p = pointerPos(e);
    const current = cropRef.current;
    const canMove = current.w >= MIN_SIZE && insideCrop(p.x, p.y, current);

    dragRef.current = {
      mode: canMove ? "move" : "draw",
      startX: p.x,
      startY: p.y,
      startCrop: current,
      moved: false,
    };

    if (!canMove) {
      setCrop(normalizeRect({ x: p.x, y: p.y, w: MIN_SIZE, h: MIN_SIZE }, display));
    }
  };

  const onPointerMove = (e: React.PointerEvent) => {
    const drag = dragRef.current;
    if (!drag) return;
    const p = pointerPos(e);
    const dx = p.x - drag.startX;
    const dy = p.y - drag.startY;
    if (Math.abs(dx) > 2 || Math.abs(dy) > 2) drag.moved = true;

    if (drag.mode === "move") {
      setCrop(
        normalizeRect(
          {
            x: drag.startCrop.x + dx,
            y: drag.startCrop.y + dy,
            w: drag.startCrop.w,
            h: drag.startCrop.h,
          },
          display
        )
      );
      return;
    }

    const x = Math.min(drag.startX, p.x);
    const y = Math.min(drag.startY, p.y);
    const w = Math.abs(p.x - drag.startX);
    const h = Math.abs(p.y - drag.startY);
    setCrop(normalizeRect({ x, y, w, h }, display));
  };

  const onPointerUp = () => {
    const drag = dragRef.current;
    dragRef.current = null;
    if (!drag) return;
    if (!drag.moved) {
      setCrop(drag.startCrop);
    }
  };

  const handleConfirm = () => {
    const img = imgRef.current;
    if (!img || !natural.w || crop.w < MIN_SIZE || crop.h < MIN_SIZE) return;
    const sx = (crop.x / display.w) * natural.w;
    const sy = (crop.y / display.h) * natural.h;
    const sw = (crop.w / display.w) * natural.w;
    const sh = (crop.h / display.h) * natural.h;

    const canvas = document.createElement("canvas");
    canvas.width = Math.max(1, Math.round(sw));
    canvas.height = Math.max(1, Math.round(sh));
    const ctx = canvas.getContext("2d");
    if (!ctx) return;
    ctx.drawImage(img, sx, sy, sw, sh, 0, 0, canvas.width, canvas.height);

    canvas.toBlob(
      (blob) => {
        if (!blob) return;
        onConfirm(
          new File([blob], file.name.replace(/(\.\w+)?$/, "_crop.jpg"), { type: "image/jpeg" })
        );
      },
      "image/jpeg",
      0.92
    );
  };

  return (
    <div className="fixed inset-0 z-50 grid grid-rows-[auto_auto_1fr_auto] bg-appBg/95 backdrop-blur-md px-4 pt-4 pb-[max(1rem,env(safe-area-inset-bottom))]">
      <div className="flex items-center justify-between">
        <h3 className="text-sm font-semibold text-textPrimary">{t.crop_title}</h3>
        <button type="button" onClick={onCancel} className="p-2 text-textMuted">
          <X className="w-5 h-5" />
        </button>
      </div>

      <p className="text-[11px] text-textMuted mt-2 leading-snug line-clamp-2">{t.crop_hint}</p>

      <div
        ref={containerRef}
        className="min-h-0 flex items-center justify-center overflow-hidden my-2"
      >
        <div
          className="relative select-none touch-none w-full mx-auto"
          style={{ maxWidth: display.w || "100%", maxHeight: MAX_IMAGE_HEIGHT }}
          onPointerDown={onPointerDown}
          onPointerMove={onPointerMove}
          onPointerUp={onPointerUp}
          onPointerCancel={onPointerUp}
        >
          <img
            ref={imgRef}
            src={src}
            alt=""
            className="w-full h-auto block rounded-lg pointer-events-none"
            style={{ maxHeight: MAX_IMAGE_HEIGHT, objectFit: "contain" }}
            onLoad={onImageLoad}
            draggable={false}
          />
          {display.w > 0 && crop.w > 0 && (
            <div
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

      <div className="flex gap-3 shrink-0">
        <button
          type="button"
          onClick={onCancel}
          className="flex-1 py-3 rounded-xl border border-borderSubtle text-textMuted text-sm font-medium"
        >
          {t.crop_cancel}
        </button>
        <button
          type="button"
          onClick={handleConfirm}
          className="flex-1 py-3 rounded-xl bg-accent text-white text-sm font-semibold flex items-center justify-center gap-2"
        >
          <Check className="w-4 h-4" />
          {t.crop_apply}
        </button>
      </div>
    </div>
  );
}
