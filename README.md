# Dynamic Wumpus Logic Agent

A web-based **Wumpus World** project that uses **propositional logic** and **resolution refutation** to infer safe moves in a grid environment.  
The project combines a **Flask backend** for reasoning with a **React frontend** for visualization and interaction.

## Live Demo

- **Deployed App:** [https://wumpus-chi.vercel.app/](https://wumpus-chi.vercel.app/)

## Overview

This project simulates a Wumpus World environment where an agent moves through a grid while avoiding pits and the Wumpus.  
The agent uses percepts such as **Breeze** and **Stench** to update its knowledge base and decide which neighboring cells are safe.  
The frontend displays the grid in real time and shows useful game metrics such as percepts, safe moves, and inference steps.

## Features

- Dynamic grid generation.
- Random pit and Wumpus placement.
- Percept detection for Breeze and Stench.
- Knowledge base updates using propositional logic.
- CNF conversion and resolution refutation.
- Safe move inference.
- Game over detection.
- Modern dashboard-style UI.

## Technology Stack

- Python
- Flask
- Flask-CORS
- React
- JavaScript
- HTML
- CSS

## Project Structure

```text
wumpus-agent-project/
├── backend/
│   └── app.py
├── src/
│   ├── App.js
│   └── App.css
├── public/
├── package.json
└── requirements.txt
```

## How It Works

### Backend
The Flask backend generates the world, senses percepts, maintains the knowledge base, and decides whether nearby cells are safe.  
It uses propositional logic rules and resolution to infer safety from the agent’s observations.

### Frontend
The React frontend shows the grid, movement controls, and live metrics.  
It sends move requests to the backend and updates the interface based on the returned game state.

## Installation

### 1. Clone the repository
```bash
git clone https://github.com/YOUR_USERNAME/YOUR_REPO.git
cd wumpus-agent-project
```

### 2. Install backend dependencies
```bash
cd backend
pip install -r requirements.txt
```

### 3. Install frontend dependencies
```bash
cd ..
npm install
```

## Run Locally

### Start the backend
```bash
cd backend
python app.py
```

### Start the frontend
Open a new terminal:

```bash
npm start
```

## Usage

1. Open the app in your browser.
2. Enter the grid size.
3. Click **Start Game**.
4. Move the agent using the direction buttons.
5. Observe percepts, safe moves, and inference steps.
6. Avoid pits and the Wumpus.

## Deployment

The project is deployed on Vercel at:  
[https://wumpus-chi.vercel.app/](https://wumpus-chi.vercel.app/)

## LinkedIn Post

You can view the project post here:  
[LinkedIn Post](https://www.linkedin.com/posts/suleman-arshad-b8867b33a_artificialintelligence-machinelearning-reactjs-share-7456055402229760000-LJAM?utm_source=share&utm_medium=member_desktop&rcm=ACoAAFUsL9gBKZgRhWtGxgMv9EAk6iIBWmT4T-k)

## Future Improvements

- Persistent game state.
- Auto-solving agent.
- Better path planning.
- Score tracking.
- Improved logical inference speed.

## Author

**Suleman Arshad**

## License

This project is for educational and academic use.
