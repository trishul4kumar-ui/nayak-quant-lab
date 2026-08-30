# QUANT LAB — CURSOR PROMPT 03
## Desktop Application / Local Software Execution Directive
### Version 0.3 — Companion to Prompt 01 + Prompt 02
### Date: 2026-08-30

---

## 0. PURPOSE

You are continuing development of QUANT LAB.

Prompt 01 established the repository reverse-engineering program.

Prompt 02 established the quantitative architecture, including:

- MarketState
- Mathematical Core
- Research Hypothesis Engine
- Signal Genome
- Alpha Factory
- Model Factory
- Research Integrity Engine
- Experiment Ledger
- Portfolio Engine
- Risk Firewall
- Execution Engine
- Broker abstraction
- AI research layer
- provenance/auditability
- backtest → paper → shadow → live lifecycle

This prompt adds one critical requirement:

> **QUANT LAB MUST RUN AS A REAL DESKTOP APPLICATION ON THE USER'S COMPUTER.**

Do not treat QUANT LAB as merely:

- a Python repository;
- a collection of scripts;
- a Jupyter notebook;
- a terminal-only application;
- a web page that requires a cloud server;
- a development-only dashboard.

The final product must behave like a serious engineering/scientific desktop application.

---

# 1. PRIMARY PRODUCT REQUIREMENT

The user should be able to start QUANT LAB on their computer and see a professional application window.

Target experience:

```text
Computer
   ↓
Launch QUANT LAB
   ↓
Application starts
   ↓
QUANT LAB splash/startup
   ↓
System health checks
   ↓
Local services initialize
   ↓
Main QUANT LAB interface
```

The application should be usable without opening:

- VS Code;
- Cursor;
- a Python terminal;
- Jupyter;
- a browser manually;
- Docker manually.

During development, developer tooling is acceptable.

For the eventual product, the user experience should be:

```text
Double-click QUANT LAB
        ↓
Application launches
        ↓
Use the software
```

---

# 2. ARCHITECTURAL PRINCIPLE

Do NOT rewrite the quantitative architecture simply to create a desktop GUI.

Instead:

```text
                 QUANT LAB DESKTOP
                        │
              ┌─────────┴─────────┐
              │                   │
          UI SHELL          APPLICATION SERVICES
              │                   │
              └─────────┬─────────┘
                        │
                  QUANT LAB CORE
                        │
       ┌────────────────┼────────────────┐
       ▼                ▼                ▼
   DATA FABRIC      QUANT CORE        AI CORE
       │                │                │
       └────────────────┼────────────────┘
                        ▼
                 RESEARCH ENGINE
                        │
                        ▼
                  PORTFOLIO/RISK
                        │
                        ▼
                  EXECUTION ENGINE
                        │
                        ▼
                  BROKER GATEWAY
```

The UI is a client of the domain/application layer.

The UI must NOT contain core quantitative logic.

---

# 3. DESKTOP APPLICATION STACK

Evaluate the existing repository and choose the most appropriate desktop technology.

Preferred options:

### Option A — PySide6 / Qt

Strong default if the core remains Python.

Advantages:

- native desktop application model;
- excellent widgets;
- docking panels;
- menus;
- tables;
- charts;
- threading/process integration;
- mature Windows/macOS/Linux support.

### Option B — PyQt

Acceptable if already deeply integrated.

### Option C — Tauri/Electron

Consider only if there is a strong architectural reason for a web-based frontend.

Do NOT introduce a heavy frontend stack merely because it looks modern.

The quantitative engine must remain independent of the UI technology.

Document the decision in an ADR.

---

# 4. OPERATING SYSTEM SUPPORT

The architecture must be portable.

Primary development target:

```text
Windows
```

Also maintain a path toward:

```text
macOS
Linux
```

Do not hardcode:

```text
C:\...
```

or:

```text
/Users/...
```

throughout the application.

Use platform-aware paths.

---

# 5. APPLICATION DIRECTORY STRUCTURE

Establish a clean application/runtime architecture.

Conceptual structure:

```text
quant_lab/
│
├── app/
│   ├── bootstrap/
│   ├── lifecycle/
│   ├── runtime/
│   ├── services/
│   ├── configuration/
│   └── health/
│
├── ui/
│   ├── main_window/
│   ├── navigation/
│   ├── dashboards/
│   ├── research/
│   ├── market/
│   ├── portfolio/
│   ├── risk/
│   ├── execution/
│   ├── broker/
│   ├── ai/
│   └── system/
│
├── domain/
├── data/
├── quant/
├── research/
├── models/
├── portfolio/
├── risk/
├── execution/
├── brokers/
├── ai/
├── storage/
├── infrastructure/
└── tests/
```

Adapt this to the existing repository.

Do NOT blindly create duplicate packages if equivalent architecture already exists.

---

# 6. APPLICATION ENTRY POINT

Create a single canonical application entry point.

Conceptually:

```text
quant_lab
    ↓
main()
    ↓
bootstrap()
    ↓
load configuration
    ↓
initialize logging
    ↓
initialize database
    ↓
initialize application services
    ↓
run health checks
    ↓
start UI
```

The user should not need to know internal Python modules.

---

# 7. DEVELOPMENT VS PRODUCTION MODE

Support explicit modes.

```text
DEVELOPMENT
RESEARCH
PAPER
SHADOW
LIVE
```

Example:

```text
QUANT_LAB_MODE=research
```

The mode must visibly appear somewhere in the application.

Especially:

```text
LIVE
```

must be visually unmistakable.

---

# 8. LIVE TRADING SAFETY

Default:

```text
LIVE_TRADING = FALSE
```

The application must start in:

```text
RESEARCH
```

or:

```text
PAPER
```

mode.

Live trading must require explicit activation.

Do NOT make live mode the default.

---

# 9. APPLICATION STARTUP HEALTH CHECK

When QUANT LAB launches, perform health checks.

Example:

```text
QUANT LAB STARTUP
────────────────────────────

Core Engine             ✓
Database                ✓
Data Store              ✓
Configuration           ✓
Research Engine         ✓
Backtest Engine         ✓
Risk Engine             ✓
Execution Engine        ✓
Broker Gateway          ○
AI Services             ○

Mode: RESEARCH
Live Trading: DISABLED
```

Do not prevent research operation because a broker is unavailable.

Only components required for the selected operating mode should be mandatory.

---

# 10. MAIN WINDOW

Design a professional scientific/engineering desktop interface.

Suggested layout:

```text
┌───────────────────────────────────────────────────────────────┐
│ QUANT LAB                         Mode: RESEARCH     ● SYSTEM │
├─────────────┬─────────────────────────────────────────────────┤
│             │                                                 │
│ Dashboard   │                                                 │
│             │                                                 │
│ Market      │                 MAIN WORKSPACE                  │
│             │                                                 │
│ Research    │                                                 │
│             │                                                 │
│ Alpha Lab   │                                                 │
│             │                                                 │
│ Models      │                                                 │
│             │                                                 │
│ Backtests   │                                                 │
│             │                                                 │
│ Portfolio   │                                                 │
│             │                                                 │
│ Risk        │                                                 │
│             │                                                 │
│ Execution   │                                                 │
│             │                                                 │
│ Broker      │                                                 │
│             │                                                 │
│ AI Research │                                                 │
│             │                                                 │
│ Experiments │                                                 │
│             │                                                 │
│ System      │                                                 │
│             │                                                 │
├─────────────┴─────────────────────────────────────────────────┤
│ Status | Data | Engine | Research | Risk | Execution | Logs  │
└───────────────────────────────────────────────────────────────┘
```

Do not over-design the UI initially.

Functionality first.

---

# 11. MAIN MODULES

The desktop application should eventually expose:

## Dashboard

Show:

```text
Market status
Portfolio status
Research activity
Active strategies
Risk state
System health
Recent experiments
Recent signals
Execution status
```

---

## Market

Provide:

```text
Instrument search
Price charts
Volume
Volatility
MarketState
Market regime
Market breadth
Watchlists
```

---

## Research Lab

Provide:

```text
Hypotheses
Experiments
Features
Factors
Signals
Alpha candidates
Research status
```

---

## Alpha Lab

Provide:

```text
Signal Genome
Alpha candidates
Signal performance
Robustness
Correlation
Research lineage
```

---

## Model Lab

Provide:

```text
Models
Model versions
Training runs
Validation
Metrics
Feature importance
Model lifecycle
```

---

## Backtest Lab

Provide:

```text
Strategy selection
Universe
Date range
Costs
Slippage
Execution assumptions
Run
Progress
Results
Equity curve
Drawdown
Metrics
Trade list
```

---

## Portfolio Lab

Provide:

```text
positions
weights
exposure
risk
factor exposure
allocation
P&L
```

---

## Risk Console

Provide:

```text
Risk state
Exposure
Limits
Drawdown
Daily P&L
Open risk
Rejected orders
Risk decisions
```

Risk settings must not be casually editable from an AI panel.

---

## Execution Console

Provide:

```text
Orders
Fills
Pending orders
Rejected orders
Execution latency
Slippage
Broker state
```

---

## Broker Console

Provide:

```text
Connection
Account
Cash
Margin
Positions
Orders
Reconciliation
```

Credentials must never be displayed.

---

## AI Research Console

Provide:

```text
Agents
Research requests
Hypotheses
Experiments
Critiques
Research reports
Agent activity
```

AI should remain subordinate to deterministic risk/execution controls.

---

# 12. WINDOW / PANEL SYSTEM

Use a flexible workspace.

Prefer:

```text
dockable panels
tabs
resizable panes
saved layouts
```

A quant researcher should eventually be able to arrange:

```text
Market chart
+
MarketState
+
Alpha
+
Backtest
+
Risk
```

simultaneously.

---

# 13. APPLICATION STATE

Separate UI state from domain state.

Do NOT allow widgets to become the source of truth.

Correct:

```text
Domain State
    ↓
Application Service
    ↓
View Model / Presenter
    ↓
UI
```

Not:

```text
UI widget
    ↓
random global variable
    ↓
trading engine
```

---

# 14. LONG-RUNNING TASKS

Backtests, model training, data ingestion and AI research can take seconds/minutes/hours.

The UI must not freeze.

Use:

```text
worker threads
processes
job queue
async tasks
```

as appropriate.

Provide:

```text
progress
status
cancel
logs
error reporting
```

---

# 15. JOB SYSTEM

Create a generic research/job abstraction.

Conceptually:

```text
Job
├── job_id
├── type
├── status
├── created_at
├── started_at
├── completed_at
├── progress
├── parameters
├── result
└── error
```

Statuses:

```text
QUEUED
RUNNING
PAUSED
CANCELLING
COMPLETED
FAILED
CANCELLED
```

This will support:

```text
backtest
training
data ingestion
feature calculation
alpha scan
optimization
AI research
```

---

# 16. LOCAL DATABASE

The desktop application should have a local persistent state.

Use the architecture already established.

Potential stack:

```text
PostgreSQL
```

for the authoritative relational system where required.

For local analytical workloads consider:

```text
DuckDB
Parquet
```

Do not force every dataset into PostgreSQL.

The architecture should distinguish:

```text
Transactional state
Analytical data
Research artifacts
Logs
```

---

# 17. DATA STORAGE

Recommended conceptual split:

```text
database/
    metadata
    instruments
    experiments
    models
    strategies
    orders
    positions
    risk decisions

data/
    raw/
    normalized/
    curated/
    features/

artifacts/
    models/
    backtests/
    reports/

logs/
```

Use platform-safe application data directories.

---

# 18. APPLICATION CONFIGURATION

Create a central configuration system.

Example conceptual structure:

```yaml
application:
  mode: research

database:
  ...

data:
  ...

research:
  ...

ai:
  ...

risk:
  ...

execution:
  ...

broker:
  ...

logging:
  ...
```

Never scatter configuration across source files.

---

# 19. USER SETTINGS

Persist application preferences:

```text
window size
window position
workspace layout
theme
chart preferences
default universe
default timeframe
research defaults
```

Do not store secrets as ordinary UI preferences.

---

# 20. SECRET MANAGEMENT

Broker/API credentials must be stored securely.

Never store credentials in:

```text
source code
git
plain configuration files
logs
experiment artifacts
screenshots
```

Use the operating system's secure credential mechanism where practical.

---

# 21. LOG VIEWER

The application should have a built-in log viewer.

Support:

```text
INFO
WARNING
ERROR
CRITICAL
DEBUG
```

Filters:

```text
component
severity
time
correlation_id
strategy
experiment
order
```

---

# 22. CRASH RECOVERY

The application must survive normal component failures.

Examples:

```text
data provider failure
AI provider failure
broker disconnect
database reconnect
worker crash
```

The desktop shell should remain usable where possible.

For live trading:

```text
execution uncertainty
        ↓
fail closed
        ↓
stop new risk
        ↓
reconcile
```

---

# 23. BROKER DISCONNECT UI

When the broker disconnects:

```text
BROKER: DISCONNECTED
LIVE ORDERING: BLOCKED
RECONCILIATION: REQUIRED
```

Do not simply show a small error in a log.

Critical state must be visible.

---

# 24. LIVE TRADING VISUAL SAFETY

When live trading is enabled, show:

```text
LIVE
```

prominently.

Before enabling:

```text
WARNING

You are enabling live trading.

Orders may result in real financial losses.

Current broker:
...
Current account:
...
Current risk configuration:
...
```

Require explicit confirmation.

The UI confirmation is an additional safety layer, not a replacement for the Risk Firewall.

---

# 25. PAPER TRADING

Paper mode should behave as close as practical to live mode.

Pipeline:

```text
Strategy
 ↓
Portfolio
 ↓
Risk
 ↓
Execution
 ↓
Paper Broker
```

Do not create a completely separate simplified strategy engine for paper trading.

---

# 26. SHADOW MODE

Support future:

```text
LIVE MARKET DATA
+
REAL STRATEGY
+
REAL SIGNALS
+
NO REAL ORDERS
```

Compare:

```text
what would have happened
vs
what actually happened
```

---

# 27. DESKTOP PACKAGING

The application must eventually be distributable.

Evaluate:

```text
PyInstaller
Nuitka
Briefcase
or another appropriate packaging solution
```

Choose based on:

```text
startup
dependency handling
native libraries
Python compatibility
debuggability
update strategy
```

Document the decision.

The final user should receive something resembling:

```text
QUANT LAB
    ├── installer
    └── application
```

rather than needing to manually install dozens of Python packages.

---

# 28. APPLICATION DATA LOCATION

Do not store user-generated data beside source code in production.

Use an OS-appropriate application-data directory.

Conceptually:

```text
QUANT LAB
├── Application
├── User Data
├── Research Data
├── Logs
└── Secure Credentials
```

---

# 29. BACKUP

Research is valuable.

Eventually provide:

```text
Export Research Archive
Backup Experiments
Backup Strategies
Backup Configuration
Restore
```

Do not automatically backup secrets into ordinary archives.

---

# 30. UPDATE ARCHITECTURE

Do not implement an automatic updater immediately.

But design so that future updates can distinguish:

```text
application version
database schema version
research artifact version
model version
strategy version
```

Never silently invalidate old research.

---

# 31. VERSION DISPLAY

The application should show:

```text
QUANT LAB
Version 0.x
Build <identifier>
Mode: RESEARCH
```

Research artifacts should record the software version.

---

# 32. OFFLINE OPERATION

QUANT LAB should remain useful without internet connectivity for:

```text
existing historical data
existing experiments
existing models
local backtests
local analysis
```

Internet should only be required for capabilities that actually require it.

---

# 33. DATA PROVIDER STATUS

The UI should show provider health:

```text
Provider       Status       Last Update
----------------------------------------
Historical     READY
Market Data    CONNECTED
Fundamental    READY
News           OFFLINE
Broker         DISCONNECTED
```

Avoid making a single provider failure appear to be a total system failure.

---

# 34. RESEARCH WORKSPACE

A researcher should be able to open QUANT LAB and go directly into:

```text
Research
   ↓
Hypothesis
   ↓
Experiment
   ↓
Backtest
   ↓
Results
```

The application should eventually support saving a complete research workspace.

---

# 35. RESULT EXPLORER

After a backtest, show:

```text
Summary
Performance
Risk
Drawdown
Trades
Exposure
Costs
Regimes
Robustness
Research Integrity
Experiment Metadata
```

Every result should link back to its experiment.

---

# 36. RESEARCH LINEAGE UI

Eventually allow:

```text
Hypothesis
   ↓
Feature
   ↓
Signal
   ↓
Model
   ↓
Strategy
   ↓
Experiment
   ↓
Backtest
   ↓
Result
```

Clicking any object should show its provenance.

---

# 37. NO UI-DRIVEN BUSINESS LOGIC

Strict rule:

```text
UI
≠
Business Logic
```

For example, this is prohibited:

```python
if button_clicked:
    broker.place_order(...)
```

Instead:

```text
UI
 ↓
Application Command
 ↓
Risk Engine
 ↓
Execution Engine
 ↓
Broker Gateway
```

---

# 38. COMMAND ARCHITECTURE

Consider commands such as:

```text
RunBacktest
CreateHypothesis
RunExperiment
PromoteStrategy
CreateOrderProposal
RequestRiskDecision
SubmitOrder
CancelOrder
ReconcileBroker
```

This makes the desktop application a clean client of the application layer.

---

# 39. NOTIFICATION SYSTEM

Support application notifications for important events:

```text
Backtest completed
Experiment failed
Data ingestion completed
Broker disconnected
Risk limit breached
Order rejected
Reconciliation mismatch
Strategy degraded
System error
```

Avoid excessive notifications.

---

# 40. SYSTEM STATUS

Provide a persistent status indicator:

```text
SYSTEM: HEALTHY
DATA: READY
RESEARCH: READY
RISK: ARMED
BROKER: DISCONNECTED
LIVE TRADING: DISABLED
```

The exact state model should be implemented in the system layer rather than hardcoded in UI strings.

---

# 41. FIRST DESKTOP IMPLEMENTATION

Do NOT build the entire final UI now.

Build the minimum real desktop application:

```text
Application startup
       ↓
Main Window
       ↓
Navigation
       ↓
Dashboard
       ↓
Research
       ↓
Backtest
       ↓
System Status
       ↓
Logs
```

Connect it to the actual underlying services.

Do not create fake data merely to make screenshots look complete.

---

# 42. FIRST DESKTOP DEMONSTRATION

The application should eventually demonstrate this workflow:

```text
Launch QUANT LAB
      ↓
Select Research mode
      ↓
Open Market/Data
      ↓
Select dataset
      ↓
Create/choose simple strategy
      ↓
Open Backtest Lab
      ↓
Run backtest
      ↓
Progress indicator
      ↓
Results
      ↓
Save Experiment
      ↓
Open Experiment Ledger
```

This is the first meaningful end-to-end desktop demonstration.

---

# 43. TESTING THE DESKTOP APPLICATION

Add tests for:

```text
application startup
configuration loading
database initialization
service initialization
UI initialization
job execution
job cancellation
worker failure
application shutdown
state persistence
```

Where practical, add GUI smoke tests.

---

# 44. CLEAN SHUTDOWN

When closing QUANT LAB:

```text
stop new jobs
finish/cancel workers safely
flush logs
persist state
close database connections
disconnect broker safely
close application
```

Do not terminate worker processes blindly.

---

# 45. LIVE TRADING SHUTDOWN

If live trading is active, closing the UI must NOT blindly assume:

```text
all positions are closed
```

The application should clearly distinguish:

```text
positions remain open
orders remain active
broker connection state
```

A UI shutdown is not equivalent to a portfolio shutdown.

---

# 46. PERFORMANCE

The desktop UI must remain responsive while:

```text
backtests
model training
data ingestion
AI analysis
optimization
```

are running.

Never run heavy numerical computation synchronously on the UI thread.

---

# 47. RESOURCE MONITORING

Eventually show:

```text
CPU
RAM
disk
database
worker count
job queue
```

Useful for long-running quantitative experiments.

Do not make this the initial priority.

---

# 48. ENGINEERING DOCUMENTATION

Create/update:

```text
docs/architecture/QUANT_LAB_DESKTOP_ARCHITECTURE.md
docs/architecture/ADR_DESKTOP_FRAMEWORK.md
docs/development/LOCAL_RUN.md
docs/development/PACKAGING.md
docs/operations/RUNTIME_MODES.md
```

Include diagrams.

---

# 49. CURSOR EXECUTION ORDER

Continue from the current workspace.

Do NOT reset the repository.

Execute:

```text
1. Inspect current architecture.
2. Identify existing UI/application entry points.
3. Reconcile with Prompt 02.
4. Choose desktop framework.
5. Document decision in ADR.
6. Create application bootstrap.
7. Create canonical entry point.
8. Create runtime configuration.
9. Create service lifecycle.
10. Create main desktop window.
11. Create navigation.
12. Connect Dashboard.
13. Connect Research/Backtest workflow.
14. Add system health/status.
15. Add background job infrastructure.
16. Add logging viewer.
17. Add graceful shutdown.
18. Test startup and shutdown.
19. Test a real backtest through the GUI.
20. Package a development executable if practical.
```

---

# 50. WHAT NOT TO DO

Do NOT:

```text
✗ rewrite the quantitative core
✗ put trading logic inside UI widgets
✗ hardcode broker credentials
✗ make live trading default
✗ create fake research results
✗ create fake broker responses and call them production-ready
✗ make the application browser-dependent without justification
✗ block the UI with heavy computation
✗ introduce microservices unnecessarily
✗ introduce dozens of dependencies without justification
✗ sacrifice scientific correctness for visual appearance
```

---

# 51. DEFINITION OF DONE FOR THIS STAGE

This stage is successful when:

```text
✓ QUANT LAB launches as a desktop application.
✓ A main window appears.
✓ The application has clear navigation.
✓ Research mode is the default.
✓ System health is visible.
✓ Core services initialize correctly.
✓ Existing quantitative architecture remains intact.
✓ A real backtest can be launched from the UI.
✓ Long-running work does not freeze the UI.
✓ Results are displayed.
✓ The experiment can be saved.
✓ Logs are visible.
✓ Application shuts down cleanly.
✓ No secrets are exposed.
✓ Live trading remains disabled by default.
```

---

# 52. FINAL PRODUCT PRINCIPLE

QUANT LAB should ultimately feel like:

```text
MATHEMATICAL RESEARCH LABORATORY
             +
QUANTITATIVE TRADING PLATFORM
             +
AI RESEARCH SYSTEM
             +
PORTFOLIO/RISK SYSTEM
             +
EXECUTION TERMINAL
```

inside one coherent desktop application.

The user should not have to think about the underlying Python modules, database processes, workers, APIs or internal services.

They should experience:

```text
OPEN QUANT LAB
      ↓
RESEARCH
      ↓
DISCOVER
      ↓
TEST
      ↓
VALIDATE
      ↓
PAPER TRADE
      ↓
SHADOW
      ↓
RISK APPROVAL
      ↓
LIVE EXECUTION
```

while the engineering architecture underneath maintains:

```text
correctness
reproducibility
provenance
security
risk control
auditability
modularity
performance
```

---

# 53. FINAL COMMAND TO CURSOR

**CONTINUE FROM THE CURRENT WORKSPACE.**

**DO NOT RESET THE PROJECT.**

**DO NOT THROW AWAY THE WORK FROM PROMPT 01 OR PROMPT 02.**

First inspect what already exists.

Then reconcile it with this desktop application directive.

Make the smallest number of architectural changes necessary to create a proper desktop application.

Build the desktop shell around the quantitative research engine — not the quantitative research engine around the UI.

The final objective is simple:

> **When the user turns on their computer and launches QUANT LAB, it must behave like a serious standalone quantitative engineering application.**

Proceed autonomously through the implementation, testing, debugging and documentation of this stage.
