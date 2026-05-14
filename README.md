# CHARMM-GUI API Toolkit
A unified Bash and Python toolkit for interacting with CHARMM-GUI backend API services, including **Quick Bilayer**, job status monitoring, Redis Queue insights, and local job history storage (JSON or SQLite).

This repository contains:

- **Bash Scripts** for lightweight command-line workflows
- **Python Package + CLI** for powerful scripting, job tracking, and automation
- **Job History System** (JSON or SQLite backend)
- **Pretty-printed status views** with rqinfo and queue rank
- **Modular API design** to support future CHARMM-GUI modules

---

# Installation

Clone the repository:

```bash
git clone https://github.com/junepark6/cgui_api.git
cd charmmgui
```

## Install the Python package:
```bash
python setup.py install
```

# Documentation
## Bash Usage Documentation
See README_bash.md
## Python Usage Documentation
See README_python.md

## Features
- Quick Bilayer API submission
- Secure token-based authentication
- Pretty-printed job status with Redis queue info
- Automatic job history recording (JSON or SQLite)
- Search/filter job history (--contains, --after, --module, etc.)
- Download generated CHARMM-GUI tar files
- Modular architecture

## Contact
Maintainer: Sang-Jun Park
Email: junepark6@gmail.com
