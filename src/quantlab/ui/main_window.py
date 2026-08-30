from __future__ import annotations

from PySide6.QtCore import Qt, QTimer
from PySide6.QtGui import QAction, QCloseEvent, QKeySequence, QShortcut, QShowEvent
from PySide6.QtWidgets import (
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QListWidget,
    QListWidgetItem,
    QMainWindow,
    QMessageBox,
    QPushButton,
    QScrollArea,
    QSizePolicy,
    QStackedWidget,
    QVBoxLayout,
    QWidget,
)

from quantlab.app.assistant import ContextNudge, FocusAction, NayakAssistant
from quantlab.app.bootstrap import ApplicationRuntime
from quantlab.app.mode import AppMode
from quantlab.app.settings_store import ExperienceMode, UiDensity, UiTheme
from quantlab.core.errors import SafetyError
from quantlab.ui.command_registry import build_palette_commands
from quantlab.ui.navigation import (
    _COLLAPSIBLE_SECTIONS,
    NAV_FILTER_SHORTCUT,
    NAV_RAIL_ICONS,
    NAV_SECTION_RAIL,
    NAV_SHORTCUTS,
    NavItem,
    breadcrumb_parts,
    filter_collapsed_sections,
    filter_nav_items,
    nav_for_mode,
    nav_section_header_for_page,
    nav_section_label_for_page,
    nav_status_prefix,
    nav_tooltip,
    shortcut_label,
    toggle_collapsed_section,
)
from quantlab.ui.page_scroll import wrap_page_scroll
from quantlab.ui.pages.adaptive import AdaptivePage
from quantlab.ui.pages.ai_research import AiResearchPage
from quantlab.ui.pages.alpha import AlphaPage
from quantlab.ui.pages.backtest import BacktestPage
from quantlab.ui.pages.broker import BrokerPage
from quantlab.ui.pages.broker_gateway_lab import BrokerGatewayLabPage
from quantlab.ui.pages.capital_lab import CapitalLabPage
from quantlab.ui.pages.certification_lab import CertificationLabPage
from quantlab.ui.pages.compare import ComparePage
from quantlab.ui.pages.data import DataPage
from quantlab.ui.pages.digital_twin_lab import DigitalTwinLabPage
from quantlab.ui.pages.discovery_lab import DiscoveryLabPage
from quantlab.ui.pages.econometrics_lab import EconometricsLabPage
from quantlab.ui.pages.ensemble import EnsemblePage
from quantlab.ui.pages.execution_lab import ExecutionLabPage
from quantlab.ui.pages.experiments import ExperimentsPage
from quantlab.ui.pages.features import FeaturesPage
from quantlab.ui.pages.home import HomePage
from quantlab.ui.pages.journal import JournalPage
from quantlab.ui.pages.knowledge_lab import KnowledgeLabPage
from quantlab.ui.pages.learn import LearnPage
from quantlab.ui.pages.learning import LearningPage
from quantlab.ui.pages.logs import LogsPage
from quantlab.ui.pages.market import MarketPage
from quantlab.ui.pages.monitoring_lab import MonitoringLabPage
from quantlab.ui.pages.ops_lab import OpsLabPage
from quantlab.ui.pages.paper_oms_lab import PaperOMSLabPage
from quantlab.ui.pages.portfolio import PortfolioPage
from quantlab.ui.pages.promotion_lab import PromotionLabPage
from quantlab.ui.pages.realtime_data_lab import RealTimeDataLabPage
from quantlab.ui.pages.realtime_decision_lab import RealTimeDecisionLabPage
from quantlab.ui.pages.research import ResearchPage
from quantlab.ui.pages.research_control import ResearchControlPage
from quantlab.ui.pages.risk import RiskPage
from quantlab.ui.pages.safety_lab import SafetyLabPage
from quantlab.ui.pages.settings_page import SettingsPage
from quantlab.ui.pages.shadow_lab import ShadowLabPage
from quantlab.ui.pages.system import SystemPage
from quantlab.ui.pages.tca_lab import TCALabPage
from quantlab.ui.pages.test import BacktestWizardPage
from quantlab.ui.pages.validation import ValidationPage
from quantlab.ui.theme import apply_theme, stylesheet_for
from quantlab.ui.widgets.breadcrumb_bar import BreadcrumbBar
from quantlab.ui.widgets.catalog_page import CatalogLabPage
from quantlab.ui.widgets.command_palette import CommandPalette
from quantlab.ui.widgets.data_table import wire_journal_links
from quantlab.ui.widgets.footer_status import FooterStatusBar
from quantlab.ui.widgets.lab_shell import LabPageShell
from quantlab.ui.widgets.live_confirm_dialog import LiveConfirmDialog
from quantlab.ui.widgets.notification_strip import NotificationStrip
from quantlab.ui.window_geometry import clamp_to_screen


class MainWindow(QMainWindow):
    def __init__(self, runtime: ApplicationRuntime) -> None:
        super().__init__()
        self.runtime = runtime
        self._assistant = NayakAssistant(runtime)
        prefs = runtime.ui_settings.current

        self.setObjectName("quantlab-main")
        self.setWindowTitle(f"NAYAK QUANT LAB  {runtime.version}  —  {runtime.mode.value.upper()}")
        from PySide6.QtWidgets import QApplication

        app = QApplication.instance()
        apply_theme(app if isinstance(app, QApplication) else None, prefs.theme)
        self.setStyleSheet(stylesheet_for(prefs.theme))
        self.resize(prefs.width, prefs.height)
        if prefs.x is not None and prefs.y is not None:
            self.move(prefs.x, prefs.y)
        clamp_to_screen(self)
        self.setMinimumSize(960, 600)

        self._live_banner = QLabel(
            "LIVE — orders may result in real financial losses. New live orders are still gated."
        )
        self._live_banner.setObjectName("liveBanner")
        self._live_banner.setVisible(runtime.mode is AppMode.LIVE)

        brand = QLabel("NAYAK QUANT LAB")
        brand.setObjectName("brand")
        self._greeting_chip = QLabel()
        self._greeting_chip.setObjectName("nayakVoice")

        self._guided_btn = QPushButton("Guided Lab")
        self._guided_btn.setObjectName("modeToggle")
        self._guided_btn.setCheckable(True)
        self._full_btn = QPushButton("Full Lab")
        self._full_btn.setObjectName("modeToggle")
        self._full_btn.setCheckable(True)
        if prefs.experience_mode is ExperienceMode.FULL:
            self._full_btn.setChecked(True)
        else:
            self._guided_btn.setChecked(True)
        self._guided_btn.clicked.connect(lambda: self._set_experience_mode(ExperienceMode.GUIDED))
        self._full_btn.clicked.connect(lambda: self._set_experience_mode(ExperienceMode.FULL))

        self._mode_badge = QLabel(f"Mode: {runtime.mode.value.upper()}")
        self._mode_badge.setObjectName(
            "modeBadgeLive" if runtime.mode is AppMode.LIVE else "modeBadge"
        )

        header = QHBoxLayout()
        header.addWidget(brand)
        header.addSpacing(16)
        header.addWidget(self._greeting_chip)
        header.addStretch()
        header.addWidget(self._guided_btn)
        header.addWidget(self._full_btn)
        header.addWidget(self._mode_badge)
        header.addWidget(QLabel(f"v{runtime.version}"))

        self._context_host = QWidget()
        self._context_host.setObjectName("contextHost")
        context_layout = QHBoxLayout(self._context_host)
        context_layout.setContentsMargins(8, 0, 8, 0)
        self._context_strip = QLabel()
        self._context_strip.setObjectName("contextStrip")
        self._context_strip.setWordWrap(True)
        self._context_action = QPushButton()
        self._context_action.setObjectName("primary")
        self._context_action.setVisible(False)
        self._context_action.clicked.connect(self._run_context_action)
        context_layout.addWidget(self._context_strip, 1)
        context_layout.addWidget(self._context_action)

        self._breadcrumb = BreadcrumbBar(on_section_click=self._toggle_breadcrumb_section)

        self._notification_strip = NotificationStrip(on_dismiss=self._ack_notifications)
        self._dismissed_nudges: set[str] = set()
        self._notification_ack = len(runtime.notifications)

        self.nav = QListWidget()
        self.nav.setObjectName("nav-list")
        self.nav.setFixedWidth(196)
        self.nav.setSizePolicy(QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Expanding)
        self.nav.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOn)
        self.nav.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.nav.setVerticalScrollMode(QListWidget.ScrollMode.ScrollPerPixel)

        self._nav_search = QLineEdit()
        self._nav_search.setObjectName("navSearch")
        self._nav_search.setPlaceholderText("Search pages…")
        self._nav_search.setClearButtonEnabled(True)
        self._nav_search.textChanged.connect(self._apply_nav_search)
        self._nav_search.returnPressed.connect(self._activate_first_nav_match)

        self._nav_toggle = QPushButton("«")
        self._nav_toggle.setObjectName("navToggle")
        self._nav_toggle.setFixedWidth(28)
        self._nav_toggle.setToolTip("Collapse sidebar")
        self._nav_toggle.clicked.connect(self._toggle_sidebar_collapsed)

        nav_top = QHBoxLayout()
        nav_top.setSpacing(4)
        nav_top.addWidget(self._nav_toggle)
        nav_top.addWidget(self._nav_search, 1)

        nav_column = QVBoxLayout()
        nav_column.setSpacing(4)
        nav_column.setContentsMargins(0, 0, 0, 0)
        nav_column.addLayout(nav_top)
        nav_column.addWidget(self.nav, 1)

        self._nav_host = QWidget()
        self._nav_host.setObjectName("navHost")
        self._nav_host.setFixedWidth(212)
        self._nav_host.setLayout(nav_column)
        self._nav_host.setSizePolicy(QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Expanding)

        self._base_nav_items: list[NavItem] = []

        self.stack = QStackedWidget()
        self.home = HomePage(
            runtime,
            on_action=self._handle_focus_action,
            on_journal=self._goto_journal_entry,
            on_nav=self._select_nav,
        )
        self.learn = LearnPage(runtime, on_nav=self._select_nav)
        self.test = BacktestWizardPage(
            runtime,
            on_done=self._after_backtest,
            on_journal=self._goto_journal_entry,
            on_compare=self._handoff_compare,
            on_validation=self._handoff_validation,
            on_full_lab=lambda: self._set_experience_mode(ExperienceMode.FULL),
        )
        self.journal = JournalPage(
            runtime,
            on_open_full=lambda: self._set_experience_mode(ExperienceMode.FULL),
        )
        self.settings = SettingsPage(
            runtime,
            on_theme_change=self._apply_theme,
            on_name_change=self._refresh_assistant_surfaces,
            on_density_change=self._apply_density,
        )
        self.ai_research = AiResearchPage(runtime)
        self.market = MarketPage(runtime)
        self.data = DataPage(runtime)
        self.backtest = BacktestPage(runtime, on_done=self._after_backtest)
        self.validation = ValidationPage(runtime, on_done=self._after_validation)
        self.compare = ComparePage(runtime)
        self.research = ResearchPage(on_run=self._goto_backtest_and_run)
        self.orchestration = ResearchControlPage(runtime)
        self.discovery_lab = DiscoveryLabPage(runtime)
        self.knowledge_lab = KnowledgeLabPage(runtime)
        self.capital_lab = CapitalLabPage(runtime)
        self.paper_oms_lab = PaperOMSLabPage(runtime)
        self.monitoring_lab = MonitoringLabPage(runtime)
        self.tca_lab = TCALabPage(runtime)
        self.econometrics_lab = EconometricsLabPage(runtime)
        self.certification_lab = CertificationLabPage(runtime)
        self.shadow_lab = ShadowLabPage(runtime)
        self.safety_lab = SafetyLabPage(runtime)
        self.promotion_lab = PromotionLabPage(runtime)
        self.realtime_data_lab = RealTimeDataLabPage(runtime)
        self.realtime_decision_lab = RealTimeDecisionLabPage(runtime)
        self.digital_twin_lab = DigitalTwinLabPage(runtime)
        self.ops_lab = OpsLabPage(runtime)
        self.features = FeaturesPage(runtime)
        self.alpha = AlphaPage(runtime)
        self.adaptive = AdaptivePage(runtime)
        self.learning = LearningPage(runtime)
        self.ensemble = EnsemblePage(runtime)
        self.execution_lab = ExecutionLabPage(runtime)
        self.portfolio = PortfolioPage(runtime)
        self.risk = RiskPage(runtime)
        self.experiments = ExperimentsPage(runtime)
        self.system = SystemPage(runtime)
        self.logs = LogsPage(runtime)
        self.broker = BrokerPage(runtime)
        self.broker_gateway_lab = BrokerGatewayLabPage(runtime)

        wire_journal_links(self.backtest.metrics, self._goto_journal_entry)
        wire_journal_links(self.validation.summary, self._goto_journal_entry)
        wire_journal_links(self.experiments._table, self._goto_journal_entry)
        wire_journal_links(self.test._metrics, self._goto_journal_entry)
        wire_journal_links(self.compare._table, self._goto_journal_entry)
        for page in (
            self.risk.last_factor,
            self.risk.last_risk,
            self.alpha.last,
            self.features.last,
            self.discovery_lab.last,
            self.portfolio.last,
        ):
            wire_journal_links(page, self._goto_journal_entry)

        self._pages: dict[str, QWidget] = {
            "home": self.home,
            "learn": self.learn,
            "test": self.test,
            "journal": self.journal,
            "settings": self.settings,
            "market": self.market,
            "data": self.data,
            "features": self.features,
            "research": self.research,
            "orchestration": self.orchestration,
            "discovery": self.discovery_lab,
            "knowledge": self.knowledge_lab,
            "capital": self.capital_lab,
            "paper": self.paper_oms_lab,
            "monitor": self.monitoring_lab,
            "tca": self.tca_lab,
            "econo": self.econometrics_lab,
            "certify": self.certification_lab,
            "shadow": self.shadow_lab,
            "safety": self.safety_lab,
            "promote": self.promotion_lab,
            "rt_data": self.realtime_data_lab,
            "rt_decision": self.realtime_decision_lab,
            "twin": self.digital_twin_lab,
            "ops": self.ops_lab,
            "alpha": self.alpha,
            "models": self.adaptive,
            "learning": self.learning,
            "ensemble": self.ensemble,
            "backtests": self.backtest,
            "validation": self.validation,
            "compare": self.compare,
            "portfolio": self.portfolio,
            "risk": self.risk,
            "execution": self.execution_lab,
            "broker": self.broker,
            "gateway": self.broker_gateway_lab,
            "ai": self.ai_research,
            "experiments": self.experiments,
            "system": self.system,
            "logs": self.logs,
        }
        self._wire_catalog_empty_actions()
        self._page_shells: dict[str, QScrollArea] = {}
        for key, widget in self._pages.items():
            shell = wrap_page_scroll(widget)
            self._page_shells[key] = shell
            self.stack.addWidget(shell)

        self._nav_keys: list[str] = []
        self._row_to_key: list[str | None] = []

        body = QHBoxLayout()
        body.setContentsMargins(0, 0, 0, 0)
        body.setSpacing(0)
        body.addWidget(self._nav_host)
        body.addWidget(self.stack, 1)

        central = QWidget()
        root = QVBoxLayout(central)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(0)
        root.addWidget(self._live_banner)
        root.addLayout(header)
        root.addWidget(self._context_host)
        root.addWidget(self._breadcrumb)
        root.addWidget(self._notification_strip)
        root.addLayout(body, 1)
        self.setCentralWidget(central)

        self.status_bar = FooterStatusBar()
        self.status_bar.chip_clicked.connect(self._select_nav)
        self.setStatusBar(self.status_bar)

        self.nav.currentRowChanged.connect(self._nav_changed)
        self.nav.itemClicked.connect(self._nav_item_clicked)
        self._rebuild_nav(select_key=prefs.nav)

        self._timer = QTimer(self)
        self._timer.setInterval(250)
        self._timer.timeout.connect(self._tick)
        self._timer.start()

        live_action = QAction("Request live trading…", self)
        live_action.triggered.connect(self._request_live)
        quit_action = QAction("Quit", self)
        quit_action.triggered.connect(self.close)
        menu = self.menuBar().addMenu("NAYAK QUANT LAB")
        menu.addAction(live_action)
        menu.addAction(quit_action)

        go_action = QAction("Go to page…", self)
        go_action.setShortcut(QKeySequence("Ctrl+K"))
        go_action.triggered.connect(self._open_command_palette)
        self.addAction(go_action)
        go_action_mac = QAction("Go to page… (macOS)", self)
        go_action_mac.setShortcut(QKeySequence("Meta+K"))
        go_action_mac.triggered.connect(self._open_command_palette)
        self.addAction(go_action_mac)

        filter_action = QAction("Filter sidebar…", self)
        filter_action.setShortcut(QKeySequence(NAV_FILTER_SHORTCUT))
        filter_action.triggered.connect(self._focus_nav_search)
        self.addAction(filter_action)

        nav_menu = menu.addMenu("Navigate")
        nav_menu.addAction(go_action)
        nav_menu.addAction(go_action_mac)
        nav_menu.addAction(filter_action)

        escape_clear = QShortcut(QKeySequence(Qt.Key.Key_Escape), self)
        escape_clear.activated.connect(self._clear_nav_search)

        self._last_status_sig: tuple | None = None
        self._register_nav_shortcuts()
        self._update_nav_search_visibility()
        self._apply_sidebar_collapsed(prefs.sidebar_collapsed)
        self._apply_live_chrome()
        self._apply_density_to_pages()
        self._refresh_context_strip()
        self._greeting_chip.setText(self._assistant.status_line())

    def _wire_catalog_empty_actions(self) -> None:
        for page in self._pages.values():
            if isinstance(page, CatalogLabPage) and page._on_empty_action is None:
                page.set_empty_action(self._goto_backtest_and_run)

    def _apply_density(self, _density: UiDensity | None = None) -> None:
        self._apply_density_to_pages()

    def _apply_density_to_pages(self) -> None:
        density = self.runtime.ui_settings.current.density
        for page in self._pages.values():
            if isinstance(page, LabPageShell):
                page.apply_density(density)

    def _ack_notifications(self) -> None:
        self._notification_ack = len(self.runtime.notifications)
        self._refresh_context_strip()

    def _poll_notifications(self) -> None:
        notifs = self.runtime.notifications
        if len(notifs) > self._notification_ack:
            self._notification_strip.show_message(notifs[-1])

    def _apply_theme(self, theme: UiTheme) -> None:
        from PySide6.QtWidgets import QApplication

        app = QApplication.instance()
        apply_theme(app if isinstance(app, QApplication) else None, theme)
        self.setStyleSheet(stylesheet_for(theme))

    def _refresh_assistant_surfaces(self) -> None:
        self._greeting_chip.setText(self._assistant.status_line())
        self._refresh_context_strip()
        self.home.refresh()

    def _nudge_fingerprint(self, nudge: ContextNudge) -> str:
        if nudge.nav_key:
            return f"nav:{nudge.nav_key}"
        return f"text:{nudge.text[:64]}"

    def _run_context_action(self) -> None:
        nudge = self._assistant.primary_context_nudge()
        if nudge is None:
            return
        if nudge.nav_key:
            self._select_nav(nudge.nav_key)
        self._ack_context_nudge(nudge)

    def _ack_context_nudge(self, nudge: ContextNudge) -> None:
        self._dismissed_nudges.add(self._nudge_fingerprint(nudge))
        if nudge.nav_key is None:
            self._notification_ack = len(self.runtime.notifications)
        self._refresh_context_strip()
        self.home.refresh()

    def _refresh_context_strip(self) -> None:
        nudge = self._assistant.primary_context_nudge()
        if nudge is None:
            self._context_host.setVisible(False)
            return
        if self._nudge_fingerprint(nudge) in self._dismissed_nudges:
            self._context_host.setVisible(False)
            return
        if (
            nudge.nav_key is None
            and self.runtime.notifications
            and nudge.text == self.runtime.notifications[-1]
            and len(self.runtime.notifications) <= self._notification_ack
        ):
            self._context_host.setVisible(False)
            return
        self._context_strip.setText(nudge.text)
        if nudge.nav_key and nudge.action_label:
            self._context_action.setText(f"{nudge.action_label} →")
            self._context_action.setVisible(True)
        else:
            self._context_action.setVisible(False)
        self._context_host.setVisible(True)

    def _persist_terminal_layouts(self) -> None:
        for page in (self.market, self.backtest, self.validation):
            save = getattr(page, "save_terminal_layout", None)
            if callable(save):
                save()

    def _set_experience_mode(self, mode: ExperienceMode) -> None:
        prefs = self.runtime.ui_settings.current
        if prefs.experience_mode is mode:
            return
        prefs.experience_mode = mode
        if mode is ExperienceMode.FULL:
            self._assistant.record_milestone("full_lab_unlocked")
            self._full_btn.setChecked(True)
            self._guided_btn.setChecked(False)
        else:
            self._guided_btn.setChecked(True)
            self._full_btn.setChecked(False)
        self.runtime.ui_settings.save()
        current = prefs.nav
        self._update_nav_search_visibility()
        self._apply_sidebar_collapsed(prefs.sidebar_collapsed)
        self._rebuild_nav(select_key=current if self._key_visible(current) else "home")
        self.home.refresh()

    def _update_nav_search_visibility(self) -> None:
        full = self.runtime.ui_settings.current.experience_mode is ExperienceMode.FULL
        self._nav_search.setVisible(full)
        if not full:
            self._nav_search.clear()

    def _open_command_palette(self) -> None:
        if self.runtime.ui_settings.current.experience_mode is ExperienceMode.GUIDED:
            self._set_experience_mode(ExperienceMode.FULL)
        commands = build_palette_commands(self.runtime)
        prefs = self.runtime.ui_settings.current
        palette = CommandPalette(
            commands,
            recents=prefs.palette_recents,
            on_nav=self._select_nav,
            on_action=self._run_palette_action,
            on_experiment=self._goto_journal_entry,
            on_command_run=self._record_palette_command,
            parent=self,
        )
        palette.exec()

    def _record_palette_command(self, command_id: str) -> None:
        prefs = self.runtime.ui_settings.current
        recents = [cid for cid in prefs.palette_recents if cid != command_id]
        recents.insert(0, command_id)
        prefs.palette_recents = recents[:8]
        self.runtime.ui_settings.save()

    def _handoff_compare(self) -> None:
        self._set_experience_mode(ExperienceMode.FULL)
        self._select_nav("compare")

    def _handoff_validation(self) -> None:
        self._set_experience_mode(ExperienceMode.FULL)
        self._select_nav("validation")

    def _handoff_market(self) -> None:
        self._set_experience_mode(ExperienceMode.FULL)
        self._select_nav("market")

    def _toggle_breadcrumb_section(self) -> None:
        key = self.runtime.ui_settings.current.nav
        section = nav_section_header_for_page(key)
        if section is None:
            return
        prefs = self.runtime.ui_settings.current
        prefs.collapsed_nav_sections = toggle_collapsed_section(
            prefs.collapsed_nav_sections,
            section,
        )
        self.runtime.ui_settings.save()
        self._rebuild_nav(select_key=key, fire_nav=False)

    def _update_breadcrumb(self, key: str) -> None:
        section, page = breadcrumb_parts(key)
        self._breadcrumb.set_parts(section, page)

    def _run_palette_action(self, action_id: str) -> None:
        if action_id == "run_backtest":
            self._goto_backtest_and_run()
        elif action_id == "run_validation":
            self._select_nav("validation")
            self.validation._start()
        elif action_id == "open_journal":
            self._select_nav("journal")
        elif action_id == "toggle_theme":
            prefs = self.runtime.ui_settings.current
            theme = UiTheme.LIGHT if prefs.theme is UiTheme.DARK else UiTheme.DARK
            self._apply_theme(theme)
            prefs.theme = theme
            self.runtime.ui_settings.save()
        elif action_id == "full_lab":
            self._set_experience_mode(ExperienceMode.FULL)
        elif action_id == "guided_lab":
            self._set_experience_mode(ExperienceMode.GUIDED)

    def _register_nav_shortcuts(self) -> None:
        for key, sequence in NAV_SHORTCUTS.items():
            action = QAction(self)
            action.setShortcut(QKeySequence(sequence))
            action.triggered.connect(lambda checked=False, nav_key=key: self._select_nav(nav_key))
            self.addAction(action)

    def _toggle_sidebar_collapsed(self) -> None:
        prefs = self.runtime.ui_settings.current
        self._apply_sidebar_collapsed(not prefs.sidebar_collapsed)
        prefs.sidebar_collapsed = not prefs.sidebar_collapsed
        self.runtime.ui_settings.save()

    def _apply_sidebar_collapsed(self, collapsed: bool) -> None:
        prefs = self.runtime.ui_settings.current
        if collapsed:
            self._nav_host.setFixedWidth(56)
            self.nav.setFixedWidth(48)
            self._nav_search.setVisible(False)
            self._nav_toggle.setText("»")
            self._nav_toggle.setToolTip("Expand sidebar")
        else:
            self._nav_host.setFixedWidth(212)
            self.nav.setFixedWidth(196)
            full = prefs.experience_mode is ExperienceMode.FULL
            self._nav_search.setVisible(full)
            self._nav_toggle.setText("«")
            self._nav_toggle.setToolTip("Collapse sidebar")
        self._rebuild_nav(select_key=prefs.nav, fire_nav=False)

    def _apply_live_chrome(self) -> None:
        live = self.runtime.mode is AppMode.LIVE
        self._live_banner.setVisible(live)
        self._mode_badge.setText(f"Mode: {self.runtime.mode.value.upper()}")
        self._mode_badge.setObjectName("modeBadgeLive" if live else "modeBadge")
        self._mode_badge.setStyleSheet("")
        self._mode_badge.style().unpolish(self._mode_badge)
        self._mode_badge.style().polish(self._mode_badge)
        if live:
            self._nav_host.setObjectName("navHostLive")
        else:
            self._nav_host.setObjectName("navHost")
        self._nav_host.setStyleSheet("")
        self._nav_host.style().unpolish(self._nav_host)
        self._nav_host.style().polish(self._nav_host)

    def _apply_nav_live_tint(self) -> None:
        """Backward-compatible alias for tests and callers."""
        self._apply_live_chrome()

    def _logs_has_error(self) -> bool:
        for row in self.runtime.logs.snapshot()[-50:]:
            level = str(row.get("level", row.get("log_level", ""))).lower()
            if "error" in level or "critical" in level:
                return True
        return False

    def _focus_nav_search(self) -> None:
        if self.runtime.ui_settings.current.experience_mode is ExperienceMode.GUIDED:
            self._set_experience_mode(ExperienceMode.FULL)
        self._nav_search.setFocus()
        self._nav_search.selectAll()

    def _clear_nav_search(self) -> None:
        if self._nav_search.hasFocus() and self._nav_search.text():
            self._nav_search.clear()
            return
        if self._nav_search.text():
            self._nav_search.clear()

    def _activate_first_nav_match(self) -> None:
        for row, key in enumerate(self._row_to_key):
            if key is not None:
                self.nav.setCurrentRow(row)
                return

    def _apply_nav_search(self, _query: str) -> None:
        if not self._base_nav_items:
            return
        visible = self._visible_nav_items()
        current = self.runtime.ui_settings.current.nav
        query = self._nav_search.text().strip()
        if query:
            select = next((item.key for item in visible if not item.header), None)
        elif any(not item.header and item.key == current for item in visible):
            select = current
        else:
            select = "home"
        self._paint_nav_list(visible, select_key=select, fire_nav=False)

    def _visible_nav_items(self) -> list[NavItem]:
        collapsed = frozenset(self.runtime.ui_settings.current.collapsed_nav_sections)
        folded = filter_collapsed_sections(self._base_nav_items, collapsed)
        query = self._nav_search.text() if self._nav_search.isVisible() else ""
        return filter_nav_items(folded, query)

    def _nav_item_clicked(self, item: QListWidgetItem) -> None:
        key = item.data(Qt.ItemDataRole.UserRole)
        if not key or key not in _COLLAPSIBLE_SECTIONS:
            return
        prefs = self.runtime.ui_settings.current
        prefs.collapsed_nav_sections = toggle_collapsed_section(
            prefs.collapsed_nav_sections,
            str(key),
        )
        self.runtime.ui_settings.save()
        self._rebuild_nav(select_key=prefs.nav, fire_nav=False)

    def _paint_nav_list(
        self,
        items: list[NavItem],
        *,
        select_key: str | None,
        fire_nav: bool,
    ) -> None:
        self.nav.blockSignals(True)
        self.nav.clear()
        self._nav_keys = []
        self._row_to_key = []
        row_for_key: dict[str, int] = {}
        collapsed = self.runtime.ui_settings.current.sidebar_collapsed
        status = self.runtime.status
        logs_err = self._logs_has_error()

        for item in items:
            if item.header:
                header = QListWidgetItem(
                    NAV_SECTION_RAIL.get(item.key, "—") if collapsed else item.label
                )
                header.setFlags(Qt.ItemFlag.NoItemFlags)
                header.setForeground(Qt.GlobalColor.gray)
                header.setData(Qt.ItemDataRole.UserRole, item.key)
                if collapsed:
                    header.setToolTip(item.label.strip("— ▾▸").strip())
                self.nav.addItem(header)
                self._row_to_key.append(None)
                continue
            prefix = nav_status_prefix(
                item.key,
                broker=status.broker,
                system=status.system,
                logs_has_error=logs_err,
            )
            if collapsed:
                label = NAV_RAIL_ICONS.get(item.key, item.label[:1])
            else:
                hint = shortcut_label(item.key)
                label = f"{prefix}{item.label}"
                if hint:
                    label = f"{label}   {hint}"
            self._nav_keys.append(item.key)
            row_for_key[item.key] = self.nav.count()
            self._row_to_key.append(item.key)
            row = QListWidgetItem(label)
            if collapsed:
                section = nav_section_label_for_page(item.key)
                hint = shortcut_label(item.key)
                tip_parts = [item.label.strip()]
                if section:
                    tip_parts.append(section)
                if hint:
                    tip_parts.append(hint)
                row.setToolTip(" · ".join(tip_parts))
            else:
                row.setToolTip(nav_tooltip(item.key, item.label))
            self.nav.addItem(row)

        key = select_key if select_key and select_key in row_for_key else None
        if key is None and "home" in row_for_key:
            key = "home"
        if key and key in row_for_key:
            self.nav.setCurrentRow(row_for_key[key])
        self.nav.blockSignals(False)
        if fire_nav and key and key in row_for_key:
            self._nav_changed(row_for_key[key])

    def _key_visible(self, key: str) -> bool:
        return key in self._nav_keys

    def _rebuild_nav(self, select_key: str | None = None, *, fire_nav: bool = True) -> None:
        prefs = self.runtime.ui_settings.current
        self._base_nav_items = nav_for_mode(prefs.experience_mode)
        visible = self._visible_nav_items()
        key = select_key if select_key else prefs.nav
        self._paint_nav_list(visible, select_key=key, fire_nav=fire_nav)
        self._update_breadcrumb(key or prefs.nav)
        self._paint_status()

    def _nav_changed(self, row: int) -> None:
        if row < 0 or row >= len(self._row_to_key):
            return
        key = self._row_to_key[row]
        if key is None:
            return
        shell = self._page_shells.get(key)
        if shell is None:
            return
        self.stack.setCurrentWidget(shell)
        self.runtime.ui_settings.current.nav = key
        self._update_breadcrumb(key)
        self._assistant.record_visit(key)
        nudge = self._assistant.primary_context_nudge()
        if nudge is not None and nudge.nav_key == key:
            self._ack_context_nudge(nudge)
        self._refresh_page(key)
        self._refresh_context_strip()
        self._paint_status()

    def _refresh_page(self, key: str) -> None:
        page = self._pages.get(key)
        if page is None:
            return
        if hasattr(page, "refresh"):
            page.refresh()

    def _handle_focus_action(self, action: FocusAction) -> None:
        if action is FocusAction.ONBOARDING:
            self._select_nav("learn")
        elif action is FocusAction.FIRST_BACKTEST:
            self._goto_test_wizard()
        elif action is FocusAction.LEARN_SHARPE:
            self._assistant.record_milestone("first_equity_view")
            self._select_nav("learn")
        elif action is FocusAction.VALIDATION:
            self._handoff_validation()
        elif action is FocusAction.FEATURES:
            self._set_experience_mode(ExperienceMode.FULL)
            self._select_nav("features")
        elif action is FocusAction.FULL_LAB:
            self._set_experience_mode(ExperienceMode.FULL)
        elif action is FocusAction.EXPLORE:
            self._handoff_market()
        elif action is FocusAction.JOURNAL:
            self._select_nav("journal")
        elif action is FocusAction.COMPARE:
            self._handoff_compare()
        elif action is FocusAction.MARKET:
            self._handoff_market()
        self.home.refresh()

    def _select_nav(self, key: str) -> None:
        if key not in self._nav_keys and (
            self.runtime.ui_settings.current.experience_mode is ExperienceMode.GUIDED
        ):
            self._set_experience_mode(ExperienceMode.FULL)
        for row, mapped in enumerate(self._row_to_key):
            if mapped == key:
                self.nav.setCurrentRow(row)
                return

    def _goto_test_wizard(self) -> None:
        self._select_nav("test")
        self.test.reset_wizard()

    def _goto_journal_entry(self, experiment_id: str) -> None:
        self._select_nav("journal")
        self.journal.select_experiment(experiment_id)

    def _goto_backtest_and_run(self) -> None:
        if (
            self.runtime.ui_settings.current.experience_mode is ExperienceMode.GUIDED
            and "test" in self._nav_keys
        ):
            self._select_nav("test")
            self.test.open_at_run_step()
            return
        if "backtests" in self._nav_keys:
            self._select_nav("backtests")
        self.backtest._start()

    def _after_validation(self) -> None:
        self._assistant.record_milestone("first_validation")
        self._after_backtest()

    def _after_backtest(self) -> None:
        self._assistant.record_milestone("first_backtest")
        self._assistant.record_milestone("first_equity_view")
        refresh_keys = (
            "home",
            "learn",
            "test",
            "journal",
            "experiments",
            "data",
            "validation",
            "compare",
            "alpha",
            "portfolio",
            "risk",
            "market",
            "models",
            "learning",
            "ensemble",
            "execution",
            "orchestration",
            "discovery",
            "knowledge",
            "capital",
            "paper",
            "monitor",
            "tca",
            "econo",
            "certify",
            "shadow",
            "safety",
            "promote",
            "ops",
            "gateway",
            "logs",
        )
        for key in refresh_keys:
            if key in self._pages:
                self._refresh_page(key)
        self._greeting_chip.setText(self._assistant.status_line())
        self._refresh_context_strip()
        self._paint_status()

    def _tick(self) -> None:
        self.backtest.poll()
        self.validation.poll()
        self.test.poll()
        self._poll_notifications()
        if self.runtime.ui_settings.current.nav == "home":
            self.home.refresh_pulse()
        sig = self._status_signature()
        if sig != self._last_status_sig:
            self._last_status_sig = sig
            self._paint_status()

    def _status_signature(self) -> tuple:
        status = self.runtime.status
        prefs = self.runtime.ui_settings.current
        return (
            self.runtime.mode,
            prefs.experience_mode,
            status.live_trading,
            status.broker,
            status.system,
            self._logs_has_error(),
        )

    def _paint_status(self) -> None:
        mode = self.runtime.ui_settings.current.experience_mode.value.upper()
        self.status_bar.update_from_runtime(self.runtime, mode_label=f"{mode} LAB")
        self._last_status_sig = self._status_signature()

    def _request_live(self) -> None:
        dialog = LiveConfirmDialog(self.runtime, parent=self)
        if dialog.exec() != dialog.DialogCode.Accepted:
            return
        try:
            self.runtime.try_enable_live()
            self._apply_live_chrome()
        except SafetyError as exc:
            QMessageBox.critical(self, "Live trading blocked", str(exc))

    def showEvent(self, event: QShowEvent) -> None:
        super().showEvent(event)
        clamp_to_screen(self)

    def closeEvent(self, event: QCloseEvent) -> None:
        if self.runtime.mode is AppMode.LIVE:
            QMessageBox.information(
                self,
                "Shutdown",
                "Closing the UI does not flatten the portfolio. "
                "Positions and broker orders may remain — live path is not active in this build.",
            )
        prefs = self.runtime.ui_settings.current
        prefs.width = self.width()
        prefs.height = self.height()
        prefs.x = self.x()
        prefs.y = self.y()
        self._persist_terminal_layouts()
        self.runtime.ui_settings.save(prefs)
        self._timer.stop()
        self.runtime.shutdown()
        event.accept()
