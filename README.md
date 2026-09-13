# 🏏 CricPilot

### Autonomous AI-Powered Fantasy Cricket Manager

CricPilot is an autonomous fantasy-cricket management platform that uses AI, player statistics, match conditions, availability data, weather intelligence, and a scoring simulator to build and continuously optimize a fantasy XI.

Unlike a basic fantasy team generator, CricPilot is designed to **observe → plan → optimize → validate → simulate → monitor → adapt**.

---

## 🚀 Key Features

### 🤖 Autonomous Team Management
- Interprets the user's fantasy objective and preferences
- Automatically builds the best possible Fantasy XI
- Respects budget and squad constraints
- Maintains role balance across the squad
- Automatically adapts when match conditions or player availability changes

### 🏥 Player Availability & Fitness
Tracks player status such as:
- Fit
- Injured
- Doubtful
- Unavailable

Unavailable or risky players can be identified before team selection.

### 🌦️ Match Intelligence
CricPilot considers:
- Weather conditions
- Pitch conditions
- Player availability
- Match context
- Player form and statistics

### 💰 Smart Budget Optimization
The optimizer builds teams within the fantasy budget while attempting to maximize projected performance.

Default constraints include:

- **Budget:** 100 credits
- **Squad Size:** 11 players
- **Wicket Keepers:** Minimum 1
- **Batters:** Minimum 3
- **All-Rounders:** Minimum 1
- **Bowlers:** Minimum 3
- **Maximum players from one real team:** 7

### 📊 Fantasy Scoring Simulator
Teams can be evaluated using a scoring simulator to estimate fantasy performance and compare candidate squads.

### 👑 Captain & Vice-Captain
CricPilot selects or allows selection of:
- Captain
- Vice-Captain

These choices are considered during team evaluation.

### 🔄 Autonomous Adaptation
The system continuously monitors changing conditions.

If a selected player becomes unavailable, CricPilot can:

1. Detect the change
2. Find replacement candidates
3. Validate the replacement
4. Update the fantasy team
5. Recalculate the team
6. Verify the final squad

---

# 🧠 Autonomous Workflow

```text
                 USER OBJECTIVE
                       │
                       ▼
                ┌──────────────┐
                │   OBSERVE    │
                │ Match + Data │
                └──────┬───────┘
                       │
                       ▼
                ┌──────────────┐
                │    PLAN      │
                │ AI Strategy  │
                └──────┬───────┘
                       │
                       ▼
                ┌──────────────┐
                │   OPTIMIZE   │
                │ Generate XI  │
                └──────┬───────┘
                       │
                       ▼
                ┌──────────────┐
                │   VALIDATE   │
                │ Constraints  │
                └──────┬───────┘
                       │
                       ▼
                ┌──────────────┐
                │   SIMULATE   │
                │ Score Team   │
                └──────┬───────┘
                       │
                       ▼
                ┌──────────────┐
                │    MONITOR   │
                │ Live Changes │
                └──────┬───────┘
                       │
                 Change detected?
                    /       \
                  YES        NO
                   │          │
                   ▼          │
              ┌─────────┐     │
              │ ADAPT   │─────┘
              │ & REBUILD
              └─────────┘