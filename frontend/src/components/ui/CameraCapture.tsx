import { useEffect, useRef, useState } from "react";
import { Camera, X } from "lucide-react";
import type { Translations } from "../../i18n";

interface CameraCaptureProps {
  t: Translations;
  onCapture: (file: File) => void;
  disabled?: boolean;
}

export function CameraCapture({ t, onCapture, disabled }: CameraCaptureProps) {
  const videoRef = useRef<HTMLVideoElement>(null);
  const streamRef = useRef<MediaStream | null>(null);
  const fallbackRef = useRef<HTMLInputElement>(null);
  const [open, setOpen] = useState(false);

  const stopStream = () => {
    streamRef.current?.getTracks().forEach((track) => track.stop());
    streamRef.current = null;
  };

  useEffect(() => () => stopStream(), []);

  const openCamera = async () => {
    if (disabled) return;

    if (!navigator.mediaDevices?.getUserMedia) {
      fallbackRef.current?.click();
      return;
    }

    try {
      const stream = await navigator.mediaDevices.getUserMedia({
        video: { facingMode: { ideal: "environment" } },
        audio: false,
      });
      streamRef.current = stream;
      setOpen(true);
      requestAnimationFrame(() => {
        if (videoRef.current) {
          videoRef.current.srcObject = stream;
          void videoRef.current.play();
        }
      });
    } catch {
      fallbackRef.current?.click();
    }
  };

  const closeCamera = () => {
    stopStream();
    setOpen(false);
  };

  const takePhoto = () => {
    const video = videoRef.current;
    if (!video) return;

    const canvas = document.createElement("canvas");
    canvas.width = video.videoWidth || 1280;
    canvas.height = video.videoHeight || 720;
    const ctx = canvas.getContext("2d");
    if (!ctx) return;

    ctx.drawImage(video, 0, 0, canvas.width, canvas.height);
    canvas.toBlob(
      (blob) => {
        if (!blob) return;
        const file = new File([blob], `photo-${Date.now()}.jpg`, { type: "image/jpeg" });
        onCapture(file);
        closeCamera();
        window.Telegram?.WebApp?.HapticFeedback?.impactOccurred("light");
      },
      "image/jpeg",
      0.92
    );
  };

  return (
    <>
      <button
        type="button"
        onClick={openCamera}
        disabled={disabled}
        className="magnetic-btn text-xs font-medium px-4 py-2.5 rounded-xl border border-borderSubtle bg-surfaceElevated cursor-pointer flex items-center gap-1.5 disabled:opacity-40"
      >
        <Camera className="w-3.5 h-3.5" />
        {t.home_upload_camera}
      </button>

      <input
        ref={fallbackRef}
        type="file"
        accept="image/*"
        capture="environment"
        className="hidden"
        onChange={(e) => {
          const file = e.target.files?.[0];
          if (file) onCapture(file);
          e.target.value = "";
        }}
      />

      {open && (
        <div className="fixed inset-0 z-[100] bg-black flex flex-col">
          <div className="flex items-center justify-between p-4">
            <span className="text-sm text-textPrimary">{t.home_upload_camera}</span>
            <button type="button" onClick={closeCamera} className="p-2 text-textPrimary">
              <X className="w-5 h-5" />
            </button>
          </div>
          <video ref={videoRef} playsInline muted className="flex-1 w-full object-cover" />
          <div className="p-6 flex justify-center">
            <button
              type="button"
              onClick={takePhoto}
              className="w-16 h-16 rounded-full border-4 border-accent bg-accent/20"
              aria-label={t.home_upload_camera}
            />
          </div>
        </div>
      )}
    </>
  );
}
