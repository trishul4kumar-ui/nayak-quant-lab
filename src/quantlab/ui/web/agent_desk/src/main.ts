import * as THREE from "three";
import { connect, navigate, type DeskDTO } from "./bridge";
import "./theme.css";

const root = document.querySelector<HTMLDivElement>("#scene")!;
const fallback = document.querySelector<HTMLParagraphElement>("#fallback")!;
const reducedMotion = window.matchMedia("(prefers-reduced-motion: reduce)");
let render: (() => void) | undefined;
let dispose: (() => void) | undefined;
let updateGraph: ((dto: DeskDTO) => void) | undefined;
let latest: DeskDTO | undefined;

function setupScene(): void {
  const canvas = document.createElement("canvas");
  if (!canvas.getContext("webgl2")) { fallback.textContent = "WebGL2 unavailable · native analysts available"; return; }
  const renderer = new THREE.WebGLRenderer({canvas, antialias: true, alpha: true});
  renderer.setPixelRatio(Math.min(window.devicePixelRatio, 1.5));
  const scene = new THREE.Scene();
  const camera = new THREE.PerspectiveCamera(35, 1, 0.1, 100);
  camera.position.set(0, 2, 8);
  camera.lookAt(0, 0, 0);
  const geometry = new THREE.IcosahedronGeometry(0.65, 1);
  const materials = [0x4bcfb6, 0x7bbfee, 0xe9b479].map(color => new THREE.MeshBasicMaterial({color, wireframe: true, transparent: true, opacity: 0.5}));
  const nodes = materials.map((material, index) => {
    const mesh = new THREE.Mesh(geometry, material);
    mesh.position.x = (index - 1) * 2.5;
    scene.add(mesh);
    return mesh;
  });
  const graph = new THREE.Group();
  scene.add(graph);
  const clearGraph = () => {
    for (const object of graph.children) {
      if (object instanceof THREE.Mesh || object instanceof THREE.Line) {
        object.geometry.dispose();
        const material = object.material;
        if (Array.isArray(material)) material.forEach(m => m.dispose());
        else material.dispose();
      }
    }
    graph.clear();
  };
  updateGraph = dto => {
    clearGraph();
    const positions = new Map<string, THREE.Vector3>();
    dto.evidence.forEach((item, index) => {
      const row = Math.floor(index / 5), column = index % 5;
      const position = new THREE.Vector3((column - 2) * .42, (row - 2.5) * .38, .2);
      positions.set(item.artifact_hash, position);
      const mesh = new THREE.Mesh(new THREE.SphereGeometry(.065, 8, 6),
        new THREE.MeshBasicMaterial({color: 0x7bbfee}));
      mesh.position.copy(position);
      mesh.userData.evidenceHash = item.artifact_hash;
      graph.add(mesh);
    });
    for (const edge of dto.debate?.edges ?? []) {
      const end = positions.get(edge.evidence_hash);
      if (!end) continue;
      const start = new THREE.Vector3(edge.agent === "BULL" ? -2.5 : 2.5, 0, 0);
      const color = edge.relation === "SUPPORT" ? 0x4bcfb6 : edge.relation === "CONTRADICTION" ? 0xe9b479 : 0x687e90;
      const line = new THREE.Line(new THREE.BufferGeometry().setFromPoints([start, end]),
        new THREE.LineBasicMaterial({color, transparent: true, opacity: .45}));
      graph.add(line);
    }
    nodes[1].visible = !dto.debate;
    render?.();
  };
  const raycaster = new THREE.Raycaster();
  canvas.addEventListener("click", event => {
    const bounds = canvas.getBoundingClientRect();
    const pointer = new THREE.Vector2(((event.clientX-bounds.left)/bounds.width)*2-1,
      -((event.clientY-bounds.top)/bounds.height)*2+1);
    raycaster.setFromCamera(pointer, camera);
    const hit = raycaster.intersectObjects(graph.children).find(item => item.object.userData.evidenceHash);
    if (hit) navigate("open_evidence", String(hit.object.userData.evidenceHash));
  });
  root.append(canvas);
  const resize = new ResizeObserver(() => {
    const width = Math.max(root.clientWidth, 1), height = Math.max(root.clientHeight, 1);
    renderer.setSize(width, height, false);
    camera.aspect = width / height;
    camera.updateProjectionMatrix();
    renderer.render(scene, camera);
  });
  resize.observe(root);
  render = () => renderer.render(scene, camera);
  // No synthetic thinking/progress: geometry moves only when real state arrives.
  root.addEventListener("analyst-state", () => {
    if (!document.hidden && !reducedMotion.matches) {
      nodes.forEach(node => { node.rotation.y += 0.08; });
    }
    render?.();
  });
  canvas.addEventListener("webglcontextlost", event => {
    event.preventDefault();
    fallback.textContent = "Visual context lost · native analysts available";
  });
  dispose = () => {
    resize.disconnect(); geometry.dispose(); materials.forEach(m => m.dispose());
    clearGraph(); renderer.dispose(); canvas.remove(); render = undefined; updateGraph = undefined;
  };
}

function display(dto: DeskDTO): void {
  latest = dto;
  for (const agent of dto.agents) {
    const station = document.querySelector<HTMLButtonElement>(`#${agent.agent.toLowerCase()}`)!;
    station.querySelector("strong")!.textContent = agent.state;
    station.querySelector("small")!.textContent = `${agent.task_label} · ${agent.completed_tools} tools completed`;
  }
  document.querySelector("#system-state")!.textContent = dto.debate
    ? `${dto.debate.status} · ${dto.debate.critiques} critiques / ${dto.debate.rebuttals} rebuttals`
    : "Native state connected";
  document.querySelector<HTMLButtonElement>("#debate-transcript")!.disabled = !dto.debate;
  const decision = dto.adjudication;
  document.querySelector("#adjudication")!.textContent = decision
    ? `${decision.outcome} · ${decision.no_trade ? "NO_TRADE" : "RESEARCH ONLY"} · Bull ${decision.bull_score.toFixed(2)} / Bear ${decision.bear_score.toFixed(2)} · ${decision.blocker_count} blockers${decision.expired ? " · EXPIRED" : ""}`
    : "Deterministic adjudication not evaluated";
  const scores = document.querySelector<HTMLElement>("#score-components")!;
  scores.replaceChildren();
  scores.hidden = !decision;
  for (const component of decision?.components ?? []) {
    const label = document.createElement("label"), meter = document.createElement("meter");
    label.textContent = `${component.role} · ${component.name} · ${component.status}`;
    meter.min = 0; meter.max = 1; meter.value = component.value ?? 0;
    meter.setAttribute("aria-label", `${component.role} ${component.name}: ${component.status}`);
    label.append(meter); scores.append(label);
  }
  document.querySelector("#decision-warnings")!.textContent = decision
    ? `${decision.warnings.join(" · ")} · NO EXECUTION AUTHORITY` : "";
  const evidence = document.querySelector("#evidence")!;
  evidence.replaceChildren();
  for (const item of dto.evidence) {
    const li = document.createElement("li"), button = document.createElement("button");
    button.type = "button";
    button.textContent = `${item.label} · ${item.status}`;
    button.addEventListener("click", () => navigate("open_evidence", item.artifact_hash));
    li.append(button); evidence.append(li);
  }
  root.dispatchEvent(new Event("analyst-state"));
  updateGraph?.(dto);
}

document.querySelector("#bull")!.addEventListener("click", () => navigate("select_agent", "BULL"));
document.querySelector("#bear")!.addEventListener("click", () => navigate("select_agent", "BEAR"));
document.querySelector("#debate-transcript")!.addEventListener("click", () => {
  if (latest?.adjudication) navigate("open_adjudication", latest.adjudication.decision_hash);
  else if (latest?.debate) navigate("open_debate", latest.debate.transcript_hash);
});
document.addEventListener("visibilitychange", () => { if (!document.hidden) render?.(); });
window.addEventListener("pagehide", () => dispose?.());
try { setupScene(); } catch { fallback.textContent = "Visual layer unavailable · native analysts available"; }
connect(display);
