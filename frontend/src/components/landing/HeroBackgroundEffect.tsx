import { useEffect, useRef } from "react";

interface Particle {
  x: number;
  y: number;
  vx: number;
  vy: number;
}

const PARTICLE_COLOR = "34, 211, 238"; // brand-cyan, as an rgb triplet for template use
const LINK_DISTANCE = 150;
// Deliberately sparser/dimmer than a typical decorative network effect —
// this sits directly behind the hero's headline and CTA, so it needs to
// read as ambient texture rather than compete with the text for attention.
const PARTICLE_DENSITY = 20000; // one particle per this many px^2 of canvas area
const MAX_PARTICLES = 42;

/** Canvas-drawn particle network — the "moving background" look common on
 * international cybersecurity sites (Cloudflare, CrowdStrike, etc.), used
 * in place of an actual background video since no video asset exists for
 * this project. Purely decorative (aria-hidden, pointer-events-none) and
 * sits behind the hero content. Respects prefers-reduced-motion by drawing
 * one static frame instead of animating. */
export function HeroBackgroundEffect() {
  const canvasRef = useRef<HTMLCanvasElement>(null);

  useEffect(() => {
    const canvas = canvasRef.current;
    if (!canvas) return;
    const ctx = canvas.getContext("2d");
    if (!ctx) return;

    const reducedMotion = window.matchMedia("(prefers-reduced-motion: reduce)").matches;
    const dpr = Math.min(window.devicePixelRatio || 1, 2);

    let particles: Particle[] = [];
    let width = 0;
    let height = 0;
    let animationFrame = 0;

    const seedParticles = () => {
      const count = Math.min(MAX_PARTICLES, Math.floor((width * height) / PARTICLE_DENSITY));
      particles = Array.from({ length: count }, () => ({
        x: Math.random() * width,
        y: Math.random() * height,
        vx: (Math.random() - 0.5) * 0.25,
        vy: (Math.random() - 0.5) * 0.25,
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

      for (const particle of particles) {
        if (!reducedMotion) {
          particle.x += particle.vx;
          particle.y += particle.vy;
          if (particle.x < 0 || particle.x > width) particle.vx *= -1;
          if (particle.y < 0 || particle.y > height) particle.vy *= -1;
        }
      }

      for (let i = 0; i < particles.length; i++) {
        for (let j = i + 1; j < particles.length; j++) {
          const a = particles[i];
          const b = particles[j];
          const dx = a.x - b.x;
          const dy = a.y - b.y;
          const distance = Math.sqrt(dx * dx + dy * dy);
          if (distance < LINK_DISTANCE) {
            const opacity = (1 - distance / LINK_DISTANCE) * 0.2;
            ctx.strokeStyle = `rgba(${PARTICLE_COLOR}, ${opacity})`;
            ctx.lineWidth = 1;
            ctx.beginPath();
            ctx.moveTo(a.x, a.y);
            ctx.lineTo(b.x, b.y);
            ctx.stroke();
          }
        }
      }

      for (const particle of particles) {
        ctx.fillStyle = `rgba(${PARTICLE_COLOR}, 0.4)`;
        ctx.beginPath();
        ctx.arc(particle.x, particle.y, 1.6, 0, Math.PI * 2);
        ctx.fill();
      }

      if (!reducedMotion) {
        animationFrame = requestAnimationFrame(draw);
      }
    };

    const handleResize = () => {
      resize();
      // Reduced-motion draw() doesn't self-schedule another frame, so a
      // layout change needs an explicit repaint to reflect the new size.
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
      className="pointer-events-none absolute inset-0 h-full w-full opacity-35"
    />
  );
}
