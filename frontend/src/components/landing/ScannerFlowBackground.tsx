import { useEffect, useRef } from "react";

interface Packet {
  x: number;
  y: number;
  angle: number;
  speed: number;
  radius: number;
  progress: number; // 0 (spawned at edge) -> 1 (reached center)
  flagged: boolean; // "threat" packets turn red and get stopped/blocked before the center
  stopAt: number; // progress value at which a flagged packet gets blocked
}

const SAFE_COLOR = "34, 211, 238"; // brand-cyan
const THREAT_COLOR = "239, 68, 68"; // danger red
const SPAWN_INTERVAL_MS = 90;
const MAX_PACKETS = 60;

/** Heavier, system-specific "video-like" background for the scanner
 * showcase — data packets streaming in from every edge toward the trust
 * gauge at the center, most passing through clean (cyan), a minority
 * flagged and visibly blocked partway (red, stops and fades) — a literal
 * depiction of what this section's tabs describe happening, rather than
 * a generic decorative animation. Canvas-drawn, no video asset. */
export function ScannerFlowBackground() {
  const canvasRef = useRef<HTMLCanvasElement>(null);

  useEffect(() => {
    const canvas = canvasRef.current;
    if (!canvas) return;
    const ctx = canvas.getContext("2d");
    if (!ctx) return;

    const reducedMotion = window.matchMedia("(prefers-reduced-motion: reduce)").matches;
    const dpr = Math.min(window.devicePixelRatio || 1, 2);

    let width = 0;
    let height = 0;
    let packets: Packet[] = [];
    let animationFrame = 0;
    let lastSpawn = 0;

    const resize = () => {
      const rect = canvas.getBoundingClientRect();
      width = rect.width;
      height = rect.height;
      canvas.width = width * dpr;
      canvas.height = height * dpr;
      ctx.setTransform(dpr, 0, 0, dpr, 0, 0);
    };

    const spawnPacket = (): Packet => {
      const angle = Math.random() * Math.PI * 2;
      const edgeRadius = Math.max(width, height) * 0.7;
      const flagged = Math.random() < 0.18;
      return {
        x: width / 2 + Math.cos(angle) * edgeRadius,
        y: height / 2 + Math.sin(angle) * edgeRadius,
        angle,
        speed: 0.0035 + Math.random() * 0.003,
        radius: edgeRadius,
        progress: 0,
        flagged,
        stopAt: 0.55 + Math.random() * 0.2,
      };
    };

    const drawStaticFrame = () => {
      ctx.clearRect(0, 0, width, height);
      const cx = width / 2;
      const cy = height / 2;
      // A handful of packets frozen mid-flight for the reduced-motion case.
      for (let i = 0; i < 18; i++) {
        const angle = (i / 18) * Math.PI * 2;
        const progress = 0.3 + (i % 3) * 0.2;
        const edgeRadius = Math.max(width, height) * 0.7;
        const x = cx + Math.cos(angle) * edgeRadius * (1 - progress);
        const y = cy + Math.sin(angle) * edgeRadius * (1 - progress);
        const flagged = i % 5 === 0;
        ctx.fillStyle = `rgba(${flagged ? THREAT_COLOR : SAFE_COLOR}, 0.5)`;
        ctx.beginPath();
        ctx.arc(x, y, 2, 0, Math.PI * 2);
        ctx.fill();
      }
    };

    const step = (timestamp: number) => {
      ctx.clearRect(0, 0, width, height);
      const cx = width / 2;
      const cy = height / 2;

      if (timestamp - lastSpawn > SPAWN_INTERVAL_MS && packets.length < MAX_PACKETS) {
        packets.push(spawnPacket());
        lastSpawn = timestamp;
      }

      packets = packets.filter((packet) => {
        if (packet.flagged && packet.progress >= packet.stopAt) {
          // Blocked: hold position briefly while fading out instead of reaching center.
          packet.progress += packet.speed * 0.15;
          const fade = Math.max(0, 1 - (packet.progress - packet.stopAt) * 6);
          if (fade <= 0) return false;
          const x = cx + Math.cos(packet.angle) * packet.radius * (1 - packet.stopAt);
          const y = cy + Math.sin(packet.angle) * packet.radius * (1 - packet.stopAt);
          ctx.fillStyle = `rgba(${THREAT_COLOR}, ${fade * 0.8})`;
          ctx.beginPath();
          ctx.arc(x, y, 3, 0, Math.PI * 2);
          ctx.fill();
          return true;
        }

        packet.progress += packet.speed;
        if (packet.progress >= 1) return false;

        const x = cx + Math.cos(packet.angle) * packet.radius * (1 - packet.progress);
        const y = cy + Math.sin(packet.angle) * packet.radius * (1 - packet.progress);
        const color = packet.flagged ? THREAT_COLOR : SAFE_COLOR;
        const opacity = 0.75 * (1 - packet.progress * 0.4);

        ctx.fillStyle = `rgba(${color}, ${opacity})`;
        ctx.beginPath();
        ctx.arc(x, y, packet.flagged ? 2.6 : 2, 0, Math.PI * 2);
        ctx.fill();

        // Short trailing tail toward the direction it came from.
        const tailX = cx + Math.cos(packet.angle) * packet.radius * (1 - Math.max(0, packet.progress - 0.04));
        const tailY = cy + Math.sin(packet.angle) * packet.radius * (1 - Math.max(0, packet.progress - 0.04));
        ctx.strokeStyle = `rgba(${color}, ${opacity * 0.4})`;
        ctx.lineWidth = 1;
        ctx.beginPath();
        ctx.moveTo(x, y);
        ctx.lineTo(tailX, tailY);
        ctx.stroke();

        return true;
      });

      animationFrame = requestAnimationFrame(step);
    };

    const handleResize = () => {
      resize();
      if (reducedMotion) drawStaticFrame();
    };

    resize();
    if (reducedMotion) {
      drawStaticFrame();
    } else {
      animationFrame = requestAnimationFrame(step);
    }
    window.addEventListener("resize", handleResize);

    return () => {
      cancelAnimationFrame(animationFrame);
      window.removeEventListener("resize", handleResize);
    };
  }, []);

  return (
    <canvas
      ref={canvasRef}
      aria-hidden="true"
      className="pointer-events-none absolute inset-0 h-full w-full opacity-80"
    />
  );
}
