// renderer/src/components/DitherBackground.tsx
import { useEffect, useRef } from "react";

const BAYER: number[][] = [
  [ 0,  8,  2, 10],
  [12,  4, 14,  6],
  [ 3, 11,  1,  9],
  [15,  7, 13,  5],
];

export default function DitherBackground() {
  const canvasRef = useRef<HTMLCanvasElement>(null);

  useEffect(() => {
    const canvas = canvasRef.current;
    if (!canvas) return;
    const ctx = canvas.getContext("2d")!;

    let rafId: number;
    let t = 0;
    let lastFrame = 0;
    const TARGET_FPS = 24;
    const FRAME_INTERVAL = 1000 / TARGET_FPS;
    const SCALE = 2;

    const resize = () => {
      canvas.width = Math.ceil(window.innerWidth / SCALE);
      canvas.height = Math.ceil(window.innerHeight / SCALE);
    };

    resize();
    window.addEventListener("resize", resize);

    const render = (timestamp: number) => {
      rafId = requestAnimationFrame(render);
      if (timestamp - lastFrame < FRAME_INTERVAL) return;
      lastFrame = timestamp;

      t += 0.004;

      const w = canvas.width;
      const h = canvas.height;
      const imageData = ctx.createImageData(w, h);
      const data = imageData.data;

      const breath = Math.sin(t) * 0.5 + 0.5;

      for (let y = 0; y < h; y++) {
        for (let x = 0; x < w; x++) {
          const nx = x / w;
          const ny = y / h;

          const noise =
            Math.sin(nx * 6 + t * 0.8) * Math.cos(ny * 5 - t * 0.6) +
            Math.sin(nx * 12 - t * 0.4) * Math.cos(ny * 10 + t * 0.3) * 0.5;

          const normalized = (noise / 1.5 + 1) / 2;
          const intensity = normalized * (0.2 + breath * 0.2);

          const threshold = BAYER[y % 4][x % 4] / 16;
          const dithered = intensity > threshold ? 1 : 0;

          const idx = (y * w + x) * 4;
          data[idx]     = dithered * 20;
          data[idx + 1] = dithered * 25;
          data[idx + 2] = dithered * 45;
          data[idx + 3] = dithered * 180;
        }
      }

      ctx.putImageData(imageData, 0, 0);
    };

    rafId = requestAnimationFrame(render);

    return () => {
      cancelAnimationFrame(rafId);
      window.removeEventListener("resize", resize);
    };
  }, []);

  return (
    <canvas
      ref={canvasRef}
      className="absolute inset-0 pointer-events-none w-full h-full"
      style={{
        imageRendering: "pixelated",
        mixBlendMode: "screen",
        opacity: 0.6,
      }}
    />
  );
}