import * as THREE from "three";
import { OrbitControls } from "three/addons/controls/OrbitControls.js";
import { RoundedBoxGeometry } from "three/addons/geometries/RoundedBoxGeometry.js";
import { connect, navigate, type DeskDTO, type DeskRole, type InstitutionalAgent } from "./bridge";
import "./theme.css";

type RoleSpec = {role: DeskRole; name: string; title: string; description: string; symbol: string; color: number; position: [number, number, number]; scale: number};
const roles: RoleSpec[] = [
  {role: "NAYAK", name: "NAYAK", title: "Interactive chief", description: "Your interactive entry point to the desk. Ask for evidence, research summaries, and the team's findings.", symbol: "N", color: 0x8ce5ef, position: [0, .4, -3.35], scale: 1.32},
  {role: "SUPERVISOR", name: "Supervisor", title: "Desk orchestration", description: "Assigns bounded research work, checks specialist reports, and consolidates their findings for NAYAK.", symbol: "◈", color: 0xb1a2ee, position: [0, 0, -.55], scale: 1.07},
  {role: "BULL", name: "Bull", title: "Long-side research", description: "Investigates supporting evidence and long-side hypotheses through approved research tools.", symbol: "↗", color: 0x69d6b0, position: [-3.15, 0, -2.25], scale: 1.03},
  {role: "BEAR", name: "Bear", title: "Contrary evidence", description: "Challenges assumptions, finds failure modes, and tests liquidity and regime risks.", symbol: "↘", color: 0xe8aa7c, position: [3.15, 0, -2.25], scale: 1.03},
  {role: "NEWS_DOCS", name: "News / Docs", title: "Source intelligence", description: "Reviews frozen source documents and reports what the cited material supports, or leaves unknowns unresolved.", symbol: "≡", color: 0x79bfeb, position: [-5.2, 0, .6], scale: .95},
  {role: "QUANT", name: "Quant", title: "Quantitative research", description: "Interprets approved backtests, factors, regimes, validation, and transaction-cost evidence.", symbol: "∑", color: 0x98a8fa, position: [-2.7, 0, 2.65], scale: .98},
  {role: "RISK", name: "Risk", title: "Risk interpretation", description: "Explains deterministic risk checks and blockers. Its reports cannot override the lab's policy.", symbol: "◇", color: 0xe7c981, position: [0, 0, 3.65], scale: 1.01},
  {role: "EXECUTION_MONITOR", name: "Execution", title: "Paper / shadow monitor", description: "Reviews orders, simulated fills, and reconciliation evidence in the read-only paper and shadow systems.", symbol: "⌁", color: 0x71d3db, position: [2.7, 0, 2.65], scale: .98},
  {role: "AUDIT", name: "Audit", title: "Evidence & operations", description: "Inspects the ledger, frozen reports, and anomalies, and produces an auditable evidence summary.", symbol: "✓", color: 0xc9b8da, position: [5.2, 0, .6], scale: .95},
];
const root = document.querySelector<HTMLDivElement>("#scene")!;
const fallback = document.querySelector<HTMLElement>("#fallback")!;
const reducedMotion = window.matchMedia("(prefers-reduced-motion: reduce)");
const roster = document.querySelector<HTMLElement>("#role-roster")!;
const cards = new Map<DeskRole, HTMLButtonElement>();
const labels = new Map<DeskRole, HTMLElement>();
let latest: DeskDTO | undefined;
let selected: DeskRole = "NAYAK";
let render: (() => void) | undefined;
let updateScene: ((dto?: DeskDTO) => void) | undefined;
let resetCamera: (() => void) | undefined;
let dispose: (() => void) | undefined;

function stateFor(role: DeskRole): InstitutionalAgent {
  const state = latest?.institution?.agents.find(item => item.role === role);
  if (state) return state;
  const legacy = latest?.agents.find(item => item.agent === role);
  const spec = roles.find(item => item.role === role)!;
  return {role, label: spec.name, status: legacy?.state ?? (latest ? "IDLE" : "WAITING"), task: legacy?.task_label ?? "No research assignment.", report_hash: null, summary: "No frozen institutional report is available yet.", evidence_count: legacy?.completed_tools ?? 0};
}

function updateSelection(): void {
  const spec = roles.find(item => item.role === selected)!;
  const state = stateFor(selected);
  document.querySelector<HTMLElement>("#role-detail")!.style.setProperty("--role-accent", `#${spec.color.toString(16).padStart(6, "0")}`);
  document.querySelector("#detail-number")!.textContent = `${String(roles.indexOf(spec) + 1).padStart(2, "0")} / 09`;
  document.querySelector("#detail-symbol")!.textContent = spec.symbol;
  document.querySelector("#detail-title")!.textContent = spec.title.toUpperCase();
  document.querySelector("#detail-name")!.textContent = spec.name;
  document.querySelector("#detail-description")!.textContent = spec.description;
  document.querySelector("#detail-status")!.textContent = state.status.replaceAll("_", " ");
  document.querySelector("#detail-task")!.textContent = state.task;
  document.querySelector("#detail-summary")!.textContent = state.summary;
  document.querySelector("#detail-evidence")!.textContent = `${state.evidence_count} evidence artifacts`;
  document.querySelector("#detail-hash")!.textContent = state.report_hash ? `${state.report_hash.slice(0, 10)}…` : "UNPUBLISHED";
  document.querySelector("#inspect-role")!.textContent = `Open ${spec.name} ↗`;
  for (const role of roles) {
    cards.get(role.role)!.setAttribute("aria-pressed", String(role.role === selected));
    cards.get(role.role)!.classList.toggle("working", latest?.institution?.active_role === role.role);
    cards.get(role.role)!.querySelector("small")!.textContent = stateFor(role.role).status.replaceAll("_", " ");
    const label = labels.get(role.role);
    label?.classList.toggle("selected", role.role === selected);
    label?.classList.toggle("working", latest?.institution?.active_role === role.role);
    if (label) label.querySelector("small")!.textContent = stateFor(role.role).status.replaceAll("_", " ");
  }
  updateScene?.(latest);
}

function selectRole(role: DeskRole, openNative = true): void {
  selected = role;
  updateSelection();
  if (openNative) navigate("select_role", role);
}

for (const role of roles) {
  const button = document.createElement("button");
  button.type = "button";
  button.className = "role-card";
  button.style.setProperty("--role-accent", `#${role.color.toString(16).padStart(6, "0")}`);
  button.setAttribute("aria-label", `Select ${role.name}, ${role.title}`);
  const symbol = document.createElement("span"), name = document.createElement("strong"), status = document.createElement("small");
  symbol.className = "role-symbol"; symbol.textContent = role.symbol; symbol.setAttribute("aria-hidden", "true");
  name.textContent = role.name; status.textContent = "WAITING";
  button.append(symbol, name, status);
  button.addEventListener("click", () => selectRole(role.role));
  roster.append(button); cards.set(role.role, button);
}

function setupScene(): void {
  const canvas = document.createElement("canvas");
  if (!canvas.getContext("webgl2", {antialias: true})) {
    fallback.textContent = "3D unavailable · select any agent below to open its native inspector";
    root.classList.add("no-webgl");
    return;
  }
  const renderer = new THREE.WebGLRenderer({canvas, antialias: true, alpha: true, powerPreference: "low-power"});
  renderer.setPixelRatio(Math.min(window.devicePixelRatio, 1.25));
  renderer.outputColorSpace = THREE.SRGBColorSpace;
  renderer.toneMapping = THREE.ACESFilmicToneMapping;
  renderer.toneMappingExposure = 1.22;
  const scene = new THREE.Scene();
  scene.fog = new THREE.FogExp2(0x0a1421, .025);
  const camera = new THREE.PerspectiveCamera(33, 1, .1, 100);
  const initialPosition = new THREE.Vector3(0, 9.4, 15.8);
  const initialTarget = new THREE.Vector3(0, .4, .1);
  camera.position.copy(initialPosition);
  const controls = new OrbitControls(camera, canvas);
  controls.target.copy(initialTarget);
  controls.enablePan = false;
  controls.enableZoom = false;
  controls.minPolarAngle = .45;
  controls.maxPolarAngle = 1.07;
  controls.minAzimuthAngle = -.3;
  controls.maxAzimuthAngle = .3;
  controls.enableDamping = false;
  controls.update();
  scene.add(new THREE.HemisphereLight(0xbedbff, 0x162d40, 2.35));
  const keyLight = new THREE.DirectionalLight(0xd2e8ff, 3.6);
  keyLight.position.set(-6, 10, 7); scene.add(keyLight);
  const rimLight = new THREE.DirectionalLight(0x7f91e6, 3.6);
  rimLight.position.set(5, 5, -5); scene.add(rimLight);
  const fillLight = new THREE.PointLight(0x69cdda, 35, 17, 2);
  fillLight.position.set(0, 3.5, 0); scene.add(fillLight);
  const objects = new THREE.Group(); scene.add(objects);
  const resources = new Set<THREE.BufferGeometry | THREE.Material>();
  function resource<T extends THREE.BufferGeometry | THREE.Material>(object: T): T {resources.add(object); return object;}
  const box = resource(new RoundedBoxGeometry(1, 1, 1, 2, .13));
  const sphere = resource(new THREE.SphereGeometry(1, 16, 12));
  const cylinder = resource(new THREE.CylinderGeometry(1, 1, 1, 32));
  const ring = resource(new THREE.TorusGeometry(1, .017, 6, 64));
  const darkMetal = resource(new THREE.MeshStandardMaterial({color: 0x2a4057, roughness: .36, metalness: .72}));
  const graphite = resource(new THREE.MeshStandardMaterial({color: 0x142638, roughness: .38, metalness: .67}));
  const platinum = resource(new THREE.MeshStandardMaterial({color: 0xa5b4c7, roughness: .25, metalness: .83}));
  const glass = resource(new THREE.MeshStandardMaterial({color: 0x39506f, roughness: .12, metalness: .7, transparent: true, opacity: .65}));
  const floorMat = resource(new THREE.MeshStandardMaterial({color: 0x101f2e, roughness: .42, metalness: .68}));
  const shadowMat = resource(new THREE.MeshBasicMaterial({color: 0x020712, transparent: true, opacity: .32, depthWrite: false}));
  const figures = new Map<DeskRole, {group: THREE.Group; halo: THREE.Mesh; glow: THREE.MeshStandardMaterial; haloMat: THREE.MeshBasicMaterial; labelAnchor: THREE.Object3D}>();
  const selectable: THREE.Object3D[] = [];
  function mesh(parent: THREE.Group, geometry: THREE.BufferGeometry, material: THREE.Material, scale: [number, number, number], position: [number, number, number], rotation?: [number, number, number]): THREE.Mesh {
    const item = new THREE.Mesh(geometry, material);
    item.scale.set(...scale); item.position.set(...position);
    if (rotation) item.rotation.set(...rotation);
    parent.add(item); return item;
  }
  function tube(parent: THREE.Group, points: THREE.Vector3[], radius: number, material: THREE.Material): THREE.Mesh {
    const geometry = resource(new THREE.TubeGeometry(new THREE.CatmullRomCurve3(points), 18, radius, 6, false));
    const item = new THREE.Mesh(geometry, material); parent.add(item); return item;
  }
  function line(parent: THREE.Group, points: THREE.Vector3[], color: number, opacity: number): THREE.Line {
    const geometry = resource(new THREE.BufferGeometry().setFromPoints(points));
    const material = resource(new THREE.LineBasicMaterial({color, transparent: true, opacity}));
    const item = new THREE.Line(geometry, material); parent.add(item); return item;
  }
  // A restrained architectural stage; no remote images, fonts, models, or post-processing.
  mesh(objects, cylinder, floorMat, [7.1, .18, 6.45], [0, -.25, .2]);
  mesh(objects, cylinder, graphite, [7.3, .12, 6.65], [0, -.36, .2]);
  const perimeterMat = resource(new THREE.MeshBasicMaterial({color: 0x5a91b8, transparent: true, opacity: .3}));
  mesh(objects, ring, perimeterMat, [7.05, 6.4, 1], [0, -.14, .2], [Math.PI / 2, 0, 0]);
  const grid = new THREE.GridHelper(14, 28, 0x305371, 0x1e354d);
  grid.position.set(0, -.145, .2);
  const gridMaterial = grid.material as THREE.Material;
  gridMaterial.transparent = true; gridMaterial.opacity = .35; resources.add(grid.geometry); resources.add(gridMaterial); objects.add(grid);
  const architectureMat = resource(new THREE.MeshStandardMaterial({color: 0x34506b, roughness: .45, metalness: .6, transparent: true, opacity: .35}));
  mesh(objects, cylinder, architectureMat, [4.2, .04, 1.9], [0, -.12, -3]);
  // Segmented vertical fins frame the chief without obscuring the figures.
  for (let i = 0; i < 13; i++) {
    const angle = Math.PI * 1.16 + i * Math.PI * .68 / 12;
    const x = Math.cos(angle) * 6.1, z = Math.sin(angle) * 2.8 - 3.3;
    const height = 1.1 + Math.sin(i / 12 * Math.PI) * 1.6;
    const fin = mesh(objects, box, darkMetal, [.1, height, .15], [x, height / 2 - .3, z]);
    fin.rotation.y = -angle;
  }
  // Permanent reporting lines are architectural, never fabricated task activity.
  const supervisor = roles[1].position;
  for (const spec of roles.slice(2)) {
    const [x,,z] = spec.position;
    line(objects, [new THREE.Vector3(x, -.02, z), new THREE.Vector3(x * .7, .02, z * .55), new THREE.Vector3(supervisor[0], .02, supervisor[2])], spec.color, .19);
  }
  line(objects, [new THREE.Vector3(0, .02, -.55), new THREE.Vector3(0, .02, -2.3), new THREE.Vector3(0, .41, -3.35)], 0x8ad3ec, .45);

  for (const spec of roles) {
    const station = new THREE.Group(); station.position.set(...spec.position); objects.add(station);
    const glow = resource(new THREE.MeshStandardMaterial({color: spec.color, emissive: spec.color, emissiveIntensity: .4, metalness: .35, roughness: .28}));
    const accentMetal = resource(new THREE.MeshStandardMaterial({color: spec.color, roughness: .3, metalness: .75}));
    const haloMat = resource(new THREE.MeshBasicMaterial({color: spec.color, transparent: true, opacity: spec.role === selected ? .8 : .32}));
    mesh(station, cylinder, graphite, [.87, .18, .87], [0, -.02, 0]);
    mesh(station, cylinder, darkMetal, [.8, .05, .8], [0, .09, 0]);
    mesh(station, cylinder, shadowMat, [.54, .012, .43], [0, .122, .08]);
    const halo = mesh(station, ring, haloMat, [.81, .81, 1], [0, .135, 0], [Math.PI / 2, 0, 0]);
    mesh(station, ring, haloMat, [.64, .64, 1], [0, .138, 0], [Math.PI / 2, 0, 0]);
    const body = new THREE.Group(); body.scale.setScalar(spec.scale); body.position.y = .15; station.add(body);
    const broad = spec.role === "BULL" || spec.role === "BEAR" || spec.role === "RISK";
    const width = broad ? 1.15 : .95;
    const chief = spec.role === "NAYAK";
    // Full sculpted robotic anatomy, with bevelled armor, separate joints and luminous insets.
    mesh(body, box, darkMetal, [.28, .52, .3], [-.2, .32, 0], [0, 0, -.035]);
    mesh(body, box, darkMetal, [.28, .52, .3], [.2, .32, 0], [0, 0, .035]);
    mesh(body, box, platinum, [.22, .44, .06], [-.2, .31, .165]);
    mesh(body, box, platinum, [.22, .44, .06], [.2, .31, .165]);
    mesh(body, box, graphite, [.34, .14, .5], [-.2, .06, .1]);
    mesh(body, box, graphite, [.34, .14, .5], [.2, .06, .1]);
    mesh(body, box, glow, [.25, .025, .025], [-.2, .09, .345]);
    mesh(body, box, glow, [.25, .025, .025], [.2, .09, .345]);
    mesh(body, sphere, graphite, [.16, .16, .16], [-.2, .61, 0]);
    mesh(body, sphere, graphite, [.16, .16, .16], [.2, .61, 0]);
    mesh(body, box, graphite, [.58, .23, .35], [0, .75, 0]);
    mesh(body, box, accentMetal, [.55, .1, .055], [0, .8, .18]);
    mesh(body, box, darkMetal, [.63, .68, .42], [0, 1.18, 0]);
    mesh(body, box, platinum, [.59 * width, .42, .07], [0, 1.29, .25]);
    mesh(body, box, graphite, [.48, .21, .09], [0, 1.05, .237]);
    for (let i = 0; i < 3; i++) mesh(body, box, accentMetal, [.045, .12, .045], [(-1 + i) * .1, 1.055, .296]);
    // The chest insignia has an inner lens and a metallic bezel.
    mesh(body, cylinder, graphite, [.125, .046, .125], [0, 1.33, .31], [Math.PI / 2, 0, 0]);
    mesh(body, cylinder, glow, [.085, .05, .085], [0, 1.33, .339], [Math.PI / 2, 0, 0]);
    for (const side of [-1, 1]) {
      mesh(body, sphere, graphite, [.18, .18, .18], [side * .4 * width, 1.41, 0]);
      mesh(body, box, chief ? platinum : accentMetal, [.31, .21, .39], [side * .44 * width, 1.45, .025], [0, 0, side * -.12]);
      mesh(body, box, darkMetal, [.22, .44, .25], [side * .51 * width, 1.17, .035], [0, 0, side * .09]);
      mesh(body, sphere, platinum, [.105, .105, .105], [side * .54 * width, .94, .06]);
      mesh(body, box, darkMetal, [.23, .33, .28], [side * .56 * width, .77, .1], [0, 0, side * -.08]);
      mesh(body, box, glow, [.035, .21, .04], [side * .575 * width, .79, .255]);
      mesh(body, sphere, graphite, [.13, .14, .12], [side * .55 * width, .58, .13]);
    }
    mesh(body, cylinder, platinum, [.13, .13, .13], [0, 1.62, 0]);
    mesh(body, box, chief ? platinum : darkMetal, [.52, .45, .44], [0, 1.9, 0]);
    mesh(body, box, graphite, [.48, .19, .045], [0, 1.92, .236]);
    mesh(body, box, glow, [.37, .047, .026], [0, 1.95, .268]);
    mesh(body, box, darkMetal, [.31, .07, .07], [0, 1.76, .24]);
    for (const side of [-1, 1]) mesh(body, cylinder, accentMetal, [.12, .075, .12], [side * .29, 1.9, 0], [0, 0, Math.PI / 2]);
    if (chief) {
      // Crown arcs and chest diamond distinguish the main interactive chief.
      const crown = mesh(body, ring, glow, [.48, .48, .8], [0, 2.02, -.02], [Math.PI / 2, 0, 0]);
      crown.rotation.x += .2;
      mesh(body, box, glow, [.13, .13, .035], [0, 1.33, .37], [0, 0, Math.PI / 4]);
      mesh(body, box, platinum, [.11, .46, .1], [-.36, 1.28, -.18], [0, 0, -.18]);
      mesh(body, box, platinum, [.11, .46, .1], [.36, 1.28, -.18], [0, 0, .18]);
    } else if (spec.role === "SUPERVISOR") {
      mesh(body, box, accentMetal, [.065, .33, .06], [0, 2.17, -.05]);
      mesh(body, sphere, glow, [.065, .065, .065], [0, 2.35, -.05]);
      for (const side of [-1, 1]) mesh(body, box, glow, [.24, .05, .035], [side * .36, 1.47, .23]);
      for (let i = 0; i < 3; i++) mesh(body, box, glow, [.06, .065, .035], [(i - 1) * .1, 2.07, .24]);
    } else if (spec.role === "BULL") {
      for (const side of [-1, 1]) tube(body, [new THREE.Vector3(side * .24, 2.03, 0), new THREE.Vector3(side * .43, 2.14, -.01), new THREE.Vector3(side * .46, 2.35, .06)], .055, platinum);
      mesh(body, box, accentMetal, [.44, .12, .07], [0, 1.79, .29]);
      mesh(body, box, glow, [.14, .065, .036], [-.09, 1.34, .378], [0, 0, Math.PI / 5]);
      mesh(body, box, glow, [.14, .065, .036], [.04, 1.38, .378], [0, 0, Math.PI / 5]);
    } else if (spec.role === "BEAR") {
      for (const side of [-1, 1]) {
        mesh(body, sphere, accentMetal, [.15, .16, .12], [side * .24, 2.1, -.025]);
        mesh(body, sphere, graphite, [.095, .095, .04], [side * .24, 2.12, .08]);
      }
      mesh(body, box, darkMetal, [.37, .16, .12], [0, 1.79, .255]);
      for (let i = 0; i < 3; i++) mesh(body, box, glow, [.018, .17, .03], [(i - 1) * .075, 1.33, .373], [0, 0, -.22]);
    } else if (spec.role === "NEWS_DOCS") {
      mesh(body, box, accentMetal, [.6, .12, .39], [0, 2.08, -.01]);
      const tablet = mesh(body, box, darkMetal, [.42, .56, .055], [-.69, .97, .25], [0, -.25, -.13]);
      const paper = new THREE.Group(); paper.position.copy(tablet.position); paper.rotation.copy(tablet.rotation); body.add(paper);
      for (let i = 0; i < 4; i++) mesh(paper, box, glow, [i === 0 ? .22 : .28, .022, .022], [i === 0 ? -.03 : 0, .15 - i * .095, .04]);
    } else if (spec.role === "QUANT") {
      mesh(body, box, glass, [.48, .13, .06], [0, 1.95, .29]);
      const orbit = mesh(body, ring, accentMetal, [.42, .32, 1], [.7, 1.07, .23], [.4, .1, -.4]);
      mesh(body, sphere, glow, [.09, .09, .09], [.7, 1.07, .23]);
      mesh(body, sphere, glow, [.055, .055, .055], [1.03, 1.14, .28]);
      orbit.name = "quant-orbit";
      for (let i = 0; i < 4; i++) mesh(body, box, glow, [.042, .04 + i * .035, .032], [-.15 + i * .095, 1.32, .37]);
    } else if (spec.role === "RISK") {
      const shape = new THREE.Shape(); shape.moveTo(0, .34); shape.lineTo(.28, .2); shape.lineTo(.24, -.15); shape.lineTo(0, -.36); shape.lineTo(-.24, -.15); shape.lineTo(-.28, .2); shape.closePath();
      const shieldGeo = resource(new THREE.ExtrudeGeometry(shape, {depth: .045, bevelEnabled: true, bevelThickness: .025, bevelSize: .025, bevelSegments: 2, steps: 1}));
      mesh(body, shieldGeo, accentMetal, [1, 1, 1], [-.62, 1.06, .34], [0, -.12, -.05]);
      mesh(body, box, glow, [.045, .26, .028], [-.62, 1.08, .411]);
      mesh(body, box, glow, [.2, .04, .028], [-.62, 1.12, .414]);
      mesh(body, box, accentMetal, [.43, .065, .08], [0, 2.12, .18]);
    } else if (spec.role === "EXECUTION_MONITOR") {
      mesh(body, box, graphite, [.1, .58, .12], [.32, 1.88, 0]);
      mesh(body, box, glow, [.035, .28, .035], [.38, 1.95, .045]);
      mesh(body, box, accentMetal, [.2, .035, .08], [.2, 1.75, .26]);
      const monitor = mesh(body, box, darkMetal, [.5, .32, .045], [.68, 1.12, .29], [0, -.2, .1]);
      const screen = new THREE.Group(); screen.position.copy(monitor.position); screen.rotation.copy(monitor.rotation); body.add(screen);
      line(screen, [new THREE.Vector3(-.19, -.015, .04), new THREE.Vector3(-.12, -.015, .04), new THREE.Vector3(-.07, .07, .04), new THREE.Vector3(-.02, -.09, .04), new THREE.Vector3(.04, .08, .04), new THREE.Vector3(.1, -.015, .04), new THREE.Vector3(.19, -.015, .04)], spec.color, 1);
    } else if (spec.role === "AUDIT") {
      mesh(body, cylinder, accentMetal, [.29, .08, .29], [0, 2.12, -.01]);
      mesh(body, box, graphite, [.38, .15, .06], [0, 1.95, .27]);
      for (const side of [-1, 1]) mesh(body, ring, glow, [.082, .082, 1], [side * .1, 1.95, .32]);
      mesh(body, box, platinum, [.36, .45, .07], [.66, .96, .26], [0, -.1, .13]);
      mesh(body, box, glow, [.13, .035, .026], [.59, .95, .32], [0, 0, -.65]);
      mesh(body, box, glow, [.24, .035, .026], [.72, 1, .32], [0, 0, .85]);
    }
    station.traverse(object => {object.userData.role = spec.role; if (object instanceof THREE.Mesh) selectable.push(object);});
    const labelAnchor = new THREE.Object3D();
    if (spec.role === "NAYAK") labelAnchor.position.set(-1.04, 1.5, .2);
    else if (spec.role === "SUPERVISOR") labelAnchor.position.set(1.02, 1.14, .2);
    else labelAnchor.position.set(0, -.1, .86);
    station.add(labelAnchor);
    const label = document.createElement("div"); label.className = "figure-label";
    const name = document.createElement("strong"), status = document.createElement("small");
    name.textContent = spec.name.toUpperCase(); status.textContent = "WAITING"; label.append(name, status);
    document.querySelector("#scene-labels")!.append(label); labels.set(spec.role, label);
    figures.set(spec.role, {group: body, halo, glow, haloMat, labelAnchor});
  }
  root.append(canvas);
  const raycaster = new THREE.Raycaster();
  const pointer = new THREE.Vector2();
  let down = {x: 0, y: 0};
  const pointerDown = (event: PointerEvent) => {down = {x: event.clientX, y: event.clientY};};
  const pointerUp = (event: PointerEvent) => {
    if (Math.hypot(event.clientX - down.x, event.clientY - down.y) > 6) return;
    const bounds = canvas.getBoundingClientRect();
    pointer.set(((event.clientX - bounds.left) / bounds.width) * 2 - 1, -((event.clientY - bounds.top) / bounds.height) * 2 + 1);
    raycaster.setFromCamera(pointer, camera);
    const hit = raycaster.intersectObjects(selectable, false)[0];
    if (hit?.object.userData.role) selectRole(hit.object.userData.role as DeskRole);
  };
  canvas.addEventListener("pointerdown", pointerDown); canvas.addEventListener("pointerup", pointerUp);
  let inView = true, contextLost = false, stopped = false, animation = 0, lastFrame = 0;
  const vector = new THREE.Vector3();
  render = () => {
    if (contextLost || stopped || root.clientWidth === 0) return;
    renderer.render(scene, camera);
    for (const spec of roles) {
      const figure = figures.get(spec.role)!, label = labels.get(spec.role)!;
      figure.labelAnchor.getWorldPosition(vector); vector.project(camera);
      label.style.left = `${(vector.x * .5 + .5) * root.clientWidth}px`;
      label.style.top = `${(-vector.y * .5 + .5) * root.clientHeight}px`;
      label.style.opacity = vector.z < 1 && vector.x > -1 && vector.x < 1 && vector.y > -1 && vector.y < 1 ? "1" : "0";
    }
  };
  updateScene = dto => {
    for (const spec of roles) {
      const figure = figures.get(spec.role)!;
      const inspected = spec.role === selected;
      const working = spec.role === dto?.institution?.active_role;
      figure.haloMat.opacity = working ? 1 : inspected ? .78 : .29;
      figure.glow.emissiveIntensity = working ? 1.35 : inspected ? .7 : .35;
    }
    render?.();
  };
  const tick = (time: number) => {
    animation = 0;
    if (stopped || contextLost || document.hidden || !inView || reducedMotion.matches) return;
    // Decorative idle motion only: status and research progress always come from the native bridge.
    if (time - lastFrame > 1000 / 24) {
      for (const spec of roles) {
        const figure = figures.get(spec.role)!;
        figure.group.rotation.y = Math.sin(time * .00023 + roles.indexOf(spec)) * .035;
      }
      render?.(); lastFrame = time;
    }
    animation = requestAnimationFrame(tick);
  };
  const start = () => {if (!animation && !stopped && !contextLost && !document.hidden && inView && !reducedMotion.matches) animation = requestAnimationFrame(tick); else render?.();};
  const visibility = () => {if (document.hidden && animation) {cancelAnimationFrame(animation); animation = 0;} else start();};
  const motion = () => {if (animation) cancelAnimationFrame(animation); animation = 0; start();};
  document.addEventListener("visibilitychange", visibility); reducedMotion.addEventListener("change", motion);
  const intersection = new IntersectionObserver(entries => {inView = entries[0]?.isIntersecting ?? true; if (!inView && animation) {cancelAnimationFrame(animation); animation = 0;} else start();});
  intersection.observe(root);
  let sizingFrame = 0, pendingWidth = 0, pendingHeight = 0, sizedWidth = 0, sizedHeight = 0;
  const resize = new ResizeObserver(entries => {
    const rect = entries[0]?.contentRect;
    if (!rect || rect.width < 1 || rect.height < 1) return;
    pendingWidth = Math.round(rect.width); pendingHeight = Math.round(rect.height);
    if (sizingFrame || (pendingWidth === sizedWidth && pendingHeight === sizedHeight)) return;
    // Qt WebEngine must finish its layout delivery before renderer/camera/label writes.
    sizingFrame = requestAnimationFrame(() => {
      sizingFrame = 0;
      if (stopped || contextLost || (pendingWidth === sizedWidth && pendingHeight === sizedHeight)) return;
      sizedWidth = pendingWidth; sizedHeight = pendingHeight;
      renderer.setSize(sizedWidth, sizedHeight, false); camera.aspect = sizedWidth / sizedHeight;
      // Keep the entire nine-agent chamber in frame even in a narrow native Qt panel.
      camera.fov = camera.aspect < 1.15 ? 43 : 33;
      const distance = Math.max(1, 15.2 / (2 * Math.tan(THREE.MathUtils.degToRad(camera.fov / 2)) * camera.aspect * initialPosition.distanceTo(initialTarget)));
      camera.position.copy(initialTarget).add(initialPosition.clone().sub(initialTarget).multiplyScalar(distance));
      controls.update(); camera.updateProjectionMatrix(); render?.();
    });
  }); resize.observe(root);
  resetCamera = () => {
    controls.target.copy(initialTarget);
    const distance = Math.max(1, 15.2 / (2 * Math.tan(THREE.MathUtils.degToRad(camera.fov / 2)) * camera.aspect * initialPosition.distanceTo(initialTarget)));
    camera.position.copy(initialTarget).add(initialPosition.clone().sub(initialTarget).multiplyScalar(distance));
    controls.update(); render?.();
  };
  controls.addEventListener("change", () => render?.());
  const lost = (event: Event) => {event.preventDefault(); contextLost = true; if (animation) cancelAnimationFrame(animation); animation = 0; fallback.textContent = "3D context paused · all agent inspectors remain available below";};
  const restored = () => {contextLost = false; resize.unobserve(root); resize.observe(root); fallback.textContent = "3D presentation · all research states are reported by the lab"; start();};
  canvas.addEventListener("webglcontextlost", lost); canvas.addEventListener("webglcontextrestored", restored);
  dispose = () => {
    stopped = true; if (animation) cancelAnimationFrame(animation);
    if (sizingFrame) cancelAnimationFrame(sizingFrame);
    resize.disconnect(); intersection.disconnect(); controls.dispose();
    document.removeEventListener("visibilitychange", visibility); reducedMotion.removeEventListener("change", motion);
    canvas.removeEventListener("pointerdown", pointerDown); canvas.removeEventListener("pointerup", pointerUp);
    canvas.removeEventListener("webglcontextlost", lost); canvas.removeEventListener("webglcontextrestored", restored);
    resources.forEach(item => item.dispose()); renderer.dispose(); canvas.remove();
    document.querySelector("#scene-labels")!.replaceChildren(); render = undefined; updateScene = undefined;
  };
  start(); updateScene();
}

function display(dto: DeskDTO): void {
  latest = dto;
  document.querySelector("#institution-state")!.textContent = dto.institution?.status.replaceAll("_", " ") ?? "CONNECTED";
  document.querySelector("#institution-summary")!.textContent = dto.institution?.summary ?? "Native research state is connected. Open a specialist to inspect its frozen reports.";
  document.querySelector("#system-state")!.textContent = dto.debate ? `${dto.debate.status} · ${dto.debate.critiques} critiques / ${dto.debate.rebuttals} rebuttals` : "No frozen Bull / Bear debate yet";
  document.querySelector<HTMLButtonElement>("#debate-transcript")!.disabled = !dto.debate;
  const decision = dto.adjudication;
  document.querySelector("#adjudication")!.textContent = decision ? `${decision.outcome} · ${decision.no_trade ? "NO_TRADE" : "RESEARCH ONLY"} · Bull ${decision.bull_score.toFixed(2)} / Bear ${decision.bear_score.toFixed(2)} · ${decision.blocker_count} blockers${decision.expired ? " · EXPIRED" : ""}` : "Deterministic adjudication not evaluated";
  const scores = document.querySelector<HTMLElement>("#score-components")!; scores.replaceChildren(); scores.hidden = !decision;
  for (const component of decision?.components ?? []) {
    const label = document.createElement("label"), meter = document.createElement("meter");
    label.textContent = `${component.role} · ${component.name} · ${component.status}`;
    meter.min = 0; meter.max = 1; meter.value = component.value ?? 0;
    meter.setAttribute("aria-label", `${component.role} ${component.name}: ${component.status}`); label.append(meter); scores.append(label);
  }
  document.querySelector("#decision-warnings")!.textContent = decision?.warnings.join(" · ") ?? "";
  document.querySelector("#evidence-total")!.textContent = `${dto.evidence.length} frozen artifacts`;
  const evidence = document.querySelector("#evidence")!; evidence.replaceChildren();
  for (const item of dto.evidence) {
    const li = document.createElement("li"), button = document.createElement("button"); button.type = "button";
    button.textContent = `${item.label} · ${item.status}`; button.addEventListener("click", () => navigate("open_evidence", item.artifact_hash)); li.append(button); evidence.append(li);
  }
  updateSelection();
}

document.querySelector("#inspect-role")!.addEventListener("click", () => navigate("select_role", selected));
document.querySelector("#reset-view")!.addEventListener("click", () => resetCamera?.());
document.querySelector("#debate-transcript")!.addEventListener("click", () => {
  if (latest?.adjudication) navigate("open_adjudication", latest.adjudication.decision_hash);
  else if (latest?.debate) navigate("open_debate", latest.debate.transcript_hash);
});
window.addEventListener("pagehide", () => dispose?.());
try {setupScene();} catch {fallback.textContent = "3D unavailable · all agents remain accessible through their role cards";}
updateSelection(); connect(display);
