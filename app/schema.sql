CREATE TABLE IF NOT EXISTS lecturers (
    UUID TEXT UNIQUE NOT NULL,
    title_before TEXT,
    first_name TEXT,
    middle_name TEXT,
    last_name TEXT,
    title_after TEXT,
    picture_url TEXT,
    location TEXT,
    claim TEXT,
    bio TEXT,
    tags JSON DEFAULT('[]'),
    price_per_hour INTEGER
    emails JSON DEFAULT('[]'),
    phone_numbers JSON DEFAULT('[]'),
);
CREATE TABLE IF NOT EXISTS tags (
  UUID TEXT UNIQUE NOT NULL,
  name TEXT NOT NULL
);
