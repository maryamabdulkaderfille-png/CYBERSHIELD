import { useEffect, useRef } from "react";

interface Node {
  x: number;
  y: number;
  vx: number;
  vy: number;
}

interface Blip {
  x: number;
  y: number;
  age: number; // 0 -> 1
}

const NODE_COLOR = "34, 211, 238";
const THREAT_COLOR = "239, 68, 68";
const LINK_DISTANCE = 170;
const NODE_DENSITY = 9000;
const MAX_NODES = 90;
const BLIP_CHANCE_PER_FRAME = 0.02;
const BLIP_LIFETIME = 60; // frames

/** Heavier "threat map" background for the Threat Intelligence section — a
 * denser node network than the hero's (this section is about aggregating
 * signal across every scan, so the network reads as busier/heavier), plus
 * occasional red pulses at random nodes standing in for a threat being
 * flagged somewhere on the platform. Layers underneath the section's
 * existing radar-sweep gradient rather than replacing it. */
export function ThreatMapBackground() {
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
    let nodes: Node[] = [];
    let blips: Blip[] = [];
    let animationFrame = 0;

    const seedNodes = () => {
      const count = Math.min(MAX_NODES, Math.floor((width * height) / NODE_DENSITY));
      nodes = Array.from({ length: count }, () => ({
        x: Math.random() * width,
        y: Math.random() * height,
        vx: (Math.random() - 0.5) * 0.2,
        vy: (Math.random() - 0.5) * 0.2,
      }));
    };

    const resize = () => {
      const rect = canvas.getBoundingClientRect();
      width = rect.width;
      height = rect.height;
      canvas.width = width * dpr;
      canvas.height = height * dpr;
      ctx.setTransform(dpr, 0, 0, dpr, 0, 0);
      seedNodes();
    };

    const draw = () => {
      ctx.clearRect(0, 0, width, height);

      if (!reducedMotion) {
        for (const node of nodes) {
          node.x += node.vx;
          node.y += node.vy;
          if (node.x < 0 || node.x > width) node.vx *= -1;
          if (node.y < 0 || node.y > height) node.vy *= -1;
        }
        if (Math.random() < BLIP_CHANCE_PER_FRAME && nodes.length > 0) {
          const source = nodes[Math.floor(Math.random() * nodes.length)];
          blips.push({ x: source.x, y: source.y, age: 0 });
        }
        blips = blips.filter((blip) => {
          blip.age += 1;
          return blip.age < BLIP_LIFETIME;
        });
      }

      for (let i = 0; i < nodes.length; i++) {
        for (let j = i + 1; j < nodes.length; j++) {
          const dx = nodes[i].x - nodes[j].x;
          const dy = nodes[i].y - nodes[j].y;
          const distance = Math.sqrt(dx * dx + dy * dy);
          if (distance < LINK_DISTANCE) {
            const opacity = (1 - distance / LINK_DISTANCE) * 0.3;
            ctx.strokeStyle = `rgba(${NODE_COLOR}, ${opacity})`;
            ctx.lineWidth = 1;
            ctx.beginPath();
            ctx.moveTo(nodes[i].x, nodes[i].y);
            ctx.lineTo(nodes[j].x, nodes[j].y);
            ctx.stroke();
          }
        }
      }

      for (const node of nodes) {
        ctx.fillStyle = `rgba(${NODE_COLOR}, 0.55)`;
        ctx.beginPath();
        ctx.arc(node.x, node.y, 1.5, 0, Math.PI * 2);
        ctx.fill();
      }

      for (const blip of blips) {
        const t = blip.age / BLIP_LIFETIME;
        const ringRadius = t * 26;
        ctx.strokeStyle = `rgba(${THREAT_COLOR}, ${(1 - t) * 0.6})`;
        ctx.lineWidth = 1.5;
        ctx.beginPath();
        ctx.arc(blip.x, blip.y, ringRadius, 0, Math.PI * 2);
        ctx.stroke();
        ctx.fillStyle = `rgba(${THREAT_COLOR}, ${(1 - t) * 0.8})`;
        ctx.beginPath();
        ctx.arc(blip.x, blip.y, 2.2, 0, Math.PI * 2);
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
      className="pointer-events-none absolute inset-0 h-full w-full opacity-60"
    />
  );
}
