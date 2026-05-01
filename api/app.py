from flask import Flask, jsonify, request
from flask_cors import CORS
import random
import re

app = Flask(__name__)
CORS(app)


# ---------------------------------------------------------------------------
# Literal helpers
# ---------------------------------------------------------------------------

def negate_literal(lit: str) -> str:
    return lit[1:] if lit.startswith("¬") else f"¬{lit}"


def strip_outer_parens(s: str) -> str:
    s = s.strip()
    while s.startswith("(") and s.endswith(")"):
        depth = 0
        balanced = True
        for i, ch in enumerate(s):
            if ch == "(":
                depth += 1
            elif ch == ")":
                depth -= 1
                if depth == 0 and i != len(s) - 1:
                    balanced = False
                    break
        if balanced:
            s = s[1:-1].strip()
        else:
            break
    return s


def split_top_level(expr: str, op: str):
    parts = []
    depth = 0
    start = 0
    i = 0
    while i < len(expr):
        ch = expr[i]
        if ch == "(":
            depth += 1
        elif ch == ")":
            depth -= 1
        elif depth == 0 and expr.startswith(op, i):
            parts.append(expr[start:i].strip())
            i += len(op)
            start = i
            continue
        i += 1
    parts.append(expr[start:].strip())
    return [p for p in parts if p]


# ---------------------------------------------------------------------------
# Propositional Logic KB with full CNF conversion + resolution refutation
# ---------------------------------------------------------------------------

class PropositionalLogic:
    def __init__(self):
        self.clauses = []
        self.step_counter = 0

    # Public API
    def tell(self, sentence: str):
        for clause in self._to_cnf(sentence):
            normalized = frozenset(l.strip() for l in clause if l.strip())
            if normalized and normalized not in {frozenset(c) for c in self.clauses}:
                self.clauses.append(normalized)

    def ask(self, query: str) -> bool:
        """Prove query by refutation: add ¬query to a temp KB and check for contradiction."""
        temp = PropositionalLogic()
        temp.clauses = list(self.clauses)        # share frozen sets
        temp.step_counter = self.step_counter
        negated_clauses = self._negate_query_to_cnf(query)
        for clause in negated_clauses:
            normalized = frozenset(l.strip() for l in clause if l.strip())
            if normalized:
                temp.clauses.append(normalized)
        result = temp._resolution_refutation()
        self.step_counter = temp.step_counter   # propagate counter back
        return result

    # ------------------------------------------------------------------
    # Query negation – correctly handles ¬P ∧ ¬W  →  negate each literal
    # robustly using the full CNF pipeline so compound literals work too.
    # ------------------------------------------------------------------
    def _negate_query_to_cnf(self, query: str):
        """
        query is a conjunction of literals, e.g. "¬P_1,2 ∧ ¬W_1,2".
        Its negation is a disjunction of the negated literals:
            P_1,2 ∨ W_1,2
        We convert that disjunction through the full CNF pipeline.
        """
        parts = [p.strip() for p in re.split(r"\s*∧\s*", query) if p.strip()]
        negated_parts = []
        for p in parts:
            p = strip_outer_parens(p)
            if p.startswith("¬"):
                negated_parts.append(p[1:])
            else:
                negated_parts.append(f"¬{p}")
        # Form the disjunction and push through CNF converter
        disj = " ∨ ".join(f"({pt})" for pt in negated_parts)
        return self._to_cnf(disj)

    # ------------------------------------------------------------------
    # Resolution refutation with tautology / subsumption pruning
    # ------------------------------------------------------------------
    def _resolution_refutation(self) -> bool:
        clauses = list(dict.fromkeys(self.clauses))   # deduplicate, preserve order
        # Tautology filter: discard clauses containing both p and ¬p
        clauses = [c for c in clauses if not self._is_tautology(c)]
        seen = set(clauses)

        while True:
            new = set()
            n = len(clauses)

            for i in range(n):
                for j in range(i + 1, n):
                    self.step_counter += 1
                    resolvents = self._resolve(clauses[i], clauses[j])
                    for res in resolvents:
                        if len(res) == 0:
                            return True          # empty clause → contradiction
                        fr = frozenset(res)
                        if fr not in seen and not self._is_tautology(fr):
                            new.add(fr)

            if not new:
                return False                     # saturated without contradiction

            for c in new:
                seen.add(c)
                clauses.append(c)

    @staticmethod
    def _is_tautology(clause) -> bool:
        """A clause is a tautology if it contains both p and ¬p."""
        for lit in clause:
            if negate_literal(lit) in clause:
                return True
        return False

    def _resolve(self, c1, c2):
        resolvents = []
        for lit in c1:
            comp = negate_literal(lit)
            if comp in c2:
                res = (set(c1) | set(c2)) - {lit, comp}
                resolvents.append(res)
        return resolvents

    # ------------------------------------------------------------------
    # CNF conversion – now handles De Morgan's law for ¬(compound)
    # ------------------------------------------------------------------
    def _to_cnf(self, sentence: str):
        sentence = strip_outer_parens(sentence.strip())
        return self._cnf_expr(sentence)

    def _cnf_expr(self, expr: str):
        expr = strip_outer_parens(expr)

        # ── Biconditional ──────────────────────────────────────────────
        if "⇔" in expr:
            left, right = [x.strip() for x in expr.split("⇔", 1)]
            return self._cnf_expr(f"({left} → {right}) ∧ ({right} → {left})")

        # ── Implication ────────────────────────────────────────────────
        if "→" in expr:
            left, right = [x.strip() for x in expr.split("→", 1)]
            return self._cnf_expr(f"¬({left}) ∨ ({right})")

        # ── Negation – apply De Morgan's law for compound subexpressions ─
        if expr.startswith("¬"):
            inner = strip_outer_parens(expr[1:])

            # ¬¬A  →  A
            if inner.startswith("¬"):
                return self._cnf_expr(inner[1:])

            # ¬(A ∧ B)  →  ¬A ∨ ¬B
            and_parts = split_top_level(inner, "∧")
            if len(and_parts) > 1:
                negated = " ∨ ".join(f"¬({p})" for p in and_parts)
                return self._cnf_expr(negated)

            # ¬(A ∨ B)  →  ¬A ∧ ¬B
            or_parts = split_top_level(inner, "∨")
            if len(or_parts) > 1:
                negated = " ∧ ".join(f"¬({p})" for p in or_parts)
                return self._cnf_expr(negated)

            # ¬(A → B)  →  A ∧ ¬B
            if "→" in inner:
                left, right = [x.strip() for x in inner.split("→", 1)]
                return self._cnf_expr(f"({left}) ∧ ¬({right})")

            # ¬(A ⇔ B)  →  (A ∧ ¬B) ∨ (¬A ∧ B)
            if "⇔" in inner:
                left, right = [x.strip() for x in inner.split("⇔", 1)]
                return self._cnf_expr(
                    f"(({left}) ∧ ¬({right})) ∨ (¬({left}) ∧ ({right}))"
                )

            # ¬literal – base case, keep as-is
            return [[expr]]

        # ── Conjunction ────────────────────────────────────────────────
        and_parts = split_top_level(expr, "∧")
        if len(and_parts) > 1:
            clauses = []
            for part in and_parts:
                clauses.extend(self._cnf_expr(part))
            return clauses

        # ── Disjunction ────────────────────────────────────────────────
        or_parts = split_top_level(expr, "∨")
        if len(or_parts) > 1:
            left = self._cnf_expr(or_parts[0])
            for part in or_parts[1:]:
                right = self._cnf_expr(part)
                left = self._distribute_or(left, right)
            return left

        # ── Base case: atom ────────────────────────────────────────────
        return [[expr]]

    def _distribute_or(self, cnf1, cnf2):
        """Distribute OR over AND: (A∧B) ∨ (C∧D) = (A∨C)∧(A∨D)∧(B∨C)∧(B∨D)"""
        result = []
        for c1 in cnf1:
            for c2 in cnf2:
                clause = list(dict.fromkeys(c1 + c2))   # preserve order, deduplicate
                result.append(clause)
        return result


# ---------------------------------------------------------------------------
# Wumpus World
# ---------------------------------------------------------------------------

class WumpusWorld:
    def __init__(self, rows, cols):
        self.rows = rows
        self.cols = cols
        self.agent_pos = [0, 0]
        self.visited = {(0, 0)}
        self.confirmed_safe = {(0, 0)}
        self.pits = set()
        self.wumpus = None
        self.percepts = []
        self.game_over = False          # FIX: track death
        self.game_over_reason = None    # "pit" | "wumpus" | None
        self.kb = PropositionalLogic()
        self._generate_world()
        self._initialize_start_cell()

    def _generate_world(self):
        for r in range(self.rows):
            for c in range(self.cols):
                if (r, c) != (0, 0) and random.random() < 0.15:
                    self.pits.add((r, c))

        while True:
            r = random.randint(0, self.rows - 1)
            c = random.randint(0, self.cols - 1)
            if (r, c) != (0, 0) and (r, c) not in self.pits:
                self.wumpus = (r, c)
                break

    def _initialize_start_cell(self):
        self.kb.tell("¬P_0,0")
        self.kb.tell("¬W_0,0")
        self._update_current_cell_knowledge()

    def _adjacent_cells(self, r, c):
        cells = []
        for dr, dc in [(-1, 0), (1, 0), (0, -1), (0, 1)]:
            nr, nc = r + dr, c + dc
            if 0 <= nr < self.rows and 0 <= nc < self.cols:
                cells.append((nr, nc))
        return cells

    def _sense_current_cell(self):
        r, c = self.agent_pos
        percepts = []
        for nr, nc in self._adjacent_cells(r, c):
            if (nr, nc) in self.pits:
                percepts.append("Breeze")
                break
        for nr, nc in self._adjacent_cells(r, c):
            if (nr, nc) == self.wumpus:
                percepts.append("Stench")
                break
        return percepts

    def _tell_kb_from_percepts(self, r, c, percepts):
        cell = f"{r},{c}"
        adj_cells = self._adjacent_cells(r, c)
        adj_pits = [f"P_{nr},{nc}" for nr, nc in adj_cells]
        adj_w = [f"W_{nr},{nc}" for nr, nc in adj_cells]

        if "Breeze" in percepts:
            self.kb.tell(f"B_{cell}")
        else:
            self.kb.tell(f"¬B_{cell}")
            # No breeze → no pits in any adjacent cell
            for nr, nc in adj_cells:
                self.kb.tell(f"¬P_{nr},{nc}")
                self.confirmed_safe.add((nr, nc))

        if "Stench" in percepts:
            self.kb.tell(f"S_{cell}")
        else:
            self.kb.tell(f"¬S_{cell}")
            # No stench → Wumpus not in any adjacent cell
            for nr, nc in adj_cells:
                self.kb.tell(f"¬W_{nr},{nc}")

        if adj_pits:
            self.kb.tell(f"B_{cell} ⇔ ({' ∨ '.join(adj_pits)})")
        if adj_w:
            self.kb.tell(f"S_{cell} ⇔ ({' ∨ '.join(adj_w)})")

    def _update_current_cell_knowledge(self):
        r, c = self.agent_pos
        self.percepts = self._sense_current_cell()
        self._tell_kb_from_percepts(r, c, self.percepts)

    def is_safe(self, r, c) -> bool:
        """Return True if KB can prove the cell is free of pits and Wumpus."""
        if (r, c) in self.confirmed_safe or (r, c) in self.visited:
            return True
        if (r, c) == (0, 0):
            return True
        query = f"¬P_{r},{c} ∧ ¬W_{r},{c}"
        result = self.kb.ask(query)
        if result:
            self.confirmed_safe.add((r, c))
        return result

    def get_safe_moves(self):
        if self.game_over:
            return []
        r, c = self.agent_pos
        moves = []
        for name, nr, nc in [
            ("up",    r - 1, c),
            ("down",  r + 1, c),
            ("left",  r, c - 1),
            ("right", r, c + 1),
        ]:
            if 0 <= nr < self.rows and 0 <= nc < self.cols:
                if self.is_safe(nr, nc):
                    moves.append(name)
        return moves

    def move(self, direction: str):
        """
        FIX: Only execute the move if the game is still active.
        After moving, check for death (pit / wumpus).
        Safe-move enforcement is advisory – the agent CAN move into unknown
        cells but the KB flags them as potentially dangerous.
        """
        if self.game_over:
            return self.get_state()

        r, c = self.agent_pos
        nr, nc = r, c

        if direction == "up" and r > 0:
            nr, nc = r - 1, c
        elif direction == "down" and r < self.rows - 1:
            nr, nc = r + 1, c
        elif direction == "left" and c > 0:
            nr, nc = r, c - 1
        elif direction == "right" and c < self.cols - 1:
            nr, nc = r, c + 1
        else:
            # Out-of-bounds direction – do nothing
            return self.get_state()

        self.agent_pos = [nr, nc]
        self.visited.add((nr, nc))

        # FIX: Check death BEFORE telling KB / sensing
        if (nr, nc) in self.pits:
            self.game_over = True
            self.game_over_reason = "pit"
            return self.get_state()

        if (nr, nc) == self.wumpus:
            self.game_over = True
            self.game_over_reason = "wumpus"
            return self.get_state()

        # Safe cell – add to confirmed safe and update KB
        self.confirmed_safe.add((nr, nc))
        self._update_current_cell_knowledge()
        return self.get_state()

    def get_state(self):
        grid = [["Unknown" for _ in range(self.cols)] for _ in range(self.rows)]

        for r in range(self.rows):
            for c in range(self.cols):
                pos = (r, c)
                if pos == tuple(self.agent_pos):
                    grid[r][c] = "Agent"
                elif pos in self.visited:
                    if pos in self.pits:
                        grid[r][c] = "Pit"
                    elif pos == self.wumpus:
                        grid[r][c] = "Wumpus"
                    elif pos in self.confirmed_safe:
                        grid[r][c] = "Safe"
                    else:
                        grid[r][c] = "Visited"
                elif pos in self.confirmed_safe:
                    grid[r][c] = "Safe"

        return {
            "grid": grid,
            "agent_pos": self.agent_pos,
            "percepts": self.percepts,
            "safe_moves": self.get_safe_moves(),
            "inference_steps": self.kb.step_counter,
            "visited_count": len(self.visited),
            "confirmed_safe_count": len(self.confirmed_safe),
            "game_over": self.game_over,                    # FIX: expose to frontend
            "game_over_reason": self.game_over_reason,      # FIX: "pit" | "wumpus" | None
        }


# ---------------------------------------------------------------------------
# Flask routes
# ---------------------------------------------------------------------------

game = None


@app.route("/start_game", methods=["POST"])
def start_game():
    global game
    data = request.json or {}
    rows = max(3, min(10, int(data.get("rows", 4))))
    cols = max(3, min(10, int(data.get("cols", 4))))
    game = WumpusWorld(rows, cols)
    return jsonify(game.get_state())


@app.route("/move", methods=["POST"])
def move():
    global game
    if not game:
        return jsonify({"error": "Game not started"}), 400
    data = request.json or {}
    direction = data.get("direction", "up")
    return jsonify(game.move(direction))


@app.route("/get_safe_moves", methods=["GET"])
def get_safe_moves():
    global game
    if not game:
        return jsonify({"error": "Game not started"}), 400
    return jsonify({"safe_moves": game.get_safe_moves()})


@app.route("/reset", methods=["POST"])
def reset():
    global game
    game = None
    return jsonify({"message": "reset"})


if __name__ == "__main__":
    app.run(debug=True, port=5000)
