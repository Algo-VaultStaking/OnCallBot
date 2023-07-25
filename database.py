import configparser
import mariadb


c = configparser.ConfigParser()
c.read("config.ini", encoding='utf-8')

DB_USER = str(c["DATABASE"]["user"])
DB_PASSWORD = str(c["DATABASE"]["password"])
DB_HOST = str(c["DATABASE"]["host"])
DB_NAME = str(c["DATABASE"]["name"])


# Connect to MariaDB Platform
def get_db_connection():
    try:
        conn = mariadb.connect(
            user=DB_USER,
            password=DB_PASSWORD,
            host=DB_HOST,
            port=3306,
            database=DB_NAME
        )

        return conn

    except mariadb.Error as e:
        print(f"Error connecting to MariaDB Platform: {e}")
        exit()


def initial_setup():
    try:
        conn = get_db_connection()
        cur = conn.cursor()
        cur.execute("DROP TABLE call_schedule;")

        cur.execute("CREATE TABLE call_schedule("
                    "schedule_id INT, "
                    "calendar_id VARCHAR(30), "
                    "user VARCHAR(250), "
                    "start VARCHAR(30), "
                    "end VARCHAR(30), "
                    "guild BIGINT);")

        #cur.execute("DROP TABLE guild_info;")

        #cur.execute("CREATE TABLE guild_info("
        #            "guild BIGINT, "
        #            "on_call_role BIGINT);")

        #cur.execute(f"INSERT INTO guild_info VALUES(837853470136467517, 1116012502879305749);")  # Vault Staking
        #cur.execute(f"INSERT INTO guild_info VALUES(454734546869551114, 0);")  # Connext Public
        #cur.execute(f"INSERT INTO guild_info VALUES(992549151134982234, 1120679303043092631);")  # Connext Private

        conn.commit()

        cur.close()
        conn.close()
    except mariadb.Error as e:
        print(f"Error: {e}")


def add_to_schedule(db_connection, calendar_id: str, user: str, start: str, end: str, guild: int):
    cur = db_connection.cursor()
    try:
        try:
            cur.execute(f"SELECT max(schedule_id) FROM call_schedule;")
            next_schedule_id: int = int(cur.fetchall()[0][0]) + 1
        except Exception as e:
            next_schedule_id = 0

        cur.execute(f"INSERT INTO call_schedule VALUES ({next_schedule_id}, \"{calendar_id}\", \"{user}\", \"{start}\", \"{end}\", {guild});")
        db_connection.commit()

        return True
    except Exception as e:
        print(e)
        return False


def get_from_schedule(db_connection, schedule_id: int, guild: int):
    cur = db_connection.cursor()
    try:
        cur.execute(f"SELECT * FROM call_schedule WHERE schedule_id={schedule_id} and guild={guild};")
        result = cur.fetchall()
        return result
    except Exception as e:
        print(e)
        return False


def remove_from_schedule(db_connection, schedule_id: int, guild: int):
    cur = db_connection.cursor()
    try:
        cur.execute(f"DELETE FROM call_schedule WHERE schedule_id={schedule_id} and guild={guild};")
        db_connection.commit()
        return True
    except Exception as e:
        print(e)
        return False


def list_schedule(db_connection, guild: int):
    cur = db_connection.cursor()
    try:
        cur.execute(f"SELECT schedule_id, day_of_week, start, end, user FROM call_schedule WHERE guild={guild};")
        result = cur.fetchall()

        return result
    except Exception as e:
        print(e)
        return False


def get_schedule(db_connection, guild_id):
    cur = db_connection.cursor()
    try:
        cur.execute(f"SELECT start, end, user "
                    f"FROM call_schedule "
                    f"WHERE guild = {guild_id};")
        result = cur.fetchall()

        return result
    except Exception as e:
        print(e)
        return False


def get_on_call_role(db_connection, guild_id: int):
    cur = db_connection.cursor()

    try:
        command = f"SELECT on_call_role " \
                  f"FROM guild_info " \
                  f"WHERE guild = {guild_id};"
        cur.execute(command)
        return int(cur.fetchall()[0][0])

    except Exception as e:
        print(e)
        return False


def set_on_call_role(db_connection, guild_id: int, role_id):
    cur = db_connection.cursor()

    try:
        command = f"UPDATE guild_info " \
                  f"SET on_call_role = {role_id} " \
                  f"WHERE guild = {guild_id};"
        cur.execute(command)
        db_connection.commit()
        return True

    except Exception as e:
        print(e)
        return False


def clear_schedule(db_connection, guild):
    cur = db_connection.cursor()
    try:
        cur.execute(f"DELETE FROM call_schedule WHERE guild={guild};")
        db_connection.commit()

        return True
    except Exception as e:
        print(e)
        return False


def get_all_users_on_schedule(db_connection, guild: int):
    cur = db_connection.cursor()
    try:
        cur.execute(f"SELECT user FROM call_schedule WHERE guild={guild};")
        result = cur.fetchall()
        return result
    except Exception as e:
        print(e)
        return False


def get_all_calendar_ids(db_connection, guild: int):
    cur = db_connection.cursor()
    try:
        cur.execute(f"SELECT calendar_id FROM call_schedule WHERE guild={guild};")
        result = cur.fetchall()
        calendar_ids = []
        for calendar_id in result:
            calendar_ids.append(calendar_id[0])
        print(calendar_ids)
        return calendar_ids
    except Exception as e:
        print("get_all_calendar_ids error: ", e)
        return False