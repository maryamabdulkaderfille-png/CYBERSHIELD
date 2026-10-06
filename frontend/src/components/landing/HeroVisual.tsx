import { motion } from "framer-motion";

/** One large shield as the single focal point (no icon necklace) — built as
 * layered SVG rather than a scaled-up icon: a blurred offset duplicate for
 * drop-shadow depth, a diagonal brand gradient fill, a clipped glass-highlight
 * sweep, a gradient rim-light stroke, and a glowing checkmark emblem with a
 * few faint circuit traces for a "high-tech" texture. Pure CSS/SVG/Framer
 * Motion — no new dependencies, no raster assets. */
const SHIELD_PATH =
  "M100 8 C100 8 56 24 34 36 L34 108 C34 158 62 194 100 214 C138 194 166 158 166 108 L166 36 C144 24 100 8 100 8 Z";

const DATA_STREAMS = [
  { d: "M -20 60 C 40 20, 120 20, 220 70", delay: 0 },
  { d: "M -10 170 C 60 210, 140 210, 210 150", delay: 1.2 },
];

const PARTICLES = [
  { top: "10%", left: "22%", size: 10, delay: 0 },
  { top: "18%", left: "78%", size: 7, delay: 0.7 },
  { top: "58%", left: "8%", size: 8, delay: 1.4 },
  { top: "85%", left: "26%", size: 6, delay: 0.4 },
  { top: "80%", left: "82%", size: 9, delay: 1.8 },
];

export function HeroVisual() {
  return (
    <div className="relative mx-auto aspect-square w-full max-w-[368px]" aria-hidden="true">
      {/* Ambient background glow — slow breathing, kept but toned down so it
          reads as a refined halo rather than the brightest thing on screen */}
      <motion.div
        className="absolute inset-6 rounded-full bg-gradient-to-br from-brand-blue/20 via-brand-cyan/8 to-transparent blur-3xl"
        animate={{ opacity: [0.4, 0.7, 0.4], scale: [1, 1.05, 1] }}
        transition={{ duration: 6, repeat: Infinity, ease: "easeInOut" }}
      />

      {/* Subtle data streams flowing behind the shield */}
      <svg viewBox="0 0 200 220" className="absolute inset-0 h-full w-full" preserveAspectRatio="xMidYMid meet">
        <defs>
          <linearGradient id="hero-stream-gradient" x1="0" y1="0" x2="1" y2="0">
            <stop offset="0%" stopColor="#3b82f6" stopOpacity="0" />
            <stop offset="50%" stopColor="#22d3ee" stopOpacity="0.55" />
            <stop offset="100%" stopColor="#3b82f6" stopOpacity="0" />
          </linearGradient>
        </defs>
        {DATA_STREAMS.map((stream, i) => (
          <motion.path
            key={i}
            d={stream.d}
            fill="none"
            stroke="url(#hero-stream-gradient)"
            strokeWidth="1.4"
            strokeDasharray="10 14"
            animate={{ strokeDashoffset: [0, -48] }}
            transition={{ duration: 4.5, repeat: Infinity, ease: "linear", delay: stream.delay }}
          />
        ))}
      </svg>

      {/* Two slow pulse rings radiating from the shield */}
      <div className="absolute left-1/2 top-1/2 h-32 w-32 -translate-x-1/2 -translate-y-1/2 animate-pulse-slow rounded-full border border-brand-cyan/18" />
      <div
        className="absolute left-1/2 top-1/2 h-48 w-48 -translate-x-1/2 -translate-y-1/2 animate-pulse-slow rounded-full border border-brand-blue/10"
        style={{ animationDelay: "0.9s" }}
      />

      {/* The shield itself — perspective wrapper + slow tilt gives a gentle
          pseudo-3D "turning in space" feel without any 3D library */}
      <div className="absolute inset-0 flex items-center justify-center" style={{ perspective: 900 }}>
        <motion.div
          initial={{ opacity: 0, scale: 0.82, y: 14 }}
          animate={{
            opacity: 1,
            scale: 1,
            y: [0, -8, 0],
            rotateY: [-7, 7, -7],
            rotateX: [2, -2, 2],
          }}
          transition={{
            opacity: { duration: 0.7, delay: 0.25, ease: "easeOut" },
            scale: { duration: 0.7, delay: 0.25, ease: "easeOut" },
            y: { duration: 6, repeat: Infinity, ease: "easeInOut", delay: 0.9 },
            rotateY: { duration: 9, repeat: Infinity, ease: "easeInOut", delay: 0.9 },
            rotateX: { duration: 9, repeat: Infinity, ease: "easeInOut", delay: 0.9 },
          }}
          className="w-[62%] drop-shadow-[0_30px_60px_rgba(34,211,238,0.18)]"
          style={{ transformStyle: "preserve-3d" }}
        >
          <svg viewBox="0 0 200 220" className="h-full w-full overflow-visible">
            <defs>
              <linearGradient id="hero-shield-fill" x1="0" y1="0" x2="1" y2="1">
                <stop offset="0%" stopColor="#3b82f6" />
                <stop offset="100%" stopColor="#22d3ee" />
              </linearGradient>
              <linearGradient id="hero-shield-rim" x1="0" y1="0" x2="1" y2="1">
                <stop offset="0%" stopColor="#ffffff" stopOpacity="0.9" />
                <stop offset="45%" stopColor="#22d3ee" stopOpacity="0.35" />
                <stop offset="100%" stopColor="#22d3ee" stopOpacity="0" />
              </linearGradient>
              <linearGradient id="hero-shield-gloss" x1="0" y1="0" x2="0.7" y2="1">
                <stop offset="0%" stopColor="#ffffff" stopOpacity="0.55" />
                <stop offset="35%" stopColor="#ffffff" stopOpacity="0.08" />
                <stop offset="60%" stopColor="#ffffff" stopOpacity="0" />
              </linearGradient>
              <clipPath id="hero-shield-clip">
                <path d={SHIELD_PATH} />
              </clipPath>
              <filter id="hero-emblem-glow" x="-50%" y="-50%" width="200%" height="200%">
                <feGaussianBlur stdDeviation="3.2" result="blur" />
                <feMerge>
                  <feMergeNode in="blur" />
                  <feMergeNode in="SourceGraphic" />
                </feMerge>
              </filter>
            </defs>

            {/* Blurred offset duplicate = soft drop-shadow depth beneath the shield */}
            <path d={SHIELD_PATH} fill="#0a0e1a" opacity="0.55" transform="translate(7 12)" style={{ filter: "blur(8px)" }} />

            {/* Main shield body */}
            <path d={SHIELD_PATH} fill="url(#hero-shield-fill)" />

            {/* Faint circuit traces for a high-tech texture, clipped to the shield */}
            <g clipPath="url(#hero-shield-clip)" stroke="#ffffff" strokeOpacity="0.16" strokeWidth="1.2" fill="none">
              <path d="M46 60 H80 V78" />
              <path d="M154 150 H124 V132" />
              <circle cx="80" cy="78" r="2.2" fill="#ffffff" fillOpacity="0.25" stroke="none" />
              <circle cx="124" cy="132" r="2.2" fill="#ffffff" fillOpacity="0.25" stroke="none" />
            </g>

            {/* Glass highlight sweep, clipped to the shield silhouette */}
            <path d={SHIELD_PATH} fill="url(#hero-shield-gloss)" clipPath="url(#hero-shield-clip)" />

            {/* Gradient rim light along the edge */}
            <path d={SHIELD_PATH} fill="none" stroke="url(#hero-shield-rim)" strokeWidth="2.5" />

            {/* Glowing checkmark emblem */}
            <path
              d="M72 116 L93 138 L132 92"
              fill="none"
              stroke="#f8fafc"
              strokeWidth="9"
              strokeLinecap="round"
              strokeLinejoin="round"
              filter="url(#hero-emblem-glow)"
            />
          </svg>
        </motion.div>
      </div>

      {/* Sparse, soft glowing particles — bokeh-style rather than sharp dots */}
      {PARTICLES.map((p, i) => (
        <motion.span
          key={i}
          className="absolute rounded-full bg-brand-cyan/60 blur-[2px]"
          style={{ top: p.top, left: p.left, width: p.size, height: p.size }}
          animate={{ opacity: [0.15, 0.75, 0.15], y: [0, -12, 0] }}
          transition={{ duration: 5 + (i % 3), repeat: Infinity, ease: "easeInOut", delay: p.delay }}
        />
      ))}
    </div>
  );
}
