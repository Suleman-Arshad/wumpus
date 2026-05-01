import React, { useState, useCallback } from 'react';
import './App.css';

const CELL_COLORS = {
  Unknown: '#64748b',
  Safe: '#22c55e',
  Visited: '#94a3b8',
  Pit: '#ef4444',
  Wumpus: '#7f1d1d',
  Agent: '#2563eb',
};

function App() {
  const [gridSize, setGridSize] = useState({ rows: 4, cols: 4 });
  const [gameState, setGameState] = useState(null);
  const [gameStarted, setGameStarted] = useState(false);
  const [loading, setLoading] = useState(false);

  const apiBase = 'http://localhost:5000';

  const startGame = useCallback(async () => {
    setLoading(true);
    try {
      const res = await fetch(`${apiBase}/start_game`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(gridSize),
      });
      const data = await res.json();
      setGameState(data);
      setGameStarted(true);
    } catch (err) {
      console.error('start_game error:', err);
    } finally {
      setLoading(false);
    }
  }, [gridSize]);

  const moveAgent = useCallback(async (direction) => {
    setLoading(true);
    try {
      const res = await fetch(`${apiBase}/move`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ direction }),
      });
      const data = await res.json();
      setGameState(data);
    } catch (err) {
      console.error('move error:', err);
    } finally {
      setLoading(false);
    }
  }, []);

  const resetGame = async () => {
    try {
      await fetch(`${apiBase}/reset`, { method: 'POST' });
      setGameStarted(false);
      setGameState(null);
    } catch (err) {
      console.error('reset error:', err);
    }
  };

  const renderCell = (cell, r, c) => {
    const background = CELL_COLORS[cell] || '#64748b';
    const text =
      cell === 'Agent' ? 'A' :
      cell === 'Safe' ? 'S' :
      cell === 'Visited' ? 'V' :
      cell === 'Pit' ? 'P' :
      cell === 'Wumpus' ? 'W' :
      '';

    return (
      <div
        key={`${r}-${c}`}
        className="cell"
        style={{
          backgroundColor: background,
          border: cell === 'Agent' ? '3px solid #0f172a' : '1px solid rgba(255,255,255,0.08)',
        }}
        title={`(${r}, ${c}) - ${cell}`}
      >
        {text}
      </div>
    );
  };

  const statusClass = gameState?.game_over
    ? `status status-${gameState.game_over_reason}`
    : 'status status-active';

  return (
    <div className="App">
      <header className="topbar">
        <div>
          <h1>Dynamic Wumpus Logic Agent</h1>
          <p>Propositional logic, resolution refutation, and dynamic percepts</p>
        </div>
      </header>

      {!gameStarted ? (
        <div className="panel start-panel">
          <h2>Start New Game</h2>
          <div className="controls">
            <label>
              Rows
              <input
                type="number"
                min="3"
                max="10"
                value={gridSize.rows}
                onChange={(e) =>
                  setGridSize({ ...gridSize, rows: Number(e.target.value) })
                }
              />
            </label>

            <label>
              Cols
              <input
                type="number"
                min="3"
                max="10"
                value={gridSize.cols}
                onChange={(e) =>
                  setGridSize({ ...gridSize, cols: Number(e.target.value) })
                }
              />
            </label>
          </div>

          <button className="primary-btn" onClick={startGame} disabled={loading}>
            {loading ? 'Starting...' : 'Start Game'}
          </button>
        </div>
      ) : (
        <div className="layout">
          <section className="panel metrics-panel">
            <h2>Metrics</h2>
            <div className={statusClass}>
              {gameState?.game_over
                ? `Game Over: ${gameState.game_over_reason?.toUpperCase()}`
                : 'Game Running'}
            </div>

            <div className="metric-list">
              <p><strong>Agent Position:</strong> {gameState?.agent_pos?.join(', ')}</p>
              <p><strong>Percepts:</strong> {gameState?.percepts?.length ? gameState.percepts.join(', ') : 'None'}</p>
              <p><strong>Inference Steps:</strong> {gameState?.inference_steps ?? 0}</p>
              <p><strong>Visited Cells:</strong> {gameState?.visited_count ?? 0}</p>
              <p><strong>Confirmed Safe:</strong> {gameState?.confirmed_safe_count ?? 0}</p>
              <p><strong>Safe Moves:</strong> {gameState?.safe_moves?.length ? gameState.safe_moves.join(', ') : 'None'}</p>
            </div>

            <button className="reset-btn" onClick={resetGame}>
              New Game
            </button>
          </section>

          <section className="panel grid-panel">
            <h2>Grid</h2>
            <div
              className="grid"
              style={{
                gridTemplateColumns: `repeat(${gridSize.cols}, 72px)`,
                gridTemplateRows: `repeat(${gridSize.rows}, 72px)`,
              }}
            >
              {gameState?.grid?.map((row, r) =>
                row.map((cell, c) => renderCell(cell, r, c))
              )}
            </div>
          </section>

          <section className="panel control-panel">
            <h2>Move Agent</h2>
            {gameState?.game_over ? (
              <div className="game-over-box">
                <p>The game has ended.</p>
                <button className="primary-btn" onClick={resetGame}>
                  Start New Game
                </button>
              </div>
            ) : (
              <>
                <div className="move-buttons">
                  <button onClick={() => moveAgent('up')} disabled={loading}>Up</button>
                  <button onClick={() => moveAgent('left')} disabled={loading}>Left</button>
                  <button onClick={() => moveAgent('down')} disabled={loading}>Down</button>
                  <button onClick={() => moveAgent('right')} disabled={loading}>Right</button>
                </div>

                <p className="hint">
                  Move the agent and let the knowledge base infer safe cells.
                </p>
              </>
            )}
          </section>
        </div>
      )}
    </div>
  );
}

export default App;
