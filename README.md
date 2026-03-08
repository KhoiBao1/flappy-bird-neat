# 🐦 Flappy Bird × NEAT AI

> A full recreation of the classic Flappy Bird game — built from scratch in Python, powered by a NEAT neural network, and deployed as a live web application.

[![Python](https://img.shields.io/badge/Python-3.11-blue?logo=python&logoColor=white)](https://python.org)
[![Pygame](https://img.shields.io/badge/Pygame-2.6.1-green?logo=pygame)](https://pygame.org)
[![Flask](https://img.shields.io/badge/Flask-3.1-black?logo=flask)](https://flask.palletsprojects.com)
[![NEAT](https://img.shields.io/badge/NEAT--Python-2.0-orange)](https://neat-python.readthedocs.io)
[![Render](https://img.shields.io/badge/Deployed%20on-Render-46E3B7?logo=render)](https://render.com)

---

## 🌐 Live Demo

🔗 **[flappy-bird-neat.onrender.com](https://flappy-bird-neat.onrender.com)**

> ⚠️ **Note:** The live demo runs on Render's free tier, so graphics have been slightly reduced to maintain performance on limited server resources. For the best experience, see the [Run Locally](#-run-locally-best-experience) section below.

---

## 📖 About This Project

This project is a **complete ground-up recreation** of Flappy Bird — not a fork, not a tutorial copy. Every class, physics calculation, collision system, and rendering pipeline was written manually.

What makes it more than just a clone is the integration of **NEAT (NeuroEvolution of Augmenting Topologies)** — a genetic algorithm that evolves neural networks over generations. Watch the AI go from completely clueless in Generation 1 to effortlessly navigating pipes by Generation 5–10.

The game is served as a **live web app** using Flask, which streams the Pygame canvas as an MJPEG video feed to the browser — meaning the actual Python game runs on the server and is watched in real time.

---

## 🎮 Three Game Modes

| Mode | Description |
|------|-------------|
| 🤖 **AI + Vision Rays** | NEAT AI trains in real time. Red sensor lines visualize the exact inputs fed into the neural network each frame. |
| 🎮 **Player Mode** | Classic Flappy Bird. Click or press `Space` to flap. Includes a Game Over screen with a **Try Again** button. |
| ✨ **AI Clean Mode** | Same NEAT AI, but with a clean interface — no sensor lines. Watch the birds evolve without distraction. |

---

## 🧠 How the AI Works

The AI uses **NEAT (NeuroEvolution of Augmenting Topologies)** via the `neat-python` library.

Each bird has its own small neural network with:
- **3 inputs:** bird's Y position, distance to the top pipe gap, distance to the bottom pipe gap
- **1 output:** whether to jump (> 0.5 = jump)

Each generation, birds that survive longer and pass more pipes receive higher **fitness scores**. The top performers survive and their networks are mutated and bred into the next generation. Over time, the population evolves to play the game well — no hardcoded rules, no human guidance.

```
Inputs (3)         Hidden Layer        Output (1)
─────────────      ────────────        ──────────
Bird Y pos    ──►                 ──►  Jump?
Top gap dist  ──►   [NEAT auto]   ──►
Bot gap dist  ──►                 ──►
```

---

## 🏗️ Architecture

```
flappy-bird-neat/
│
├── app.py                    # Flask server — streams Pygame via MJPEG
├── Flappy_bird.py            # AI mode with red vision rays
├── Flappy_bird_player.py     # Human player mode
├── Flappy_bird_ai_clean.py   # AI mode, clean view
│
├── templates/
│   └── index.html            # Web UI — mode selector + game stream
│
├── config-feedforward.txt    # NEAT algorithm configuration
├── requirements.txt
├── render.yaml               # Render deployment config
│
└── imgs/
    ├── bird1.png / bird2.png / bird3.png
    ├── pipe.png
    ├── base.png
    └── bg.png
```

### How the web streaming works

```
Pygame renders frame
       ↓
Surface captured as JPEG bytes  (capture() function)
       ↓
Flask streams bytes via MJPEG   (/video_feed route)
       ↓
Browser displays as <img> tag   (looks like live video)
       ↓
User clicks → POST /action → bird.jump() on server
```

---

## 🚀 Run Locally (Best Experience)

Running locally gives full 60 FPS with full-resolution graphics — no streaming overhead.

**1. Clone the repository**
```bash
git clone https://github.com/KhoiBao1/flappy-bird-neat.git
cd flappy-bird-neat
```

**2. Install dependencies**
```bash
pip install -r requirements.txt
```

**3. Start the server**
```bash
python app.py
```

**4. Open your browser at** `http://localhost:10000`

### ⚡ Optional: Full-resolution graphics

The live demo uses a reduced-quality capture function to save bandwidth on the free server. To restore full quality locally, open `app.py` and replace the `capture()` function:

**Current (optimized for server):**
```python
def capture(win):
    global latest_frame
    buf = io.BytesIO()
    small = pygame.transform.scale(win, (360, 576))
    pygame.image.save(small, buf, "JPEG")
    from PIL import Image
    buf.seek(0)
    img = Image.open(buf)
    out = io.BytesIO()
    img.save(out, format='JPEG', quality=50)
    with frame_lock:
        latest_frame = out.getvalue()
```

**Replace with (full quality):**
```python
def capture(win):
    global latest_frame
    buf = io.BytesIO()
    pygame.image.save(win, buf, "JPEG")
    with frame_lock:
        latest_frame = buf.getvalue()
```

---

## 🛠️ Tech Stack

| Technology | Role |
|------------|------|
| **Python 3.11** | Core language |
| **Pygame 2.6** | Game engine — rendering, physics, collision |
| **NEAT-Python** | Neuroevolution algorithm |
| **Flask** | Web server + MJPEG streaming |
| **HTML / CSS / JS** | Frontend UI |
| **Render** | Cloud deployment |

---

## 📦 Requirements

```
flask
pygame==2.6.1
neat-python
```

---

## 🔧 NEAT Configuration Highlights

Key parameters from `config-feedforward.txt` that shape how the AI evolves:

| Parameter | Value | Effect |
|-----------|-------|--------|
| `pop_size` | 20 | Birds per generation |
| `fitness_threshold` | 100 | Stop when a bird scores this |
| `activation_default` | tanh | Neuron activation function |
| `weight_mutate_rate` | 0.8 | How often weights mutate |

---

## 📸 Preview

| Landing Page | AI Vision Rays | Player Mode |
|:---:|:---:|:---:|
| Choose your mode | Red lines = neural inputs | Classic gameplay |

---

## 👤 Author

**Bao Khoi**
- GitHub: [@KhoiBao1](https://github.com/KhoiBao1)

---

## 📄 License

This project is open source and available under the [MIT License](LICENSE).

---

<div align="center">
  <sub>Built from scratch with Python 🐍 · Powered by evolution 🧬 · Deployed on the web 🌐</sub>
</div>
