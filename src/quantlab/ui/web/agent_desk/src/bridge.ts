export type AgentState = {agent: "BULL" | "BEAR"; state: string; task_label: string; completed_tools: number};
export type EvidenceNode = {artifact_hash: string; label: string; status: string};
export type EvidenceEdge = {agent: "BULL" | "BEAR"; evidence_hash: string; relation: "SUPPORT" | "CONTRADICTION" | "CRITIQUE_REFERENCE" | "REQUESTED"};
export type DebateState = {transcript_hash: string; status: "COMPLETE" | "INCOMPLETE" | "STALE"; critiques: number; rebuttals: number; edges: EvidenceEdge[]; adjudication: "NOT_EVALUATED"};
export type ComponentState = {role: "BULL" | "BEAR"; name: string; status: string; value: number | null; points: number};
export type AdjudicationState = {decision_hash: string; transcript_hash: string; outcome: string; no_trade: boolean; bull_score: number; bear_score: number; blocker_count: number; expired: boolean; components: ComponentState[]; warnings: string[]; execution_authority: false};
export type DeskDTO = {agents: AgentState[]; evidence: EvidenceNode[]; debate?: DebateState | null; adjudication?: AdjudicationState | null; safety: {ai_order_authority: false; live_trading: false}};
type NativeBridge = {presentation: string; presentationChanged: {connect: (fn: (raw: string) => void) => void}; navigate: (intent: string, identity: string) => void};
declare global {
  interface Window {
    qt?: {webChannelTransport: unknown};
    QWebChannel?: new (transport: unknown, ready: (channel: {objects: {agentDesk: NativeBridge}}) => void) => unknown;
  }
}
let bridge: NativeBridge | undefined;

function parse(raw: string): DeskDTO | undefined {
  try {
    if (raw.length > 200000) return;
    const dto = JSON.parse(raw) as DeskDTO;
    if (!Array.isArray(dto.agents) || !Array.isArray(dto.evidence)) return;
    if (dto.safety.ai_order_authority !== false || dto.safety.live_trading !== false) return;
    if (!dto.agents.every(a => ["BULL", "BEAR"].includes(a.agent) && typeof a.state === "string" && typeof a.task_label === "string" && Number.isInteger(a.completed_tools))) return;
    if (!dto.evidence.every(e => /^[a-f0-9]{64}$/.test(e.artifact_hash) && typeof e.label === "string" && typeof e.status === "string")) return;
    if (dto.evidence.length > 40) return;
    if (dto.debate) {
      const d = dto.debate;
      if (!/^[a-f0-9]{64}$/.test(d.transcript_hash) || !["COMPLETE", "INCOMPLETE", "STALE"].includes(d.status) || d.adjudication !== "NOT_EVALUATED") return;
      if (![d.critiques, d.rebuttals].every(n => Number.isInteger(n) && n >= 0 && n <= 2) || !Array.isArray(d.edges) || d.edges.length > 80) return;
      if (!d.edges.every(e => ["BULL", "BEAR"].includes(e.agent) && /^[a-f0-9]{64}$/.test(e.evidence_hash) && ["SUPPORT", "CONTRADICTION", "CRITIQUE_REFERENCE", "REQUESTED"].includes(e.relation) && dto.evidence.some(node => node.artifact_hash === e.evidence_hash))) return;
    }
    if (dto.adjudication) {
      const a = dto.adjudication;
      const outcomes = ["BULL_DOMINANT", "BEAR_DOMINANT", "CONFLICTED", "LOW_CONFIDENCE", "NO_EDGE", "INSUFFICIENT_DATA", "VALIDATION_BLOCKED", "RISK_BLOCKED", "LIQUIDITY_BLOCKED", "NO_TRADE"];
      const score = (v: number) => Number.isFinite(v) && v >= 0 && v <= 100;
      if (!/^[a-f0-9]{64}$/.test(a.decision_hash) || a.transcript_hash !== dto.debate?.transcript_hash || !outcomes.includes(a.outcome) || a.execution_authority !== false) return;
      if (typeof a.no_trade !== "boolean" || typeof a.expired !== "boolean" || !score(a.bull_score) || !score(a.bear_score) || !Number.isInteger(a.blocker_count) || a.blocker_count < 0) return;
      if (!Array.isArray(a.components) || a.components.length > 24 || !a.components.every(c => ["BULL", "BEAR"].includes(c.role) && typeof c.name === "string" && typeof c.status === "string" && score(c.points) && (c.value === null || (Number.isFinite(c.value) && c.value >= 0 && c.value <= 1)))) return;
      if (!Array.isArray(a.warnings) || a.warnings.length > 20 || !a.warnings.every(w => typeof w === "string")) return;
      if (!a.no_trade && (a.blocker_count > 0 || !["BULL_DOMINANT", "BEAR_DOMINANT"].includes(a.outcome))) return;
    }
    return dto;
  } catch { return; }
}

export function connect(onState: (dto: DeskDTO) => void): void {
  if (!window.QWebChannel || !window.qt) return;
  new window.QWebChannel(window.qt.webChannelTransport, channel => {
    bridge = channel.objects.agentDesk;
    const update = (raw: string) => { const dto = parse(raw); if (dto) onState(dto); };
    bridge.presentationChanged.connect(update);
    update(bridge.presentation);
  });
}

export function navigate(intent: "select_agent" | "open_evidence" | "open_debate" | "open_adjudication", identity: string): void {
  bridge?.navigate(intent, identity);
}
