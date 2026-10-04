export type AgentState = {agent: "BULL" | "BEAR"; state: string; task_label: string; completed_tools: number};
export type EvidenceNode = {artifact_hash: string; label: string; status: string};
export type DeskDTO = {agents: AgentState[]; evidence: EvidenceNode[]; safety: {ai_order_authority: false; live_trading: false}};
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

export function navigate(intent: "select_agent" | "open_evidence", identity: string): void {
  bridge?.navigate(intent, identity);
}
