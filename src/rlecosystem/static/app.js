// Draws the frames the server pushes over /ws. The world keeps its own size (e.g. 1600x900)
// and is scaled to fit the window. Edges wrap, so things near an edge also show on the other side.

const canvas = document.getElementById("world");
const ctx = canvas.getContext("2d");
const visionButton = document.getElementById("vision");
const speedButton = document.getElementById("speed");
const statsLine = document.getElementById("stats");

const FIELD = "#101a22";
const TYPE_COLORS = ["#4ade80", "#60a5fa", "#f87171"]; // food, blue, red (index = type code)
const NOTHING = 3;

let frame = null;
let showVision = false;
let ws = null;

function connect() {
  ws = new WebSocket(`ws://${location.host}/ws`);
  ws.onmessage = (event) => {
    frame = JSON.parse(event.data);
    updatePanel();
  };
  ws.onclose = () => {
    statsLine.textContent = "disconnected: is the server running? Retrying…";
    setTimeout(connect, 1000);
  };
}

function updatePanel() {
  const s = frame.stats;
  const minutes = Math.floor(s.sim_seconds / 60);
  const seconds = Math.floor(s.sim_seconds % 60).toString().padStart(2, "0");
  statsLine.textContent =
    `simulated ${minutes}m ${seconds}s · ${s.food_per_min.toFixed(1)} food/min per blue · ` +
    `brain updates ${s.updates} · ${s.ticks_per_s} steps/s`;
  speedButton.textContent = s.speed === "fast" ? "Speed: fast-forward" : "Speed: watch";
}

visionButton.onclick = () => {
  showVision = !showVision;
  visionButton.textContent = showVision ? "Vision: on" : "Vision: off";
};

speedButton.onclick = () => {
  if (!frame || ws.readyState !== WebSocket.OPEN) return;
  ws.send(JSON.stringify({ speed: frame.stats.speed === "fast" ? "watch" : "fast" }));
};

function resize() {
  const dpr = window.devicePixelRatio || 1;
  canvas.width = Math.round(window.innerWidth * dpr);
  canvas.height = Math.round(window.innerHeight * dpr);
}

function circle(x, y, r, color) {
  ctx.beginPath();
  ctx.arc(x, y, r, 0, 2 * Math.PI);
  ctx.fillStyle = color;
  ctx.fill();
}

function drawVision(x, y, heading, seen, w) {
  const width = (2 * Math.PI) / w.slices;
  for (let k = 0; k < w.slices; k++) {
    const start = heading + (k - 0.5) * width;
    ctx.beginPath();
    ctx.moveTo(x, y);
    ctx.arc(x, y, w.vision_radius, start, start + width);
    ctx.closePath();
    const [type] = seen[k];
    if (type !== NOTHING) {
      ctx.fillStyle = TYPE_COLORS[type] + "33";
      ctx.fill();
    }
    ctx.strokeStyle = "rgba(216, 222, 228, 0.18)";
    ctx.lineWidth = 1;
    ctx.stroke();
  }
}

function drawBlue(x, y, heading, w) {
  circle(x, y, w.blue_radius, TYPE_COLORS[1]);
  ctx.beginPath();
  ctx.moveTo(x, y);
  ctx.lineTo(x + Math.cos(heading) * w.blue_radius, y + Math.sin(heading) * w.blue_radius);
  ctx.strokeStyle = "#0b1220";
  ctx.lineWidth = 2;
  ctx.stroke();
}

function draw() {
  requestAnimationFrame(draw);
  ctx.setTransform(1, 0, 0, 1, 0, 0);
  ctx.fillStyle = "#05080b";
  ctx.fillRect(0, 0, canvas.width, canvas.height);
  if (!frame) return;

  const w = frame.world;
  const scale = Math.min(canvas.width / w.width, canvas.height / w.height);
  const ox = (canvas.width - w.width * scale) / 2;
  const oy = (canvas.height - w.height * scale) / 2;
  ctx.setTransform(scale, 0, 0, scale, ox, oy);
  ctx.fillStyle = FIELD;
  ctx.fillRect(0, 0, w.width, w.height);

  ctx.save();
  ctx.beginPath();
  ctx.rect(0, 0, w.width, w.height);
  ctx.clip();
  for (const [x, y] of frame.food) circle(x, y, w.food_radius, TYPE_COLORS[0]);
  // Each blue is drawn at its 8 wrapped copies too; the clip hides the ones off the field.
  for (const dx of [-w.width, 0, w.width]) {
    for (const dy of [-w.height, 0, w.height]) {
      frame.blues.forEach(([x, y, heading], i) => {
        if (showVision) drawVision(x + dx, y + dy, heading, frame.slices[i], w);
      });
      for (const [x, y, heading] of frame.blues) drawBlue(x + dx, y + dy, heading, w);
    }
  }
  ctx.restore();
}

window.addEventListener("resize", resize);
resize();
connect();
draw();
