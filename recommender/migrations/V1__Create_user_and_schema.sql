CREATE USER movie_application WITH PASSWORD 'password';

GRANT CONNECT ON DATABASE movies_recommender TO movie_application;
CREATE SCHEMA IF NOT EXISTS data;
GRANT USAGE ON SCHEMA data to movie_application;
ALTER DEFAULT PRIVILEGES IN SCHEMA data GRANT SELECT on TABLES to movie_application;