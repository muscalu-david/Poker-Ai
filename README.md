Approximating Nash Equilibrium in Heads-Up Limit Hold'em PokerThis project represents a Bachelor's thesis focused on the design, implementation, and evaluation of a Heads-Up Limit Texas Hold'em poker bot based on the Monte Carlo Counterfactual Regret Minimization (MCCFR) algorithm.The system includes:A multi-process, parallelized offline MCCFR training pipeline.A REST Backend (FastAPI) & Frontend (React) for playing directly against the trained bot.An independent Assistant Module (Computer Vision & OCR) that reads the game state directly from the screen and provides real-time action recommendations.🏗 System ArchitectureThe system is split into four main components:+-----------------------------------------------------------------------+
|                            OFFLINE TRAINING                           |
|  - MCCFR (External Sampling) parallelized multi-process (WSL2/Linux)  |
|  - Precomputed EHS table generation + State abstraction (bucketing)   |
+-----------------------------------------------------------------------+
                                   |
                                   v (Average Strategy File)
+-----------------------------------------------------------------------+
|                            GAME APPLICATION                           |
|  - Frontend: React (Poker Table UI, Live Action Log)                  |
|  - Backend: FastAPI (Manages pyspiel.State, REST API endpoints)       |
|  - Bot Agent: Loads the trained strategy                              |
+-----------------------------------------------------------------------+
                                   ^
                                   | (Action Recommendation over HTTP)
+-----------------------------------------------------------------------+
|                    ASSISTANT MODULE (VISION / OCR)                    |
|  - Windows Agent (OpenCV & Tesseract): Screen capture, card detection |
|  - Linux Service (WSL2): OpenSpiel state reconstruction & query       |
+-----------------------------------------------------------------------+
🛠 Technologies and Libraries UsedCore Algorithmic / Game Theory: OpenSpiel (universal_poker), treys (poker hand evaluation).Backend: Python 3, FastAPI, Uvicorn.Frontend: React, HTML5 / CSS3 (Interactive Poker Table UI).Computer Vision / OCR: OpenCV, Tesseract OCR.Training Environment: WSL2 (Ubuntu / Linux) – required for OpenSpiel's universal_poker module.📊 State Space Abstraction (Bucketing)To ensure algorithm convergence within a reasonable timeframe on standard hardware, game states are abstracted into string keys of the format:$$\text{P:\{player\}\vert{}B:\{bucket\}\vert{}R:\{round\}\vert{}H:\{betting\_history\}\vert{}L:\{legal\_actions\}}$$Preflop: 169 canonical buckets (pairs, suited, and offsuit hand combinations).Flop, Turn, River: Buckets mapped based on Effective Hand Strength (EHS).Flop: Precomputed offline lookup table built via Monte Carlo simulations ($1000$ samples per combination).Turn & River: Evaluated dynamically on query via Monte Carlo sampling ($100$ samples per state).Betting History: Maintains a bounded window of the last 4 betting actions ($fold/call/bet$).🚀 Installation and Usage1. PrerequisitesWindows with WSL2 (Ubuntu) installed.Python 3.10+ (in both Windows and WSL2 environments).Tesseract OCR installed on Windows.2. Offline Training (MCCFR)Training runs across multiple worker processes within the Linux environment (WSL2):# Inside WSL2
cd training/
python3 train_mccfr.py --workers 4 --duration-hours 20
The resulting average strategy will be serialized into a checkpoint/model file loaded by the backend.3. Running the Game Application (Client-Server)Backend (FastAPI) - Running in WSL2:cd backend/
pip install -r requirements.txt
uvicorn main:app --reload --host 0.0.0.0 --port 8000
Frontend (React) - Running on Host/WSL2:cd frontend/
npm install
npm start
The application will be accessible at http://localhost:3000.4. Computer Vision Assistant ModuleThe assistant is split into two processes to overcome cross-platform constraints of OpenSpiel:Start Recommendation Service (Linux / WSL2):cd advisor/
python3 advisor_service.py
Calibrate Screen Regions (Windows - Executed once):python calibrate.py
Drag bounding boxes over your hole cards, board cards, the LIVE LOG text region, and action buttons.Start Screen Capture and Notifications (Windows):python advisor_windows.py
The system polls screen regions every 1.5 seconds and triggers native Windows notifications displaying recommended actions (e.g., CALL, BET, FOLD).📈 Experimental EvaluationThe trained bot was evaluated in automated matches against two benchmark agents (starting stack of $12000$ chips per hand):Random Bot:Result: Consistent linear advantage ($+48,600$ chips profit over 400 hands).Expectimax Bot (Heuristic / Monte Carlo):Early Training Checkpoint: $-41,700$ chips loss over 400 hands.Extended Training Checkpoint (~124 million additional iterations): Complete reversal to $+34,600$ chips profit over 500 hands.👤 AuthorGraduate: Muscalu David-CristianScientific Advisors: Assoc. Prof. Dr. Bogdan Alexe, Assist. PhD Cand. Alexandra Diaconu
