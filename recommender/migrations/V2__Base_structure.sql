-- Trigrams used for fuzzy searching
CREATE EXTENSION pg_trgm;

CREATE TABLE IF NOT EXISTS data.file_storage_base (
    id TEXT,
    name TEXT UNIQUE,
    storage_base TEXT      -- Either local folder, or URL, or whatever. Should we use a storage base class?
);

CREATE TABLE IF NOT EXISTS data.file_storage (
    id TEXT,
    display_filename TEXT,  -- Maybe it will always just be "poster" or "backdrop", will just be sued in html for alt links.
    storage_base TEXT,      -- ID of the storage base class, enables also credentions
    storage_filename TEXT   --
);

CREATE TABLE IF NOT EXISTS data.movie_infos (
    id int primary key,
    tmdb_id int,
    title TEXT not null,
    description TEXT,
    release_date DATE, -- proper dataatype here?
    duration INT,
    mpaa TEXT,
    poster TEXT, -- Will reference a file_storage object
    backdrop TEXT, -- Will reference a file_storage object
    recommendations JSONB, -- e.g. soemthing like: { [{ label: "tmdb", recommended: [99, 1, 4, 5, 6] }] }
    trailer_url TEXT,
    actors JSONB, -- Here will most probably be the normal input from tmdb
    genres JSONB, -- also here directly form tmd
    ratings JSONB -- so that we can have arbitrary ratings
);
