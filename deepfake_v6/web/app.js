"use strict";
const $ = (id) => document.getElementById(id);
const LABEL = {
  likely_fake: ["Có dấu hiệu giả", "fake"],
  likely_real: ["Có vẻ thật", "real"],
  uncertain: ["Không chắc chắn", "unc"],
  cannot_assess: ["Không đánh giá được", "none"],
};
const SIG = { face_manipulation: "Khuôn mặt bị ghép/chỉnh", ai_generated: "Toàn khung do AI tạo" };

// ---------- tabs ----------
document.querySelectorAll(".tab").forEach((b) => b.addEventListener("click", () => {
  document.querySelectorAll(".tab").forEach((x) => x.classList.toggle("active", x === b));
  $("tab-file").hidden = b.dataset.tab !== "file";
  $("tab-live").hidden = b.dataset.tab !== "live";
}));

function setBadge(el, verdict) {
  const [txt, cls] = LABEL[verdict] || ["Lỗi", "none"];
  el.textContent = txt;
  el.className = "badge " + cls;
}
function setMeter(barId, pctId, score, thr) {
  const bar = $(barId), meter = bar.parentElement;
  const p = score == null ? 0 : Math.max(0, Math.min(1, score));
  bar.style.width = (p * 100).toFixed(0) + "%";
  $(pctId).textContent = score == null ? "–" : (p * 100).toFixed(0) + "%";
  let t = meter.querySelector(".thr");
  if (!t) { t = document.createElement("div"); t.className = "thr"; meter.appendChild(t); }
  t.style.left = ((thr ?? 0.5) * 100) + "%";
}
function drawChart(svg, pts, thr, xmax) {
  // pts: [{x, y}] with y in 0..1; null y = gap
  const W = 600, H = 160, P = 8;
  const X = (x) => P + (xmax > 0 ? x / xmax : 0) * (W - 2 * P);
  const Y = (y) => H - P - y * (H - 2 * P);
  let s = `<line x1="0" x2="${W}" y1="${Y(thr)}" y2="${Y(thr)}" stroke="#d29922" stroke-dasharray="6 4"/>`;
  s += `<text x="${W - 4}" y="${Y(thr) - 4}" fill="#d29922" font-size="11" text-anchor="end">ngưỡng ${thr}</text>`;
  let path = "", pen = false;
  for (const p of pts) {
    if (p.y == null) { pen = false; continue; }
    path += (pen ? "L" : "M") + X(p.x).toFixed(1) + " " + Y(p.y).toFixed(1) + " "; pen = true;
  }
  s += `<path d="${path}" fill="none" stroke="#3fb950" stroke-width="2.5"/>`;
  for (const p of pts) if (p.y != null)
    s += `<circle cx="${X(p.x)}" cy="${Y(p.y)}" r="3.5" fill="${p.y >= thr ? "#f85149" : "#3fb950"}"><title>${p.label ?? ""} ${(p.y * 100).toFixed(0)}%</title></circle>`;
  svg.innerHTML = s;
}

// ---------- file check ----------
const drop = $("drop");
["dragenter", "dragover"].forEach((e) => drop.addEventListener(e, (ev) => { ev.preventDefault(); drop.classList.add("over"); }));
["dragleave", "drop"].forEach((e) => drop.addEventListener(e, (ev) => { ev.preventDefault(); drop.classList.remove("over"); }));
drop.addEventListener("drop", (ev) => ev.dataTransfer.files[0] && checkFile(ev.dataTransfer.files[0]));
$("pick").addEventListener("change", (ev) => ev.target.files[0] && checkFile(ev.target.files[0]));

async function checkFile(file) {
  const isVid = file.type.startsWith("video");
  const url = URL.createObjectURL(file);
  $("preview").innerHTML = isVid ? `<video src="${url}" controls muted></video>` : `<img src="${url}" alt="">`;
  $("fname").textContent = `${file.name} · ${(file.size / 1048576).toFixed(1)} MB`;
  $("previewCard").hidden = false; $("resultCard").hidden = false;
  $("spinner").hidden = false; $("result").hidden = true; $("error").hidden = true;
  const fd = new FormData(); fd.append("file", file);
  try {
    const res = await fetch("/api/deepfake/check?thumbs=true", { method: "POST", body: fd });
    const r = await res.json();
    if (!res.ok) throw new Error(r.message || res.statusText);
    showResult(r);
  } catch (e) {
    $("error").textContent = "Lỗi: " + e.message; $("error").hidden = false;
  } finally { $("spinner").hidden = true; }
}

function showResult(r) {
  $("result").hidden = false;
  setBadge($("badge"), r.verdict);
  setMeter("bar", "pct", r.score, r.threshold);
  $("reason").textContent = r.reason || "";
  $("reasons").innerHTML = (r.reasons || []).map((x) => `<li class="${rcls(x)}">${ricon(x)} ${x.text}</li>`).join("");
  $("advice").textContent = r.advice || ""; $("advice").hidden = !r.advice;
  $("disc").textContent = r.disclaimer || "";
  $("time").textContent = `Thời gian xử lý: ${r.elapsed_s}s · mô hình: ${r.model}`;
  const sig = $("signals"); sig.innerHTML = "";
  if (r.signals) for (const [k, v] of Object.entries(r.signals)) {
    const lab = (LABEL[v.verdict] || ["?"])[0];
    sig.insertAdjacentHTML("beforeend", `<p class="sig">• ${SIG[k] || k}: ${v.score == null ? "–" : (v.score * 100).toFixed(0) + "%"} (ngưỡng ${(v.threshold * 100).toFixed(0)}%) → <b>${lab}</b></p>`);
  }
  const th = $("thumbs"); th.innerHTML = "";
  let items = [];
  if (r.type === "video") {
    $("chartWrap").hidden = false;
    const pts = (r.frames || []).map((f) => ({ x: f.t, y: f.fake_score ?? null, label: f.t + "s" }));
    drawChart($("chart"), pts, r.threshold, r.duration_s || (pts.length ? pts[pts.length - 1].x : 1));
    items = (r.most_suspicious || []).map((m) => ({ src: m.thumb, cap: `${m.t}s · ${(m.fake_score * 100).toFixed(0)}%` }));
    $("thumbsTitle").textContent = "Khung đáng ngờ nhất";
  } else {
    $("chartWrap").hidden = true;
    items = (r.faces || []).map((f, i) => ({ src: f.thumb, cap: `Mặt ${i + 1}: ${f.fake_score == null ? (f.quality_issues || []).join(", ") || "–" : (f.fake_score * 100).toFixed(0) + "%"}` }));
    $("thumbsTitle").textContent = "Khuôn mặt tìm thấy";
  }
  items = items.filter((i) => i.src);
  for (const i of items) th.insertAdjacentHTML("beforeend", `<figure><img src="${i.src}" alt=""><figcaption>${i.cap}</figcaption></figure>`);
  $("thumbsWrap").hidden = items.length === 0;
}

// ---------- live call ----------
const video = $("liveVideo"), overlay = $("overlay");
const grab = document.createElement("canvas");
let stream = null, timer = null, busy = false, sid = "", hist = [], t0 = 0, lat = [];

async function startLive(kind) {
  stopLive();
  try {
    if (kind !== "file") { video.removeAttribute("src"); video.load(); } else { video.play(); }
    if (kind === "screen") stream = await navigator.mediaDevices.getDisplayMedia({ video: { frameRate: 5 }, audio: false });
    else if (kind === "cam") stream = await navigator.mediaDevices.getUserMedia({ video: true, audio: false });
    if (stream) { video.srcObject = stream; stream.getVideoTracks()[0].addEventListener("ended", stopLive); }
  } catch (e) { $("liveStat").textContent = "Không mở được nguồn hình: " + e.message; return; }
  sid = Math.random().toString(36).slice(2); hist = []; lat = []; t0 = performance.now();
  await fetch("/api/deepfake/frame/reset?session_id=" + sid, { method: "POST" });
  $("btnStop").disabled = false; $("btnChal").disabled = false; $("liveStat").textContent = "Đang theo dõi…";
  timer = setInterval(tick, 1000);
}
function stopLive() {
  if (timer) clearInterval(timer); timer = null;
  if (stream) stream.getTracks().forEach((t) => t.stop()); stream = null;
  if (video.src) { video.pause(); }
  $("btnStop").disabled = true; chalOn = false; if ($("btnChal")) $("btnChal").disabled = true; $("liveStat").textContent = hist.length ? "Đã dừng." : "";
}
async function tick() {
  if (busy || chalOn || !video.videoWidth) return;
  busy = true;
  const s = Math.min(1, 960 / video.videoWidth);
  grab.width = Math.round(video.videoWidth * s); grab.height = Math.round(video.videoHeight * s);
  grab.getContext("2d").drawImage(video, 0, 0, grab.width, grab.height);
  const blob = await new Promise((ok) => grab.toBlob(ok, "image/jpeg", 0.85));
  const fd = new FormData(); fd.append("file", blob, "frame.jpg");
  try {
    const res = await fetch("/api/deepfake/frame?session_id=" + sid, { method: "POST", body: fd });
    const r = await res.json();
    if (res.ok) showLive(r);
  } catch (e) { $("liveStat").textContent = "Lỗi kết nối API: " + e.message; }
  busy = false;
}
function showLive(r) {
  const t = (performance.now() - t0) / 1000;
  hist.push({ x: t, y: r.smoothed_score, label: t.toFixed(0) + "s" }); if (hist.length > 90) hist.shift();
  lat.push(r.latency_s); if (lat.length > 20) lat.shift();
  setBadge($("liveBadge"), r.verdict);
  setMeter("liveBar", "livePct", r.smoothed_score, r.threshold);
  const x0 = hist[0].x;
  drawChart($("liveChart"), hist.map((h) => ({ ...h, x: h.x - x0 })), r.threshold, Math.max(10, t - x0));
  $("alert").hidden = !r.alert;
  const avg = lat.reduce((a, b) => a + b, 0) / lat.length;
  $("liveInfo").textContent = `Khung: ${r.frames_received} · mặt: ${r.faces.length} · điểm khung này: ${r.frame_score == null ? "–" : (r.frame_score * 100).toFixed(0) + "%"} · cửa sổ ${r.window}/8 · xử lý ~${avg.toFixed(2)}s/khung`;
  const ls = $("liveSignals");
  if (ls && r.reasons) ls.innerHTML = "<h4>Lý do</h4><ul class=\"reasons\">" + r.reasons.map((x) =>
    `<li class="${rcls(x, true)}">${ricon(x, true)} ${x.text}${x.contributing ? " <b class=\"contrib\">[đang góp vào điểm]</b>" : ""}</li>`).join("") + "</ul>";
  // face boxes
  overlay.width = video.clientWidth; overlay.height = video.clientHeight;
  const ctx = overlay.getContext("2d"); ctx.clearRect(0, 0, overlay.width, overlay.height);
  ctx.lineWidth = 3; ctx.font = "14px sans-serif";
  for (const f of r.faces) {
    const [x, y, w, h] = f.box_rel;
    const col = f.fake_score == null ? "#8b949e" : f.fake_score >= r.threshold ? "#f85149" : "#3fb950";
    ctx.strokeStyle = col; ctx.fillStyle = col;
    ctx.strokeRect(x * overlay.width, y * overlay.height, w * overlay.width, h * overlay.height);
    ctx.fillText(f.fake_score == null ? "chất lượng thấp" : (f.fake_score * 100).toFixed(0) + "%", x * overlay.width, y * overlay.height - 5);
  }
}
$("btnScreen").onclick = () => startLive("screen");
$("btnCam").onclick = () => startLive("cam");
$("btnFile").onclick = () => $("liveFile").click();
$("liveFile").onchange = (ev) => {
  const f = ev.target.files[0]; if (!f) return;
  stopLive(); video.srcObject = null; video.src = URL.createObjectURL(f); video.loop = true;
  startLive("file");
};
$("btnStop").onclick = stopLive;

// ---------- item 1: icon rules (red only when it really pushes the score) ----------
function isInfo(x, live) { return x.abnormal && (live ? !x.contributing : !!x.info); }
function rcls(x, live) { return !x.abnormal ? "ok" : isInfo(x, live) ? "info" : "bad"; }
function ricon(x, live) { return !x.abnormal ? "✅" : isInfo(x, live) ? "ℹ️" : "⚠️"; }

// ---------- item 2: Kiểm tra chủ động ----------
let chalOn = false;
const sleep = (ms) => new Promise((ok) => setTimeout(ok, ms));
async function lmFrame() {
  const s = Math.min(1, 480 / video.videoWidth);
  grab.width = Math.round(video.videoWidth * s); grab.height = Math.round(video.videoHeight * s);
  grab.getContext("2d").drawImage(video, 0, 0, grab.width, grab.height);
  const blob = await new Promise((ok) => grab.toBlob(ok, "image/jpeg", 0.8));
  const fd = new FormData(); fd.append("file", blob, "f.jpg");
  const res = await fetch("/api/deepfake/landmarks", { method: "POST", body: fd });
  return res.ok ? res.json() : { face: false };
}
async function collect(ms) {
  const out = [], end = performance.now() + ms;
  while (performance.now() < end && chalOn) { try { out.push(await lmFrame()); } catch (e) { /* skip */ } }
  return out;
}
const med = (a) => { const b = [...a].sort((x, y) => x - y); return b.length ? b[Math.floor(b.length / 2)] : null; };
const f2 = (x) => (x == null ? "–" : x.toFixed(2).replace(".", ","));
function evalTurn(base, ss, label) {
  const ys = ss.filter((f) => f.face && f.yaw != null).map((f) => f.yaw);
  const lost = ss.filter((f) => !f.face).length;
  if (ys.length < 3) return { st: "❓", sign: 0, text: `${label}: chỉ thấy mặt ở ${ys.length}/${ss.length} khung (mất mặt ${lost} khung) → chưa đo được` };
  const d = ys.map((y) => y - base), dmax = d.reduce((a, b) => (Math.abs(b) > Math.abs(a) ? b : a), 0);
  const ok = Math.abs(dmax) >= 0.12;
  return { st: ok ? "✅" : "⚠️", sign: Math.sign(dmax), text: `${label}: độ xoay đầu lệch tối đa ${f2(dmax)} so với lúc nhìn thẳng (cần ≥ 0,12), ${ys.length} khung có mặt` };
}
async function runChallenge() {
  if (!video.videoWidth || chalOn) return;
  chalOn = true; $("btnChal").disabled = true; $("chalBox").hidden = false; $("chalList").innerHTML = ""; $("chalVerdict").textContent = "";
  const add = (r) => $("chalList").insertAdjacentHTML("beforeend", `<li class="${r.st === "✅" ? "ok" : r.st === "⚠️" ? "bad" : "info"}">${r.st} ${r.text}</li>`);
  const step = async (txt, ms) => { $("chalStep").textContent = txt; await sleep(1200); return collect(ms); };
  const res = [];
  try {
    const b0 = await step("👀 Nhìn thẳng vào camera…", 1500);
    const base = med(b0.filter((f) => f.face && f.yaw != null).map((f) => f.yaw)) ?? 0;
    const L = evalTurn(base, await step("⬅️ Quay đầu sang TRÁI", 3000), "Quay trái"); add(L); res.push(L);
    const R = evalTurn(base, await step("➡️ Quay đầu sang PHẢI", 3000), "Quay phải");
    if (R.st === "✅" && L.st === "✅" && R.sign === L.sign) { R.st = "⚠️"; R.text += " — nhưng cùng chiều với lần quay trái"; }
    add(R); res.push(R);
    const bl = await step("😉 Chớp mắt 2 lần", 3500);
    const eyes = bl.filter((f) => f.face && f.eye != null).map((f) => f.eye);
    let B;
    if (eyes.length < 5) B = { st: "❓", text: `Chớp mắt: chỉ đo được mắt ở ${eyes.length} khung (cần ≥ 5; phòng tối/camera mờ) → chưa đo được` };
    else {
      const m = med(eyes); let dips = 0, low = false;
      for (const e of eyes) { if (e < 0.7 * m) { if (!low) dips++; low = true; } else low = false; }
      B = { st: dips >= 1 ? "✅" : "⚠️", text: `Chớp mắt: thấy ${dips} lần độ mở mắt giảm < 70% mức thường, trong ${eyes.length} khung (cần ≥ 1; máy lấy ~${(eyes.length / 3.5).toFixed(0)} khung/giây nên có thể lỡ)` };
    }
    add(B); res.push(B);
    const hd = await step("✋ Đưa tay che ngang qua mặt rồi bỏ ra", 3500);
    const vis = hd.filter((f) => f.face && (f.prob ?? 0) >= 0.95).length, n = hd.length;
    let H;
    if (n < 4) H = { st: "❓", text: `Đưa tay qua mặt: chỉ có ${n} khung → chưa đo được` };
    else {
      const covered = n - vis, back = hd.slice(-3).some((f) => f.face);
      H = { st: covered >= 1 && back ? "✅" : covered >= 1 ? "❓" : "⚠️",
            text: `Đưa tay qua mặt: ${covered}/${n} khung mặt bị che/mất (cần ≥ 1), ${back ? "mặt hiện lại sau đó" : "chưa thấy mặt hiện lại"}${covered === 0 ? " — mặt vẫn hiện rõ dù có tay che (lớp mặt giả thường không bị che)" : ""}` };
    }
    add(H); res.push(H);
    const ok = res.filter((r) => r.st === "✅").length, bad = res.filter((r) => r.st === "⚠️").length;
    const v = bad >= 3 ? ["Nghi giả", "fake"] : ok >= 3 && bad === 0 ? ["Đạt", "real"] : ["Cần xác minh thêm", "unc"];
    $("chalVerdict").innerHTML = `<span class="badge ${v[1]}">${v[0]}</span> ${ok}/4 bước đạt, ${bad} bước bất thường, ${4 - ok - bad} bước chưa đo được`;
  } finally { $("chalStep").textContent = "Xong."; chalOn = false; $("btnChal").disabled = !timer; }
}
$("btnChal").onclick = runChallenge;
