DROP TABLE IF EXISTS players;
DROP TABLE IF EXISTS rooms;

create TABLE players (
    id INTEGER PRIMARY KEY,
    alias TEXT NOT NULL,
    alive BOOLEAN NOT NULL DEFAULT TRUE,
    room_host INTEGER NOT NULL,
    info TEXT,
    item INTEGER,
    role INTEGER NOT NULL,
    FOREIGN KEY(room_host) REFERENCES room(host_id)
);

CREATE TABLE rooms (
    host_id INTEGER PRIMARY KEY
);

create TABLE IF NOT EXISTS users (
    id INTEGER PRIMARY KEY,
    room_host INTEGER,
    total_games INTEGER NOT NULL DEFAULT 0,
    wins INTEGER NOT NULL DEFAULT 0,
    xp: INTEGER NOT NULL DEFAULT 0,
    FOREIGN KEY(room_host) REFERENCES rooms(host_id)
);
