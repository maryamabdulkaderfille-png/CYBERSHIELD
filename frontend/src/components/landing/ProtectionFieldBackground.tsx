import { useEffect, useRef } from "react";

interface OrbitParticle {
  radius: number;
  angle: number;
  speed: number;
  size: number;
}

const COLOR = "34, 211, 238"; // brand-cyan
const PARTICLE_COUNT = 34;

/** Heavier closing-section background — particles orbiting the CTA card in
 * concentric rings, reading as a "protection field" around the final call
 * to action rather than a plain static glow. Canvas-drawn, no video asset. */
export function ProtectionFieldBackground() {
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
    let particles: OrbitParticle[] = [];
    let animationFrame = 0;

    const seedParticles = () => {
      const maxRadius = Math.min(width, height) * 0.55;
      particles = Array.from({ length: PARTICLE_COUNT }, () => ({
        radius: maxRadius * (0.35 + Math.random() * 0.65),
        angle: Math.random() * Math.PI * 2,
        speed: (0.0015 + Math.random() * 0.002) * (Math.random() < 0.5 ? 1 : -1),
        size: 1 + Math.random() * 1.6,
      }));
    };

    const resize = () => {
      const rect = canvas.getBoundingClientRect();
      width = rect.width;
      height = rect.height;
      canvas.width = width * dpr;
      canvas.height = height * dpr;
      ctx.setTransform(dpr, 0, 0, dpr, 0, 0);
      seedParticles();
    };

    const draw = () => {
      ctx.clearRect(0, 0, width, height);
      const cx = width / 2;
      const cy = height / 2;

      for (const ring of [0.35, 0.55, 0.75]) {
        const maxRadius = Math.min(width, height) * 0.55;
        ctx.strokeStyle = `rgba(${COLOR}, 0.08)`;
        ctx.lineWidth = 1;
        ctx.beginPath();
        ctx.arc(cx, cy, maxRadius * ring, 0, Math.PI * 2);
        ctx.stroke();
      }

      for (const particle of particles) {
        if (!reducedMotion) particle.angle += particle.speed;
        const x = cx + Math.cos(particle.angle) * particle.radius;
        const y = cy + Math.sin(particle.angle) * particle.radius * 0.55; // slight ellipse for perspective
        ctx.fillStyle = `rgba(${COLOR}, 0.55)`;
        ctx.beginPath();
        ctx.arc(x, y, particle.size, 0, Math.PI * 2);
        ctx.fill();
      }

      if (!reducedMotion) animationFrame = requestAnimationFrame(draw);
    };

    const handleResize = () => {
      resize();
      if (reducedMotion) draw();
    };

    resize();
    draw();
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
      className="pointer-events-none absolute inset-0 h-full w-full opacity-70"
    />
  );
}
