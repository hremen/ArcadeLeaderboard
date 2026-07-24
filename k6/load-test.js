import http from "k6/http";
import { check, sleep } from "k6";
import { randomIntBetween } from "https://jslib.k6.io/k6-utils/1.4.0/index.js";

const BASE_URL = __ENV.BASE_URL || "http://localhost:8000";

const GAMES = ["pacman", "tetris", "snake", "breakout", "donkeykong"];
const MAX_SCORES = {
  pacman: 999999,
  tetris: 9999999,
  snake: 99999,
  breakout: 896980,
  donkeykong: 1247700,
};

export const options = {
  stages: [
    { duration: "15s", target: 5 },
    { duration: "30s", target: 20 },
    { duration: "30s", target: 50 },
    { duration: "15s", target: 0 },
  ],
};

function randomPlayer() {
  const chars = "ABCDEFGHIJKLMNOPQRSTUVWXYZ";
  return (
    chars[randomIntBetween(0, 25)] +
    chars[randomIntBetween(0, 25)] +
    chars[randomIntBetween(0, 25)]
  );
}

export default function () {
  const game = GAMES[randomIntBetween(0, GAMES.length - 1)];

  const submitRes = http.post(
    `${BASE_URL}/scores`,
    JSON.stringify({
      player: randomPlayer(),
      game: game,
      score: randomIntBetween(1, MAX_SCORES[game]),
    }),
    { headers: { "Content-Type": "application/json" } }
  );
  check(submitRes, {
    "score submitted (201 or 429)": (r) => r.status === 201 || r.status === 429,
  });

  const lbRes = http.get(
    `${BASE_URL}/leaderboard/${game}?limit=10`
  );
  check(lbRes, {
    "leaderboard OK (200)": (r) => r.status === 200,
  });

  sleep(0.1);
}
