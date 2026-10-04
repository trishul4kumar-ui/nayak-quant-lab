import * as THREE from "three";
import { connect, navigate, type DeskDTO } from "./bridge";
import "./theme.css";

const root = document.querySelector<HTMLDivElement>("#scene")!;
const fallback = document.querySelector<HTMLParagraphElement>("#fallback")!;
const reducedMotion = window.matchMedia("(prefers-reduced-motion: reduce)");
let render: (() => void) | undefined;
let dispose: (() => void) | undefined;

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
    renderer.dispose(); canvas.remove(); render = undefined;
  };
}

function display(dto: DeskDTO): void {
  for (const agent of dto.agents) {
    const station = document.querySelector<HTMLButtonElement>(`#${agent.agent.toLowerCase()}`)!;
    station.querySelector("strong")!.textContent = agent.state;
    station.querySelector("small")!.textContent = `${agent.task_label} · ${agent.completed_tools} tools completed`;
  }
  document.querySelector("#system-state")!.textContent = "Native state connected";
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
}

document.querySelector("#bull")!.addEventListener("click", () => navigate("select_agent", "BULL"));
document.querySelector("#bear")!.addEventListener("click", () => navigate("select_agent", "BEAR"));
document.addEventListener("visibilitychange", () => { if (!document.hidden) render?.(); });
window.addEventListener("pagehide", () => dispose?.());
try { setupScene(); } catch { fallback.textContent = "Visual layer unavailable · native analysts available"; }
connect(display);
