"""Optional local visual surface. No tools or execution objects are exposed."""

from __future__ import annotations

import json
import os
from pathlib import Path

from PySide6.QtCore import Property, QObject, QUrl, Signal, Slot
from PySide6.QtWidgets import QLabel, QVBoxLayout, QWidget

from quantlab.agents.presentation import (
    AdjudicationVisualDTO,
    AgentVisualStateDTO,
    DebateVisualDTO,
    EvidenceNodeSummaryDTO,
    SystemSafetyDTO,
)


class AgentDeskBridge(QObject):
    presentationChanged = Signal(str)
    navigationRequested = Signal(str, str)

    def __init__(self, parent: QObject | None = None) -> None:
        super().__init__(parent)
        self._evidence: frozenset[str] = frozenset()
        self._transcript: str | None = None
        self._decision: str | None = None
        self._payload = json.dumps(
            {"agents": [], "evidence": [], "safety": SystemSafetyDTO().model_dump(mode="json")}
        )

    @Property(str, notify=presentationChanged)
    def presentation(self) -> str:
        return self._payload

    def publish(
        self,
        states: tuple[AgentVisualStateDTO, ...],
        evidence: tuple[EvidenceNodeSummaryDTO, ...],
        debate: DebateVisualDTO | None = None,
        adjudication: AdjudicationVisualDTO | None = None,
    ) -> None:
        self._evidence = frozenset(row.artifact_hash for row in evidence)
        self._transcript = debate.transcript_hash if debate else None
        self._decision = adjudication.decision_hash if adjudication else None
        self._payload = json.dumps(
            {
                "agents": [row.model_dump(mode="json") for row in states],
                "evidence": [row.model_dump(mode="json") for row in evidence],
                "debate": debate.model_dump(mode="json") if debate else None,
                "adjudication": adjudication.model_dump(mode="json") if adjudication else None,
                "safety": SystemSafetyDTO().model_dump(mode="json"),
            }
        )
        self.presentationChanged.emit(self._payload)

    @Slot(str, str)
    def navigate(self, intent: str, identity: str) -> None:
        allowed = (
            (intent == "select_agent" and identity in {"BULL", "BEAR"})
            or (intent == "open_evidence" and identity in self._evidence)
            or (intent == "open_debate" and identity == self._transcript and bool(identity))
            or (intent == "open_adjudication" and identity == self._decision and bool(identity))
        )
        if allowed:
            self.navigationRequested.emit(intent, identity)


class AgentDeskWebView(QWidget):
    """WebEngine is lazy/opt-in; headless and native controls work without Chromium."""

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.bridge = AgentDeskBridge(self)
        self._web: QWidget | None = None
        self._channel: QObject | None = None
        self._profile: QObject | None = None
        self._interceptor: QObject | None = None
        layout = QVBoxLayout(self)
        self.fallback = QLabel("Native analyst view · visual layer optional")
        self.fallback.setAccessibleName("Agent visual fallback")
        self.fallback.setWordWrap(True)
        layout.addWidget(self.fallback)
        asset = Path(__file__).parents[1] / "web" / "agent_desk" / "dist" / "index.html"
        if (
            os.environ.get("QUANT_LAB_AGENT_VISUALS") != "1"
            or not asset.is_file()
            or os.environ.get("QT_QPA_PLATFORM") == "offscreen"
        ):
            return
        try:
            from PySide6.QtWebChannel import QWebChannel
            from PySide6.QtWebEngineCore import (
                QWebEnginePage,
                QWebEngineProfile,
                QWebEngineSettings,
                QWebEngineUrlRequestInfo,
                QWebEngineUrlRequestInterceptor,
            )
            from PySide6.QtWebEngineWidgets import QWebEngineView

            asset_root = asset.parent.resolve()

            class LocalRequests(QWebEngineUrlRequestInterceptor):
                def interceptRequest(self, info: QWebEngineUrlRequestInfo) -> None:
                    url = info.requestUrl()
                    allowed = (
                        url.scheme() == "qrc" and url.path() == "/qtwebchannel/qwebchannel.js"
                    ) or (
                        url.isLocalFile()
                        and Path(url.toLocalFile()).resolve().is_relative_to(asset_root)
                    )
                    info.block(not allowed)

            class LocalPage(QWebEnginePage):
                def acceptNavigationRequest(
                    self,
                    url: QUrl | str,
                    navigation_type: QWebEnginePage.NavigationType,
                    is_main_frame: bool,
                ) -> bool:
                    local_url = QUrl(url)
                    return local_url.isLocalFile() and Path(
                        local_url.toLocalFile()
                    ).resolve().is_relative_to(asset_root)

            web = QWebEngineView(self)
            web.setMinimumHeight(380)
            # The view/page must be deleted before its profile, not as its sibling
            # under the view. QObject destroys children in their creation order.
            profile = QWebEngineProfile(self)
            profile.setHttpCacheType(QWebEngineProfile.HttpCacheType.MemoryHttpCache)
            interceptor = LocalRequests(profile)
            profile.setUrlRequestInterceptor(interceptor)
            page = LocalPage(profile, web)
            web.setPage(page)
            page.settings().setAttribute(
                QWebEngineSettings.WebAttribute.LocalContentCanAccessRemoteUrls,
                False,
            )
            channel = QWebChannel(page)
            channel.registerObject("agentDesk", self.bridge)
            page.setWebChannel(channel)

            def loaded(ready: bool) -> None:
                self.fallback.setVisible(not ready)
                web.setVisible(ready)
                if not ready:
                    self.fallback.setText(
                        "Visual layer unavailable · native inspectors remain active"
                    )

            def crashed(*_: object) -> None:
                loaded(False)

            web.loadFinished.connect(loaded)
            page.renderProcessTerminated.connect(crashed)
            web.setUrl(QUrl.fromLocalFile(str(asset)))
            self._web, self._channel = web, channel
            self._profile, self._interceptor = profile, interceptor
            layout.addWidget(web)
        except ImportError:
            self.fallback.setText("WebEngine unavailable · native analyst view available")
