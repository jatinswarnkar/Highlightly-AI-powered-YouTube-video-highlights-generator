/**
 * Vanilla JavaScript implementation of Aceternity UI's Dotted Glow Background
 */
class DottedGlowBackground {
  constructor(canvas, options = {}) {
    this.canvas = canvas;
    this.ctx = canvas.getContext('2d');

    // Props from Aceternity component
    this.gap = options.gap || 14;
    this.radius = options.radius || 1.25;
    this.dotColor = options.color || 'rgba(255, 255, 255, 0.4)';
    this.glowColor = options.glowColor || 'rgba(99, 102, 241, 0.8)'; // Indigo 500
    this.opacity = options.opacity || 1;
    this.speedMin = options.speedMin || 0.3;
    this.speedMax = options.speedMax || 1.6;
    this.speedScale = options.speedScale || 1;

    this.dots = [];
    this.animationFrameId = null;

    this.resizeHandler = this.resize.bind(this);
    window.addEventListener('resize', this.resizeHandler);
    
    // Initial setup
    this.resize();
  }

  resize() {
    const parent = this.canvas.parentElement;
    // Set actual canvas resolution to match pixel density
    const dpr = window.devicePixelRatio || 1;
    this.canvas.width = parent.clientWidth * dpr;
    this.canvas.height = parent.clientHeight * dpr;
    
    // Set visual size
    this.canvas.style.width = `${parent.clientWidth}px`;
    this.canvas.style.height = `${parent.clientHeight}px`;
    
    this.ctx.scale(dpr, dpr);
    this.initDots();
  }

  initDots() {
    this.dots = [];
    const width = this.canvas.clientWidth;
    const height = this.canvas.clientHeight;

    const cols = Math.ceil(width / this.gap);
    const rows = Math.ceil(height / this.gap);

    for (let i = 0; i <= cols; i++) {
        for (let j = 0; j <= rows; j++) {
            // Add some jitter to speeds
            const speed = (Math.random() * (this.speedMax - this.speedMin) + this.speedMin) * this.speedScale * 0.02;
            this.dots.push({
                x: i * this.gap,
                y: j * this.gap,
                phase: Math.random() * Math.PI * 2,
                speed: speed,
                baseOpacity: Math.random() * 0.3 + 0.1
            });
        }
    }

    if (!this.animationFrameId) {
        this.animate();
    }
  }

  animate() {
    const width = this.canvas.clientWidth;
    const height = this.canvas.clientHeight;
    
    this.ctx.clearRect(0, 0, width, height);

    // Create central mask / glow effect 
    const cx = width / 2;
    const cy = height / 2;

    for (const dot of this.dots) {
        dot.phase += dot.speed;
        
        // Calculate distance from center for radial mask
        const dx = dot.x - cx;
        const dy = dot.y - cy;
        const dist = Math.sqrt(dx * dx + dy * dy);
        const maxDist = Math.max(width, height) / 1.5;
        
        // Edge fade mask (like Aceternity's mask-image)
        const mask = Math.max(0, 1 - (dist / maxDist));
        
        // Pulsing opacity
        const pulse = (Math.sin(dot.phase) + 1) / 2; // 0 to 1
        const currentOpacity = (dot.baseOpacity + pulse * 0.5) * this.opacity * mask;

        this.ctx.beginPath();
        this.ctx.arc(dot.x, dot.y, this.radius, 0, Math.PI * 2);
        
        this.ctx.fillStyle = this.dotColor;
        this.ctx.globalAlpha = currentOpacity;
        
        // Add glow to brighter dots
        if (currentOpacity > 0.4) {
             this.ctx.shadowBlur = 8;
             this.ctx.shadowColor = this.glowColor;
         } else {
             this.ctx.shadowBlur = 0;
         }
        
        this.ctx.fill();
    }
    
    // Reset global composite and alpha
    this.ctx.globalAlpha = 1;
    this.ctx.shadowBlur = 0;

    this.animationFrameId = requestAnimationFrame(this.animate.bind(this));
  }

  destroy() {
    window.removeEventListener('resize', this.resizeHandler);
    if (this.animationFrameId) {
        cancelAnimationFrame(this.animationFrameId);
    }
  }
}

// Initialize on DOM load
document.addEventListener('DOMContentLoaded', () => {
    const canvas = document.getElementById('dotted-glow-canvas');
    if (canvas) {
        new DottedGlowBackground(canvas, {
            gap: 20,
            radius: 1.5,
            color: 'rgba(255, 255, 255, 0.5)',
            glowColor: 'rgba(99, 102, 241, 1)', // Indigo Glow
            speedMin: 0.3,
            speedMax: 1.6
        });
    }
});
