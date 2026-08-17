# EIK setup on Windows

EIK's Python features run directly on Windows. The external Linux security tools
(`nmap`, `nikto`, `nuclei`, and others) require Kali/Ubuntu through WSL2 or a
separate Linux machine.

## Python environment

This workspace is configured with a local virtual environment at `.venv`.
Open PowerShell in `C:\EIK` and use:

```powershell
.\.venv\Scripts\Activate.ps1
python EIK.py --help
python -m unittest discover -s tests -v
```

If you clone the project again, recreate it with:

```powershell
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install --upgrade pip
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
```

## Linux scanner tools

This PC currently has WSL installed but reports that virtualization is disabled,
so no Linux distribution can start. Enable virtualization in BIOS/UEFI and enable
the Windows **Virtual Machine Platform** feature, then install a Linux distribution.
After that, install only the tools needed for your authorized assessment inside
the Linux environment. EIK still provides its built-in HTTP hardening baseline on
Windows without those tools.

## First scan

Create `scope.txt` containing only a domain you own, then run a standard profile:

```text
your-site.example
```

```powershell
.\.venv\Scripts\python.exe EIK.py -t https://your-site.example `
  --assessment-profile standard --authorized `
  --engagement-id my-website-2026 --scope scope.txt --sarif --fail-on high
```

The engagement label is your own text; it is not a government ID.
