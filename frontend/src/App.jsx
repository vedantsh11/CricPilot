import { useMemo, useState } from "react";
import "./App.css";

const API = "http://127.0.0.1:8000";
const BUDGET = 100;

const ROLES = [
  "ALL",
  "WICKET_KEEPER",
  "BATTER",
  "ALL_ROUNDER",
  "BOWLER",
];

const ROLE_LABELS = {
  WICKET_KEEPER: "WK",
  BATTER: "BAT",
  ALL_ROUNDER: "AR",
  BOWLER: "BOWL",
};

const ROLE_RULES = {
  WICKET_KEEPER: 1,
  BATTER: 3,
  ALL_ROUNDER: 1,
  BOWLER: 3,
};

function toNumber(value, fallback = 0) {
  const n = Number(value);
  return Number.isFinite(n) ? n : fallback;
}

function normalizeRole(value) {
  const role = String(value || "")
    .toUpperCase()
    .replace(/[-\s]/g, "_");

  if (
    role.includes("WICKET") ||
    role === "WK" ||
    role.includes("KEEPER")
  ) {
    return "WICKET_KEEPER";
  }

  if (role.includes("ALL")) return "ALL_ROUNDER";
  if (role.includes("BOWL")) return "BOWLER";
  if (role.includes("BAT")) return "BATTER";

  return "BATTER";
}

function getCondition(player) {
  const text = [
    player?.condition,
    player?.fitness,
    player?.availability_status,
    player?.availability,
    player?.status,
    player?.injury_status,
  ]
    .filter(Boolean)
    .join(" ")
    .toLowerCase();

  if (
    player?.injured === true ||
    player?.is_injured === true ||
    player?.injury === true ||
    text.includes("injured") ||
    text.includes("injury")
  ) {
    return "INJURED";
  }

  if (
    player?.available === false ||
    player?.is_available === false ||
    text.includes("unavailable") ||
    text.includes("out")
  ) {
    return "UNAVAILABLE";
  }

  if (text.includes("doubt")) {
    return "DOUBTFUL";
  }

  if (
    player?.available === true ||
    player?.is_available === true ||
    text.includes("fit") ||
    text.includes("available")
  ) {
    return "FIT";
  }

  return "UNKNOWN";
}

function normalizePlayer(player, index = 0) {
  return {
    ...player,

    id: String(
      player?.id ||
        player?.player_id ||
        player?.name ||
        `player-${index}`
    ),

    name:
      player?.name ||
      player?.player_name ||
      player?.full_name ||
      `Player ${index + 1}`,

    realTeam:
      player?.real_team ||
      player?.team ||
      player?.team_name ||
      "Unknown Team",

    role: normalizeRole(player?.role),

    credits: toNumber(
      player?.credits ??
        player?.cost ??
        player?.price ??
        player?.fantasy_credits,
      0
    ),

    projected: toNumber(
      player?.projected_points ??
        player?.projectedPoints ??
        player?.fantasy_avg ??
        player?.avg_points ??
        player?.fantasy_average,
      0
    ),

    ceiling: toNumber(
      player?.fantasy_ceiling ??
        player?.ceiling ??
        player?.max_points,
      0
    ),

    condition: getCondition(player),
  };
}

function deepFind(object, keys, seen = new WeakSet()) {
  if (!object || typeof object !== "object") {
    return null;
  }

  if (seen.has(object)) {
    return null;
  }

  seen.add(object);

  if (Array.isArray(object)) {
    for (const item of object) {
      const result = deepFind(item, keys, seen);

      if (result !== null) {
        return result;
      }
    }

    return null;
  }

  for (const key of keys) {
    if (Object.prototype.hasOwnProperty.call(object, key)) {
      return object[key];
    }
  }

  for (const value of Object.values(object)) {
    const result = deepFind(value, keys, seen);

    if (result !== null) {
      return result;
    }
  }

  return null;
}

function extractTeam(data) {
  const candidates = [
    data?.engine_result?.team,
    data?.engine_result?.current_team,
    data?.engine_result?.selected_team,
    data?.team,
    data?.current_team,
    data?.selected_team,
  ];

  for (const candidate of candidates) {
    if (Array.isArray(candidate)) {
      return candidate.map(normalizePlayer);
    }

    if (
      candidate?.players &&
      Array.isArray(candidate.players)
    ) {
      return candidate.players.map(normalizePlayer);
    }
  }

  return [];
}

function extractPlayerPool(data) {
  const candidates = [
    data?.engine_result?.players,
    data?.engine_result?.player_pool,
    data?.engine_result?.available_players,
    data?.players,
    data?.player_pool,
    data?.available_players,
  ];

  for (const candidate of candidates) {
    if (Array.isArray(candidate)) {
      return candidate.map(normalizePlayer);
    }
  }

  return [];
}

function extractMessage(data) {
  return (
    data?.message ||
    data?.response ||
    data?.engine_result?.message ||
    data?.engine_result?.explanation ||
    "Backend operation completed."
  );
}

function extractWeather(data) {
  return deepFind(data, [
    "weather",
    "weather_condition",
    "weather_data",
  ]);
}

function extractPitch(data) {
  return deepFind(data, [
    "pitch",
    "pitch_condition",
    "pitch_data",
  ]);
}

function extractSimulation(data) {
  return deepFind(data, [
    "simulation",
    "simulator",
    "simulation_result",
  ]);
}

function displayObject(value, fallback) {
  if (!value) return fallback;

  if (typeof value === "string") {
    return value;
  }

  return (
    value?.summary ||
    value?.description ||
    value?.condition ||
    value?.type ||
    value?.status ||
    fallback
  );
}

function conditionBadge(condition) {
  if (condition === "FIT") {
    return <span className="condition fit">● FIT</span>;
  }

  if (condition === "INJURED") {
    return (
      <span className="condition injured">
        ● INJURED
      </span>
    );
  }

  if (condition === "UNAVAILABLE") {
    return (
      <span className="condition injured">
        ● UNAVAILABLE
      </span>
    );
  }

  if (condition === "DOUBTFUL") {
    return (
      <span className="condition doubtful">
        ● DOUBTFUL
      </span>
    );
  }

  return (
    <span className="condition unknown">
      ● UNKNOWN
    </span>
  );
}

function App() {
  const [players, setPlayers] = useState([]);
  const [selected, setSelected] = useState([]);

  const [roleFilter, setRoleFilter] = useState("ALL");

  const [captain, setCaptain] = useState("");
  const [viceCaptain, setViceCaptain] = useState("");

  const [loading, setLoading] = useState(false);
  const [operation, setOperation] = useState("READY");

  const [messages, setMessages] = useState([
    {
      type: "ai",
      text:
        "CricPilot AI Core online. Sync your player data, manually build your XI, or let the autonomous optimizer create the strongest valid team.",
    },
  ]);

  const [backendMessage, setBackendMessage] =
    useState("");

  const [weather, setWeather] = useState(null);
  const [pitch, setPitch] = useState(null);
  const [simulation, setSimulation] = useState(null);

  const [chatInput, setChatInput] = useState("");

  const totalCredits = useMemo(() => {
    return selected.reduce(
      (sum, player) => sum + player.credits,
      0
    );
  }, [selected]);

  const remainingCredits = BUDGET - totalCredits;

  const projectedPoints = useMemo(() => {
    return selected.reduce(
      (sum, player) => sum + player.projected,
      0
    );
  }, [selected]);

  const roleCounts = useMemo(() => {
    const counts = {
      WICKET_KEEPER: 0,
      BATTER: 0,
      ALL_ROUNDER: 0,
      BOWLER: 0,
    };

    selected.forEach((player) => {
      counts[player.role] =
        (counts[player.role] || 0) + 1;
    });

    return counts;
  }, [selected]);

  const teamValid =
    selected.length === 11 &&
    totalCredits <= BUDGET &&
    Object.entries(ROLE_RULES).every(
      ([role, minimum]) =>
        roleCounts[role] >= minimum
    );

  const filteredPlayers =
    roleFilter === "ALL"
      ? players
      : players.filter(
          (player) => player.role === roleFilter
        );

  const selectedIds = new Set(
    selected.map((player) => player.id)
  );

  const injuredCount = selected.filter(
    (player) => player.condition === "INJURED"
  ).length;

  const doubtfulCount = selected.filter(
    (player) => player.condition === "DOUBTFUL"
  ).length;

  const fitCount = selected.filter(
    (player) => player.condition === "FIT"
  ).length;

  function scrollToSection(id) {
    document
      .getElementById(id)
      ?.scrollIntoView({
        behavior: "smooth",
        block: "start",
      });
  }

  function scrollTop() {
    window.scrollTo({
      top: 0,
      behavior: "smooth",
    });
  }

  async function callBackend(
    command,
    operationName
  ) {
    setLoading(true);
    setOperation(operationName);

    try {
      const response = await fetch(
        `${API}/api/agent/chat`,
        {
          method: "POST",
          headers: {
            "Content-Type": "application/json",
          },
          body: JSON.stringify({
            message: command,
          }),
        }
      );

      const data = await response.json();

      if (!response.ok) {
        throw new Error(
          data?.detail ||
            data?.message ||
            `Backend returned ${response.status}`
        );
      }

      const team = extractTeam(data);
      const pool = extractPlayerPool(data);

      const weatherData = extractWeather(data);
      const pitchData = extractPitch(data);
      const simulationData =
        extractSimulation(data);

      if (team.length > 0) {
        setSelected(team);

        setPlayers((current) => {
          const map = new Map(
            current.map((player) => [
              player.id,
              player,
            ])
          );

          team.forEach((player) => {
            map.set(player.id, player);
          });

          return Array.from(map.values());
        });
      }

      if (pool.length > 0) {
        setPlayers((current) => {
          const map = new Map(
            current.map((player) => [
              player.id,
              player,
            ])
          );

          pool.forEach((player) => {
            const oldPlayer = map.get(player.id);

            map.set(
              player.id,
              oldPlayer
                ? {
                    ...oldPlayer,
                    ...player,
                  }
                : player
            );
          });

          return Array.from(map.values());
        });
      }

      if (weatherData) {
        setWeather(weatherData);
      }

      if (pitchData) {
        setPitch(pitchData);
      }

      if (simulationData) {
        setSimulation(simulationData);
      }

      const message = extractMessage(data);

      setBackendMessage(message);

      setMessages((current) => [
        ...current,
        {
          type: "ai",
          text: message,
        },
      ]);

      return data;
    } catch (error) {
      setBackendMessage(error.message);

      setMessages((current) => [
        ...current,
        {
          type: "error",
          text: `Backend error: ${error.message}`,
        },
      ]);
    } finally {
      setLoading(false);
      setOperation("READY");
    }
  }

  async function syncIntelligence() {
    await callBackend(
      "Report current fantasy cricket intelligence using the existing backend tools. Return the player pool with each player's name, role, real team, credits, projected fantasy points, and exact availability, fitness or injury condition where known. Also return current weather and pitch condition. Do not invent unknown values.",
      "SYNCING DATA"
    );
  }

  async function buildBestXI() {
    await callBackend(
      "Build the best fantasy cricket XI using the existing backend optimizer. Use maximum budget 100 credits and exactly 11 players. Respect real fantasy cricket role constraints: at least 1 wicket-keeper, 3 batters, 1 all-rounder and 3 bowlers, while respecting maximum 7 players from one real team. Exclude injured or unavailable players when known. Return selected players with credits, projected fantasy points, roles, availability, captain and vice-captain.",
      "BUILDING XI"
    );
  }

  async function simulateTeam() {
    if (selected.length !== 11) {
      addSystemMessage(
        "Simulation requires exactly 11 players."
      );
      return;
    }

    await callBackend(
      "Run the existing fantasy scoring simulator on my current selected XI. Evaluate projected fantasy points, captain and vice-captain impact, scoring potential and team strength. Do not modify my selected XI.",
      "RUNNING SIMULATOR"
    );
  }

  async function analyzeTeam() {
    if (selected.length === 0) {
      addSystemMessage(
        "Add players before requesting a team analysis."
      );
      return;
    }

    await callBackend(
      "Analyze my current fantasy XI using the existing backend. Evaluate credits used, remaining credits, projected points, role balance, player availability and injury status, risk, captain, vice-captain and overall team quality.",
      "ANALYZING TEAM"
    );
  }

  async function autonomousAdapt() {
    await callBackend(
      "Autonomously monitor my current fantasy XI using the existing availability, news, weather, optimizer, simulator and validator tools. Detect unavailable, injured or risky players and changing match context. If a change is needed, find the strongest valid replacement within the 100 credit budget and role constraints. Return the updated valid XI and explain every change.",
      "AUTONOMOUS CHECK"
    );
  }

  async function sendChat() {
    if (!chatInput.trim() || loading) return;

    const text = chatInput.trim();

    setMessages((current) => [
      ...current,
      {
        type: "user",
        text,
      },
    ]);

    setChatInput("");

    await callBackend(
      text,
      "AI PROCESSING"
    );
  }

  function addSystemMessage(text) {
    setMessages((current) => [
      ...current,
      {
        type: "error",
        text,
      },
    ]);
  }

  function addPlayer(player) {
    if (selected.length >= 11) {
      addSystemMessage(
        "Your fantasy XI already contains 11 players."
      );
      return;
    }

    if (
      player.condition === "INJURED" ||
      player.condition === "UNAVAILABLE"
    ) {
      addSystemMessage(
        `${player.name} cannot be selected because the backend marked this player ${player.condition}.`
      );
      return;
    }

    if (
      totalCredits + player.credits >
      BUDGET
    ) {
      addSystemMessage(
        `Not enough credits for ${player.name}. You need ${player.credits.toFixed(
          1
        )} credits.`
      );
      return;
    }

    setSelected((current) => [
      ...current,
      player,
    ]);
  }

  function removePlayer(id) {
    setSelected((current) =>
      current.filter((player) => player.id !== id)
    );

    if (captain === id) {
      setCaptain("");
    }

    if (viceCaptain === id) {
      setViceCaptain("");
    }
  }

  function togglePlayer(player) {
    if (selectedIds.has(player.id)) {
      removePlayer(player.id);
      return;
    }

    addPlayer(player);
  }

  return (
    <div className="app">
      <div className="grid-bg" />
      <div className="scanline" />

      {/* TOPBAR */}
      <header className="navbar">
        <button
          className="brand nav-brand"
          onClick={scrollTop}
        >
          <div className="brand-mark">
            CP
          </div>

          <div>
            <strong>CRICPILOT</strong>
            <span>
              AI FANTASY COMMAND CENTER
            </span>
          </div>
        </button>

        <nav className="top-navigation">
          <button onClick={scrollTop}>
            OVERVIEW
          </button>

          <button
            onClick={() =>
              scrollToSection("intelligence")
            }
          >
            MATCH INTELLIGENCE
          </button>

          <button
            onClick={() =>
              scrollToSection("team-builder")
            }
          >
            TEAM BUILDER
          </button>

          <button
            onClick={() =>
              scrollToSection("copilot")
            }
          >
            AI COPILOT
          </button>

          <button
            onClick={() =>
              scrollToSection("autonomous")
            }
          >
            AUTONOMOUS
          </button>
        </nav>

        <button
          className="nav-button"
          onClick={syncIntelligence}
          disabled={loading}
        >
          {loading ? "SYNCING..." : "SYNC DATA"}
        </button>
      </header>

      <main className="container">
        {/* HERO */}
        <section
          id="overview"
          className="hero"
        >
          <div className="hero-copy">
            <div className="eyebrow">
              AUTONOMOUS FANTASY SPORTS MANAGER
            </div>

            <h1>
              Build your XI.
              <br />
              <span>
                Let intelligence play.
              </span>
            </h1>

            <p>
              Build your own fantasy cricket XI
              using credits, real playing roles,
              player availability, projected
              points and match conditions — or
              let CricPilot autonomously optimize
              everything.
            </p>

            <div className="hero-buttons">
              <button
                className="primary-button"
                onClick={buildBestXI}
                disabled={loading}
              >
                ⚡ BUILD BEST XI
              </button>

              <button
                className="secondary-button"
                onClick={syncIntelligence}
                disabled={loading}
              >
                ◉ SYNC MATCH DATA
              </button>

              <button
                className="secondary-button"
                onClick={() =>
                  scrollToSection("team-builder")
                }
              >
                ↓ BUILD MANUALLY
              </button>
            </div>
          </div>

          <div className="core">
            <div className="core-ring ring-one" />
            <div className="core-ring ring-two" />

            <div className="core-center">
              <span>AI</span>
              <strong>CORE</strong>
              <small>{operation}</small>
            </div>
          </div>
        </section>

        {/* STATS */}
        <section className="dashboard-grid">
          <div className="stat-card">
            <span>XI SIZE</span>
            <strong>{selected.length}/11</strong>
            <small>
              players selected
            </small>
          </div>

          <div className="stat-card">
            <span>CREDITS USED</span>
            <strong>
              {totalCredits.toFixed(1)}
            </strong>
            <small>
              of {BUDGET}
            </small>
          </div>

          <div className="stat-card">
            <span>REMAINING</span>
            <strong
              className={
                remainingCredits < 0
                  ? "danger-text"
                  : ""
              }
            >
              {remainingCredits.toFixed(1)}
            </strong>
            <small>credits</small>
          </div>

          <div className="stat-card">
            <span>PROJECTED PTS</span>
            <strong>
              {projectedPoints.toFixed(1)}
            </strong>
            <small>
              current XI
            </small>
          </div>

          <div className="stat-card">
            <span>VALIDATION</span>
            <strong
              className={
                teamValid
                  ? "green-text"
                  : "yellow-text"
              }
            >
              {teamValid
                ? "VALID"
                : "INCOMPLETE"}
            </strong>
            <small>
              fantasy constraints
            </small>
          </div>
        </section>

        {/* INTELLIGENCE */}
        <section
          id="intelligence"
          className="intelligence-grid"
        >
          <div className="panel intelligence-panel">
            <div className="panel-header">
              <div>
                <span className="section-label">
                  LIVE MATCH DATA
                </span>
                <h2>
                  Match Intelligence
                </h2>
              </div>

              <span className="status-badge">
                AI MONITORED
              </span>
            </div>

            <div className="condition-grid">
              <div className="condition-card">
                <span>WEATHER</span>

                <strong>
                  {displayObject(
                    weather,
                    "Awaiting backend"
                  )}
                </strong>

                {weather &&
                  typeof weather ===
                    "object" && (
                    <div className="condition-details">
                      {weather.temperature_c !=
                        null && (
                        <span>
                          {
                            weather.temperature_c
                          }
                          °C
                        </span>
                      )}

                      {weather.temperature !=
                        null && (
                        <span>
                          {
                            weather.temperature
                          }
                          °
                        </span>
                      )}

                      {weather.rain_probability !=
                        null && (
                        <span>
                          Rain{" "}
                          {
                            weather.rain_probability
                          }
                          %
                        </span>
                      )}

                      {weather.wind_kph !=
                        null && (
                        <span>
                          Wind{" "}
                          {weather.wind_kph} km/h
                        </span>
                      )}
                    </div>
                  )}
              </div>

              <div className="condition-card">
                <span>PITCH</span>

                <strong>
                  {displayObject(
                    pitch,
                    "Awaiting backend"
                  )}
                </strong>

                {pitch &&
                  typeof pitch ===
                    "object" && (
                    <div className="condition-details">
                      {pitch.type && (
                        <span>
                          {pitch.type}
                        </span>
                      )}

                      {pitch.surface && (
                        <span>
                          {pitch.surface}
                        </span>
                      )}

                      {pitch.pace && (
                        <span>
                          Pace: {pitch.pace}
                        </span>
                      )}

                      {pitch.spin && (
                        <span>
                          Spin: {pitch.spin}
                        </span>
                      )}
                    </div>
                  )}
              </div>

              <div className="condition-card">
                <span>
                  PLAYER CONDITION
                </span>

                <strong>
                  {injuredCount} injured
                </strong>

                <div className="condition-details">
                  <span>
                    {fitCount} fit
                  </span>

                  <span>
                    {doubtfulCount} doubtful
                  </span>
                </div>
              </div>

              <div className="condition-card">
                <span>
                  SCORING ENGINE
                </span>

                <strong>
                  {simulation
                    ? displayObject(
                        simulation,
                        "Complete"
                      )
                    : "Not simulated"}
                </strong>

                <button
                  className="mini-button"
                  onClick={simulateTeam}
                  disabled={
                    loading ||
                    selected.length !== 11
                  }
                >
                  RUN SIMULATOR
                </button>
              </div>
            </div>
          </div>
        </section>

        {/* BUILDER */}
        <section
          id="team-builder"
          className="builder-layout"
        >
          {/* PLAYER DATABASE */}
          <div className="panel player-pool">
            <div className="panel-header">
              <div>
                <span className="section-label">
                  PLAYER DATABASE
                </span>

                <h2>
                  Choose Your Players
                </h2>
              </div>

              <span className="pool-count">
                {players.length} PLAYERS
              </span>
            </div>

            <div className="role-tabs">
              {ROLES.map((role) => (
                <button
                  key={role}
                  className={
                    roleFilter === role
                      ? "active"
                      : ""
                  }
                  onClick={() =>
                    setRoleFilter(role)
                  }
                >
                  {role === "ALL"
                    ? "ALL"
                    : ROLE_LABELS[role]}
                </button>
              ))}
            </div>

            {players.length === 0 ? (
              <div className="empty-state">
                <div className="empty-icon">
                  ◉
                </div>

                <h3>
                  Player pool not loaded
                </h3>

                <p>
                  Sync the existing backend
                  intelligence engine to load
                  player roles, credits,
                  projected points and
                  availability.
                </p>

                <button
                  className="primary-button"
                  onClick={syncIntelligence}
                  disabled={loading}
                >
                  LOAD PLAYERS
                </button>
              </div>
            ) : (
              <div className="player-grid">
                {filteredPlayers.map(
                  (player) => {
                    const isSelected =
                      selectedIds.has(
                        player.id
                      );

                    const blocked =
                      player.condition ===
                        "INJURED" ||
                      player.condition ===
                        "UNAVAILABLE";

                    return (
                      <div
                        className={`player-card ${
                          isSelected
                            ? "selected-player"
                            : ""
                        } ${
                          blocked
                            ? "blocked-player"
                            : ""
                        }`}
                        key={player.id}
                      >
                        <div className="player-top">
                          <div className="player-avatar">
                            {player.name
                              .charAt(0)
                              .toUpperCase()}
                          </div>

                          <div className="player-name">
                            <strong>
                              {player.name}
                            </strong>

                            <span>
                              {player.realTeam}
                            </span>
                          </div>

                          <span className="role-badge">
                            {
                              ROLE_LABELS[
                                player.role
                              ]
                            }
                          </span>
                        </div>

                        <div className="player-condition">
                          {conditionBadge(
                            player.condition
                          )}
                        </div>

                        <div className="player-stats">
                          <div>
                            <span>
                              CREDITS
                            </span>

                            <strong>
                              {player.credits.toFixed(
                                1
                              )}
                            </strong>
                          </div>

                          <div>
                            <span>
                              PROJECTED
                            </span>

                            <strong>
                              {player.projected.toFixed(
                                1
                              )}
                            </strong>
                          </div>

                          <div>
                            <span>
                              CEILING
                            </span>

                            <strong>
                              {player.ceiling
                                ? player.ceiling.toFixed(
                                    1
                                  )
                                : "—"}
                            </strong>
                          </div>
                        </div>

                        <button
                          className={
                            isSelected
                              ? "remove-player"
                              : "add-player"
                          }
                          onClick={() =>
                            togglePlayer(player)
                          }
                          disabled={
                            blocked &&
                            !isSelected
                          }
                        >
                          {isSelected
                            ? "✓ SELECTED"
                            : blocked
                            ? "UNAVAILABLE"
                            : "+ ADD TO XI"}
                        </button>
                      </div>
                    );
                  }
                )}
              </div>
            )}
          </div>

          {/* TEAM */}
          <aside className="panel team-panel">
            <div className="panel-header">
              <div>
                <span className="section-label">
                  YOUR SQUAD
                </span>

                <h2>
                  Fantasy XI
                </h2>
              </div>

              <span
                className={
                  teamValid
                    ? "valid-badge"
                    : "warning-badge"
                }
              >
                {teamValid
                  ? "VALID XI"
                  : `${selected.length}/11`}
              </span>
            </div>

            <div className="credit-bar">
              <div className="credit-info">
                <span>
                  CREDITS
                </span>

                <strong>
                  {totalCredits.toFixed(1)}
                  {" / "}
                  {BUDGET}
                </strong>
              </div>

              <div className="bar">
                <div
                  style={{
                    width: `${Math.min(
                      100,
                      Math.max(
                        0,
                        (totalCredits /
                          BUDGET) *
                          100
                      )
                    )}%`,
                  }}
                />
              </div>

              <small>
                {remainingCredits.toFixed(1)}
                {" credits remaining"}
              </small>
            </div>

            <div className="role-checks">
              {Object.entries(
                ROLE_RULES
              ).map(
                ([role, minimum]) => (
                  <div
                    key={role}
                    className={
                      roleCounts[role] >=
                      minimum
                        ? "role-check complete"
                        : "role-check"
                    }
                  >
                    <span>
                      {ROLE_LABELS[role]}
                    </span>

                    <strong>
                      {roleCounts[role]}/
                      {minimum}+
                    </strong>
                  </div>
                )
              )}
            </div>

            <div className="selected-list">
              {selected.length === 0 ? (
                <div className="selected-empty">
                  Your XI is empty.
                  <br />
                  Select players from the
                  database.
                </div>
              ) : (
                selected.map(
                  (player, index) => (
                    <div
                      className="selected-row"
                      key={player.id}
                    >
                      <span className="player-number">
                        {String(
                          index + 1
                        ).padStart(2, "0")}
                      </span>

                      <div className="selected-name">
                        <strong>
                          {player.name}
                        </strong>

                        <span>
                          {
                            ROLE_LABELS[
                              player.role
                            ]
                          }{" "}
                          ·{" "}
                          {player.realTeam}
                        </span>
                      </div>

                      <div className="selected-points">
                        <strong>
                          {player.projected.toFixed(
                            1
                          )}
                        </strong>

                        <span>
                          PTS
                        </span>
                      </div>

                      <div className="selected-credit">
                        {player.credits.toFixed(
                          1
                        )}
                      </div>

                      <button
                        className="x-button"
                        onClick={() =>
                          removePlayer(
                            player.id
                          )
                        }
                      >
                        ×
                      </button>
                    </div>
                  )
                )
              )}
            </div>

            <div className="captain-section">
              <div>
                <label>
                  CAPTAIN
                </label>

                <select
                  value={captain}
                  onChange={(event) => {
                    const value =
                      event.target.value;

                    setCaptain(value);

                    if (
                      value ===
                      viceCaptain
                    ) {
                      setViceCaptain("");
                    }
                  }}
                >
                  <option value="">
                    Select Captain
                  </option>

                  {selected.map(
                    (player) => (
                      <option
                        key={player.id}
                        value={player.id}
                      >
                        {player.name}
                      </option>
                    )
                  )}
                </select>
              </div>

              <div>
                <label>
                  VICE CAPTAIN
                </label>

                <select
                  value={viceCaptain}
                  onChange={(event) => {
                    const value =
                      event.target.value;

                    if (
                      value === captain
                    ) {
                      return;
                    }

                    setViceCaptain(value);
                  }}
                >
                  <option value="">
                    Select Vice Captain
                  </option>

                  {selected.map(
                    (player) => (
                      <option
                        key={player.id}
                        value={player.id}
                      >
                        {player.name}
                      </option>
                    )
                  )}
                </select>
              </div>
            </div>

            <button
              className="simulate-button"
              onClick={simulateTeam}
              disabled={
                loading ||
                selected.length !== 11
              }
            >
              ◈ SIMULATE THIS XI
            </button>

            <button
              className="analyze-button"
              onClick={analyzeTeam}
              disabled={
                loading ||
                selected.length === 0
              }
            >
              ANALYZE TEAM WITH AI
            </button>
          </aside>
        </section>

        {/* ROLE BALANCE + COPILOT */}
        <section className="lower-grid">
          <div className="panel role-panel">
            <div className="panel-header">
              <div>
                <span className="section-label">
                  REAL GAME ROLES
                </span>

                <h2>
                  Role Balance
                </h2>
              </div>
            </div>

            <div className="role-bars">
              {Object.entries(
                roleCounts
              ).map(
                ([role, count]) => (
                  <div
                    className="role-bar-row"
                    key={role}
                  >
                    <div className="role-bar-title">
                      <span>
                        {
                          ROLE_LABELS[
                            role
                          ]
                        }
                      </span>

                      <strong>
                        {count}
                      </strong>
                    </div>

                    <div className="role-track">
                      <div
                        style={{
                          width: `${Math.min(
                            100,
                            count * 20
                          )}%`,
                        }}
                      />
                    </div>
                  </div>
                )
              )}
            </div>

            <div className="role-rule-box">
              <span>
                FANTASY RULES
              </span>

              <p>
                1+ WK · 3+ BAT · 1+ AR ·
                3+ BOWL · 11 TOTAL · ≤100
                CREDITS
              </p>
            </div>
          </div>

          <div
            id="copilot"
            className="panel ai-panel"
          >
            <div className="panel-header">
              <div>
                <span className="section-label">
                  AGENT OUTPUT
                </span>

                <h2>
                  AI Copilot
                </h2>
              </div>

              <span className="ai-online">
                ● ONLINE
              </span>
            </div>

            <div className="chat-messages">
              {messages
                .slice(-7)
                .map(
                  (
                    message,
                    index
                  ) => (
                    <div
                      className={`chat-message ${message.type}`}
                      key={index}
                    >
                      <span>
                        {message.type ===
                        "user"
                          ? "YOU"
                          : message.type ===
                            "error"
                          ? "SYSTEM"
                          : "AI CORE"}
                      </span>

                      <p>
                        {message.text}
                      </p>
                    </div>
                  )
                )}
            </div>

            <div className="quick-actions">
              <button
                onClick={() =>
                  setChatInput(
                    "Which players are injured, unavailable or doubtful?"
                  )
                }
              >
                INJURY REPORT
              </button>

              <button
                onClick={() =>
                  setChatInput(
                    "Analyze the current pitch and weather impact."
                  )
                }
              >
                PITCH + WEATHER
              </button>

              <button
                onClick={() =>
                  setChatInput(
                    "Find the strongest XI under 100 credits."
                  )
                }
              >
                OPTIMIZE XI
              </button>

              <button
                onClick={() =>
                  setChatInput(
                    "Check my team for availability and selection risks."
                  )
                }
              >
                RISK CHECK
              </button>
            </div>

            <div className="chat-input">
              <input
                value={chatInput}
                onChange={(event) =>
                  setChatInput(
                    event.target.value
                  )
                }
                onKeyDown={(event) => {
                  if (
                    event.key ===
                    "Enter"
                  ) {
                    sendChat();
                  }
                }}
                placeholder="Ask CricPilot anything..."
              />

              <button
                onClick={sendChat}
                disabled={
                  loading ||
                  !chatInput.trim()
                }
              >
                SEND →
              </button>
            </div>
          </div>
        </section>

        {/* AUTONOMOUS */}
        <section
          id="autonomous"
          className="autonomous-panel"
        >
          <div>
            <span className="section-label">
              AUTONOMOUS DECISION LOOP
            </span>

            <h2>
              CRICPILOT ENGINE
            </h2>
          </div>

          <div className="pipeline">
            <span>
              PLAYER DATA
            </span>

            <i>→</i>

            <span>
              AVAILABILITY
            </span>

            <i>→</i>

            <span>
              WEATHER
            </span>

            <i>→</i>

            <span>
              PITCH
            </span>

            <i>→</i>

            <span>
              OPTIMIZER
            </span>

            <i>→</i>

            <span>
              SIMULATOR
            </span>

            <i>→</i>

            <span>
              VALIDATOR
            </span>

            <i>→</i>

            <span>
              ADAPT
            </span>
          </div>

          <button
            className="autonomous-button"
            onClick={autonomousAdapt}
            disabled={loading}
          >
            {loading
              ? "MONITORING..."
              : "START AUTONOMOUS CHECK"}
          </button>
        </section>

        {/* BACKEND RESPONSE */}
        {backendMessage && (
          <section className="backend-result">
            <span>
              LAST AI ENGINE RESPONSE
            </span>

            <p>
              {backendMessage}
            </p>
          </section>
        )}

        <footer>
          <span>CRICPILOT</span>
          <span>
            AI OPTIMIZATION
          </span>
          <span>
            CREDIT CONSTRAINTS
          </span>
          <span>
            PLAYER AVAILABILITY
          </span>
          <span>
            FANTASY SIMULATION
          </span>
          <span>
            AUTONOMOUS ADAPTATION
          </span>
        </footer>
      </main>
    </div>
  );
}

export default App;