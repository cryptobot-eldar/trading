import MySQLdb
import sys



def main():
    print('Starting api keys sync module')

    PS()


def PS():
    api_key=api_key_get()
    api_secret=api_secret_get()
    bot_mode = parameters()[23]

    print api_key, api_secret
    if bot_mode==1:

        with open('/usr/local/bin/config.py', 'w') as f:
            f.write("key = "+api_key)
            f.write("\n")
            f.close()

        with open('/usr/local/bin/config.py', 'a') as f:
            f.write("secret = "+api_secret)
            f.close()
    else:
        pass



def api_key_get():
    db = MySQLdb.connect("database-service", "cryptouser", "123456", "cryptodb")
    cursor = db.cursor()
    cursor.execute("SELECT api_key FROM parameters")
    r = cursor.fetchall()
    for row in r:
        return (row[0])
    return 0



def api_secret_get():
    db = MySQLdb.connect("database-service", "cryptouser", "123456", "cryptodb")
    cursor = db.cursor()
    cursor.execute("SELECT api_secret FROM parameters")
    r = cursor.fetchall()
    for row in r:
        return (row[0])
    return 0

def parameters():
    db = MySQLdb.connect("database-service", "cryptouser", "123456", "cryptodb")
    cursor = db.cursor()
    cursor.execute("SELECT * FROM parameters")
    r = cursor.fetchall()
    for row in r:
        return (row[1]), (row[2]), (row[3]), (row[4]), (row[5]), (row[6]), (row[7]), (row[8]), (row[9]), (row[10]), (row[11]), (row[12]), (row[13]), (row[14]), (row[15]), (row[16]), (row[17]), (row[18]), (row[19]), (row[20]), (row[21]), (row[22]), (row[23]), (row[24])

    return 0


if __name__ == "__main__":
    main()