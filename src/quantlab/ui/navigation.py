"""Navigation definitions for Guided and Full Lab modes."""

from __future__ import annotations

from dataclasses import dataclass

from quantlab.app.settings_store import ExperienceMode


@dataclass(frozen=True)
class NavItem:
    key: str
    label: str
    header: bool = False


GUIDED_NAV: list[NavItem] = [
    NavItem("home", "Home"),
    NavItem("learn", "Learn"),
    NavItem("test", "Test"),
    NavItem("journal", "Journal"),
    NavItem("settings", "Settings"),
]

# Quant workflow pipeline: Research → Validate → Execute (+ Lab utilities).
FULL_NAV: list[NavItem] = [
    NavItem("__h_lab", "— Lab —", header=True),
    NavItem("home", "Home"),
    NavItem("journal", "Journal"),
    NavItem("settings", "Settings"),
    NavItem("__h_research", "— Research —", header=True),
    NavItem("data", "Data"),
    NavItem("features", "Features"),
    NavItem("research", "Research"),
    NavItem("orchestration", "Research Control"),
    NavItem("discovery", "Discovery Lab"),
    NavItem("knowledge", "Knowledge Lab"),
    NavItem("alpha", "Alpha Lab"),
    NavItem("market", "Market"),
    NavItem("models", "Adaptive"),
    NavItem("learning", "Model Lab"),
    NavItem("ensemble", "Ensemble Lab"),
    NavItem("ai", "AI Research"),
    NavItem("__h_validate", "— Validate —", header=True),
    NavItem("backtests", "Backtests"),
    NavItem("validation", "Validation"),
    NavItem("compare", "Compare"),
    NavItem("risk", "Risk"),
    NavItem("execution", "Execution Lab"),
    NavItem("capital", "Capital Lab"),
    NavItem("paper", "Paper OMS Lab"),
    NavItem("monitor", "Monitoring Lab"),
    NavItem("tca", "TCA & Capacity Lab"),
    NavItem("econo", "Econometrics Lab"),
    NavItem("certify", "Validation & Certification Lab"),
    NavItem("shadow", "Shadow Trading Lab"),
    NavItem("safety", "Safety & Control Lab"),
    NavItem("promote", "Certification & Promotion Lab"),
    NavItem("rt_data", "Real-Time Data Lab"),
    NavItem("rt_decision", "Real-Time Decision Lab"),
    NavItem("twin", "Digital Twin / Shadow Lab"),
    NavItem("__h_execute", "— Execute —", header=True),
    NavItem("portfolio", "Portfolio"),
    NavItem("broker", "Broker"),
    NavItem("gateway", "Broker Gateway Lab"),
    NavItem("logs", "Logs"),
    NavItem("__h_ops", "— Ops —", header=True),
    NavItem("experiments", "Experiments"),
    NavItem("ops", "Operations Control Lab"),
    NavItem("system", "System"),
]

_NAV_LABELS: dict[str, str] = {
    item.key: item.label for item in (*GUIDED_NAV, *FULL_NAV) if not item.header
}

# Keyboard shortcuts (Meta = ⌘ on macOS, Ctrl on Windows/Linux).
# Home/Market use Shift variants to avoid macOS Hide (⌘H) and Minimize (⌘M).
NAV_SHORTCUTS: dict[str, str] = {
    "home": "Meta+Shift+H",
    "journal": "Meta+J",
    "settings": "Meta+,",
    "data": "Meta+D",
    "features": "Meta+Shift+F",
    "research": "Meta+Shift+R",
    "orchestration": "Meta+Shift+O",
    "discovery": "Meta+Shift+Y",
    "knowledge": "Meta+Shift+N",
    "alpha": "Meta+Shift+A",
    "market": "Meta+Shift+M",
    "models": "Meta+Shift+U",
    "learning": "Meta+Shift+L",
    "ensemble": "Meta+Shift+E",
    "ai": "Meta+Shift+I",
    "backtests": "Meta+B",
    "validation": "Meta+V",
    "compare": "Meta+Shift+C",
    "risk": "Meta+Shift+K",
    "execution": "Meta+Shift+X",
    "capital": "Meta+Shift+W",
    "paper": "Meta+Shift+Q",
    "monitor": "Meta+Shift+Z",
    "tca": "Meta+Alt+T",
    "econo": "Meta+Alt+E",
    "certify": "Meta+Alt+C",
    "shadow": "Meta+Alt+S",
    "safety": "Meta+Alt+G",
    "promote": "Meta+Alt+P",
    "rt_data": "Meta+Alt+F",
    "rt_decision": "Meta+Alt+N",
    "twin": "Meta+Alt+W",
    "ops": "Meta+Alt+O",
    "portfolio": "Meta+P",
    "broker": "Meta+Shift+B",
    "gateway": "Meta+Alt+Y",
    "logs": "Meta+Shift+G",
    "experiments": "Meta+Shift+T",
    "system": "Meta+Shift+S",
}

# Focus the sidebar filter box (Full Lab).
NAV_FILTER_SHORTCUT = "Meta+U"

# macOS system shortcuts that previously collided — documented for Settings help.
SHORTCUT_CONFLICT_NOTES: tuple[str, ...] = (
    "Home uses ⌘⇧H (not ⌘H — macOS Hide window).",
    "Market uses ⌘⇧M (not ⌘M — macOS Minimize window).",
    "⌘K opens the command palette; ⌘U focuses sidebar filter.",
)

# Collapsed icon rail (single glyph per page).
NAV_RAIL_ICONS: dict[str, str] = {
    "home": "⌂",
    "journal": "✎",
    "settings": "⚙",
    "data": "⛁",
    "features": "ƒ",
    "research": "?",
    "orchestration": "⎈",
    "discovery": "∑",
    "knowledge": "◉",
    "alpha": "α",
    "market": "◎",
    "models": "↻",
    "learning": "μ",
    "ensemble": "⊕",
    "ai": "✦",
    "backtests": "▶",
    "validation": "✓",
    "compare": "⇄",
    "risk": "⚠",
    "execution": "⏱",
    "capital": "₹",
    "paper": "▤",
    "monitor": "▣",
    "tca": "⌁",
    "econo": "ρ",
    "certify": "☑",
    "shadow": "◐",
    "safety": "⊘",
    "promote": "⬡",
    "rt_data": "◷",
    "rt_decision": "◬",
    "twin": "⧉",
    "ops": "⎈",
    "portfolio": "◫",
    "broker": "⎔",
    "gateway": "▦",
    "logs": "≡",
    "experiments": "⌗",
    "system": "●",
}

NAV_SECTION_RAIL: dict[str, str] = {
    "__h_lab": "L",
    "__h_research": "R",
    "__h_validate": "V",
    "__h_execute": "X",
    "__h_ops": "O",
}

NAV_STATUS_KEYS: frozenset[str] = frozenset({"broker", "logs", "system"})

NAV_KEYWORDS: dict[str, tuple[str, ...]] = {
    "home": ("dashboard", "start", "greeting"),
    "learn": ("glossary", "sharpe", "lessons", "tutorial"),
    "test": ("wizard", "backtest", "momentum", "experiment"),
    "journal": ("notes", "notebook", "diary"),
    "settings": ("prefs", "theme", "config"),
    "market": ("watchlist", "nse", "nifty", "instruments", "quotes"),
    "data": ("fabric", "dataset", "catalog", "historical"),
    "features": ("feature", "ic", "momentum_20", "factor", "signal"),
    "research": ("hypothesis", "pipeline", "notebook", "orchestration"),
    "alpha": ("alpha", "signal", "ic", "strategy"),
    "models": ("adaptive", "online"),
    "learning": ("model", "statistical", "ols"),
    "ensemble": ("combine", "meta", "stack"),
    "backtests": ("backtest", "equity", "run", "simulation"),
    "validation": ("validate", "walk-forward", "gate", "robustness", "oos"),
    "compare": ("compare", "side", "diff", "metrics"),
    "portfolio": ("weights", "construction", "holdings", "pnl"),
    "risk": ("firewall", "covariance", "factor", "margin", "stress"),
    "execution": ("orders", "oms", "fills", "microstructure", "slippage", "impact"),
    "capital": (
        "capital",
        "allocation",
        "kelly",
        "sizing",
        "budget",
        "decision",
        "target",
    ),
    "paper": (
        "paper",
        "oms",
        "order",
        "fill",
        "reconciliation",
        "tca",
        "simulate",
    ),
    "monitor": (
        "monitor",
        "performance",
        "attribution",
        "drift",
        "drawdown",
        "feedback",
    ),
    "tca": (
        "tca",
        "shortfall",
        "capacity",
        "fragility",
        "calibration",
        "slippage",
    ),
    "econo": (
        "econometrics",
        "stationarity",
        "granger",
        "cointegration",
        "var",
        "causal",
    ),
    "certify": (
        "certification",
        "model-risk",
        "waiver",
        "prelive",
        "reproduce",
        "checklist",
    ),
    "shadow": (
        "shadow",
        "paper-production",
        "freshness",
        "checkpoint",
        "replay",
        "kill-switch",
    ),
    "safety": (
        "safety",
        "kill-switch",
        "authorization",
        "gateway",
        "live-disabled",
        "g15",
    ),
    "promote": (
        "promotion",
        "release-gate",
        "live-certification",
        "release-eligible",
        "waiver",
        "manifest",
    ),
    "rt_data": (
        "realtime",
        "observe-only",
        "market-state",
        "freshness",
        "sequence",
        "snapshot",
    ),
    "rt_decision": (
        "realtime-decision",
        "target-portfolio",
        "abstention",
        "strategy-release",
        "decision-not-order",
    ),
    "twin": (
        "digital-twin",
        "replay",
        "checkpoint",
        "counterfactual",
        "failure-injection",
        "shadow-validation",
    ),
    "ops": (
        "ops",
        "supervisor",
        "backup",
        "readiness",
        "doctor",
        "control-plane",
    ),
    "broker": ("zerodha", "openalgo", "connect", "routing"),
    "gateway": (
        "broker-gateway",
        "account-state",
        "read-only",
        "reconciliation",
        "snapshot",
        "no-order-routing",
    ),
    "ai": ("chat", "nayak", "llm", "assistant"),
    "experiments": ("ledger", "history", "runs"),
    "system": ("health", "status"),
    "logs": ("log", "trace", "debug", "telemetry", "error"),
    "orchestration": ("orchestration", "hypothesis", "family", "control", "discover"),
    "discovery": ("discovery", "genetic", "symbolic", "expression", "grammar", "genome"),
    "knowledge": (
        "knowledge",
        "genealogy",
        "evidence",
        "claim",
        "memory",
        "contradiction",
        "dead-end",
        "snapshot",
    ),
}

_COLLAPSIBLE_SECTIONS = frozenset(
    {
        "__h_lab",
        "__h_research",
        "__h_validate",
        "__h_execute",
        "__h_ops",
    }
)


def shortcut_label(key: str) -> str:
    seq = NAV_SHORTCUTS.get(key, "")
    if not seq:
        return ""
    return (
        seq.replace("Meta+Shift+", "⌘⇧")
        .replace("Meta+", "⌘")
        .replace("Ctrl+Shift+", "Ctrl+⇧")
        .replace("Ctrl+", "Ctrl+")
    )


def nav_tooltip(key: str, label: str) -> str:
    hint = shortcut_label(key)
    return f"{label}  ({hint})" if hint else label


def breadcrumb_for_key(key: str) -> str:
    section, page = breadcrumb_parts(key)
    return f"{section} / {page}" if section else page


def breadcrumb_parts(key: str) -> tuple[str, str]:
    section = ""
    for item in FULL_NAV:
        if item.header:
            if item.key in _COLLAPSIBLE_SECTIONS:
                section = item.label.strip("— ▾▸").strip()
        elif item.key == key:
            break
    label = _NAV_LABELS.get(key, key.title())
    return section, label


def nav_section_label_for_page(key: str) -> str:
    section, _ = breadcrumb_parts(key)
    return section


def nav_section_header_for_page(key: str) -> str | None:
    section_header: str | None = None
    for item in FULL_NAV:
        if item.header and item.key in _COLLAPSIBLE_SECTIONS:
            section_header = item.key
        elif item.key == key:
            return section_header
    return None


def filter_collapsed_sections(items: list[NavItem], collapsed: frozenset[str]) -> list[NavItem]:
    if not collapsed:
        return list(items)
    result: list[NavItem] = []
    skipping = False
    for item in items:
        if item.header:
            if item.key in _COLLAPSIBLE_SECTIONS:
                skipping = item.key in collapsed
                marker = "▸" if skipping else "▾"
                label = item.label.replace("—", marker, 1)
                result.append(NavItem(item.key, label, header=True))
            else:
                result.append(item)
            continue
        if not skipping:
            result.append(item)
    return result


def toggle_collapsed_section(collapsed: list[str], section_key: str) -> list[str]:
    updated = list(collapsed)
    if section_key in updated:
        updated.remove(section_key)
    else:
        updated.append(section_key)
    return updated


def nav_item_matches(item: NavItem, query: str) -> bool:
    if item.header:
        return False
    q = query.strip().lower()
    if not q:
        return True
    if q in item.key.lower() or q in item.label.lower():
        return True
    return any(q in token for token in NAV_KEYWORDS.get(item.key, ()))


def filter_nav_items(items: list[NavItem], query: str) -> list[NavItem]:
    cleaned = query.strip()
    if not cleaned:
        return list(items)
    matches = [item for item in items if nav_item_matches(item, cleaned)]
    if not matches:
        return [NavItem("__h_none", "— No matches —", header=True)]
    if len(matches) == 1:
        return matches
    return [NavItem("__h_results", f"— {len(matches)} matches —", header=True), *matches]


def nav_for_mode(mode: ExperienceMode) -> list[NavItem]:
    if mode is ExperienceMode.GUIDED:
        return list(GUIDED_NAV)
    return list(FULL_NAV)


def nav_status_prefix(key: str, *, broker: str, system: str, logs_has_error: bool) -> str:
    if key not in NAV_STATUS_KEYS:
        return ""
    if key == "broker":
        if "DISCONNECT" in broker.upper() or "BLOCK" in broker.upper():
            return "🔴 "
        return "🟢 "
    if key == "system":
        if "FAIL" in system.upper():
            return "🔴 "
        if "HEALTH" in system.upper():
            return "🟢 "
        return "🟡 "
    if key == "logs":
        return "🔴 " if logs_has_error else "🟢 "
    return ""
