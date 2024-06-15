import os
import subprocess

from RecommenderSystemsFinalProject.settings import DATABASES

flyway_conf = '''flyway.url=jdbc:postgresql://{host}:{port}/{databasename}
flyway.user={user}
flyway.password={password}
flyway.defaultSchema={schema}
'''
flyway_config_file_path = "./flyway.conf"
flyway_docker_command = 'docker run --rm -v {working_dir}:/flyway/sql -v {working_dir}/flyway.conf:/flyway/conf/flyway.conf  flyway/flyway migrate'

if __name__ == '__main__':
    print("Executing migrations")
    print("Docker host: {}".format(DATABASES["default"]["HOST"]))
    flyway_config_command = flyway_conf.format(
        host=DATABASES["default"]["HOST"],
        port=5432,
        databasename="movies_recommender",
        user=DATABASES["default"]["USER"],
        password=DATABASES["default"]["PASSWORD"],
        schema="public"
    )
    with open(flyway_config_file_path, 'w') as file:
        file.write(flyway_config_command)
    command_string_command = flyway_docker_command.format(
        sqlfiles=".",
        working_dir="."
    )
    print(command_string_command)
    subprocess.run(command_string_command, shell=True)

    print("Deleting flyway conf, to not leave password behind")
    if os.path.isfile(flyway_config_file_path):
        os.remove(flyway_config_file_path)
