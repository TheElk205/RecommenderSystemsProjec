# Movie Recommender

We are building a movie recommender website. Everything is precalculated and then stored in a postgres database.

We are generating the data in jupyter, creating respective CSVs and then pushing them all into a postgres database.

# Preparations
Create a `.env` file in the main directory with the following content:
```shell
DB_HOST=10.0.0.185
DB_USER=postgres
DB_PASSWORD=password
```
Alternatively you can pass these env when starting the application.
These values will be injected into the `settings.py` of the django project, where they will be read from for migrations and data filling.


# Initiating the database
Start a postgres database, for docker see below.

where user and password should be a user that is present on the database and has rights to create schemas, tables and insert / read data.
Then go to `recommender/migrations/prepareDatabase.py` and execute it. This will generate the tables, extendsion and everything that is needed.
# Generating Data
For this go to `recommender/dataGenerator`. Here we have to extract the movie data set into a folder called `extracted_content_ml-latest`, can be found here: https://grouplens.org/datasets/movielens/20m/.
then execute the `fill_database.py`. Maybe adapt paths to pre generated data and such.

Now we have a full database up and running and we can simply start our application!

# Testing Databases
Create a non=persistent postgres database running in docker **NOT AT ALL SAVE FOR ANYTHING BUT TESTING**
```shell
docker run --name movie-database --rm -p 5432:5432 -e POSTGRES_PASSWORD=password -e POSTGRES_DB=movies_recommender postgres:16.3
```

Create postgres database with persistent storage. **TESTING ONLY**
```shell
mkdir -p ./postgres-data
docker run --name movie-database --rm -p 5432:5432 -e POSTGRES_PASSWORD=password -e POSTGRES_DB=movies_recommender -v ./postgres-data:/var/lib/postgresql/data postgres:16.3
```

