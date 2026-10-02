# Lamport Mutual Exclusion Simulator

An interactive and explainable software-based simulation and experimentation environment for Lamport Mutual Exclusion.
(Simulated processes on one laptop - not a production distributed lock.)

## Run (Windows PowerShell) - open TWO windows

### Window 1 - backend
```powershell
cd lamport-simulator\backend
python -m venv venv
.\venv\Scripts\Activate.ps1
pip install -r requirements.txt
uvicorn app:app --reload --port 8000
```
If activation is blocked: `Set-ExecutionPolicy -Scope CurrentUser -ExecutionPolicy RemoteSigned`

### Window 2 - frontend
```powershell
cd lamport-simulator\frontend
npm install
npm run dev
```
Open http://localhost:5173  (API docs: http://localhost:8000/docs)

## Tests (backend window, venv active)
```powershell
python -m pytest -q
python run_randomized.py
```

## Notes
- Lamport's algorithm assumes FIFO channels. "FIFO channels" is ON by default. Turning it off (or the extra
  scenario "Non-FIFO channels") deliberately breaks that assumption, and the safety monitor then reports real violations.
- Experiments are stored in backend/lamport.db (SQLite). After a server restart an experiment is rebuilt from its action log.
