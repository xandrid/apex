# APEX Desktop Migration Plan

## Goal
Offload all heavy computation (Backend, Vector DB, Ingestion) to a powerful Desktop PC while maintaining the MacBook as the primary "Control Plane" for editing and interaction.

## Architecture
- **Local (MacBook)**: Source Code, Editor (VS Code), AI Agent, "Control" Scripts.
- **Remote (Desktop)**: Runtime Environment (Python, Node), Vector Index, Heavy Compute.
- **Link**: `SSH` for execution, `rsync` for code synchronization.

## Phase 1: Connectivity
- [ ] Identify Desktop IP and OS.
- [ ] Configure SSH Key-based Authentication (Password-less access).
- [ ] Create `.ssh/config` entry for easy access (e.g., `ssh apex-desktop`).

## Phase 2: Remote Environment Setup
- [ ] Install Dependencies on Desktop:
    - Python 3.10+
    - Node.js & npm
    - Git
- [ ] Clone/Copy APEX repository to Desktop.
- [ ] Configure Environment Variables (`.env`) on Desktop.

## Phase 3: Workflow Automation
We will replace local run scripts with "Remote Wrappers" that:
1.  **Sync**: Push latest code changes from Mac -> Desktop.
2.  **Execute**: Run the command on Desktop via SSH.
3.  **Stream**: Pipe logs back to Mac terminal.

### New Commands
- `apex-sync`: One-way sync of code to desktop.
- `apex-start`: Syncs code, then starts Backend + Frontend on Desktop.
- `apex-stop`: Kills all APEX processes on Desktop (Gaming Mode).
- `apex-status`: Checks resource usage (GPU/CPU) on Desktop.

## Phase 4: Verification
- [ ] Verify "Start APEX" launches services on Desktop.
- [ ] Verify MacBook can access Desktop's Frontend (Port 3000) and Backend (Port 8000).
    - *Note: We may need to configure SSH Tunnels or expose ports on Desktop firewall.*

## User Requirements Checklist
- [ ] Desktop OS (Windows/Linux/Mac)?
- [ ] Desktop Local IP Address?
- [ ] SSH Access Enabled?
