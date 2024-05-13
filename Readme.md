# Movie Recommender

We are building a movie recommender website. Everything is precalculated and then stored in a postgres database.

# Testing
Create a non=persistent postgres database running in docker **NOT AT ALL SAVE FOR ANYTHING BUT TESTING**
```shell
  docker run --name movie-databnase --rm -p 5432:5432 -e POSTGRES_PASSWORD=password -e POSTGRES_DB=movies_recommender postgres:16.3
```
