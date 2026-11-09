Heads-Up Limit Hold'em Nash Equilibrium Bot

A Heads-Up Limit Texas Hold'em poker bot built using Monte Carlo Counterfactual Regret Minimization (MCCFR) for a Bachelor's thesis at the University of Bucharest.

The project features a parallelized training pipeline, a web interface to play against the bot, and an independent Computer Vision/OCR assistant.

🚀 Quick Start

1. Prerequisites

Windows with WSL2 (Ubuntu)

Python 3.10+ & Node.js

Tesseract OCR (on Windows)

2. Offline MCCFR Training (WSL2)

cd training/
python3 train_mccfr.py --workers 4 --duration-hours 20


3. Run Web Application

Backend (FastAPI - WSL2):

cd backend/ && uvicorn main:app --reload --port 8000


Frontend (React - Host/WSL2):

cd frontend/ && npm install && npm start


Access the game interface at http://localhost:3000.

4. Run Screen Assistant Module

Start advisor service in WSL2: python3 advisor/advisor_service.py

Calibrate screen regions on Windows: python advisor/calibrate.py

Run screen analyzer on Windows: python advisor/advisor_windows.py

🛠 Features & Tech Stack

Game Engine & RL: OpenSpiel (universal_poker), treys

Backend & Frontend: FastAPI, React.js

Computer Vision: OpenCV, Tesseract OCR

Abstraction: 169 canonical preflop buckets, Effective Hand Strength (EHS) Monte Carlo sampling post-flop.

👤 Author

Muscalu David-Cristian (Faculty of Mathematics and Computer Science, University of Bucharest)

Coordinators: Assoc. Prof. Dr. Bogdan Alexe, Assist. PhD Cand. Alexandra Diaconu
