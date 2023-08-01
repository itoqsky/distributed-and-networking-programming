import sqlite3
from concurrent.futures import ThreadPoolExecutor

import grpc
import schema_pb2 as stub
import schema_pb2_grpc as service

SERVER_ADDR = '0.0.0.0:1234'

class Database(service.DatabaseServicer):
    def __init__(self):
        try:
            self.executor = ThreadPoolExecutor(max_workers=10)
            sqliteConnection = sqlite3.connect('db.sqlite')
            cursor = sqliteConnection.cursor()
            cursor.execute("CREATE TABLE IF NOT EXISTS users (user_id INTEGER PRIMARY KEY, user_name TEXT)")
            sqliteConnection.commit()
            cursor.close()
            sqliteConnection.close()
        except Exception as error:
            print("Error in Database.__init__(): ", error)

    def PutUser(self, request, context):
        print("PutUser()")
        user_id = request.user_id
        user_name = request.user_name
        try:
            sqliteConnection = sqlite3.connect('db.sqlite')
            cursor = sqliteConnection.cursor()
            cursor.execute("INSERT or REPLACE INTO users (user_id, user_name) VALUES (?, ?)", (user_id, user_name))
            sqliteConnection.commit()
            cursor.close()
            sqliteConnection.close()
            return stub.ResponseMessage(status=True)
        except Exception as error:
            print("Error in Database.PutUser(): ",error)
            return stub.ResponseMessage(status=False)
        
    def GetUsers(self, request, context):
        print("GetUsers()")
        try:
            sqliteConnection = sqlite3.connect('db.sqlite')
            cursor = sqliteConnection.cursor()
            res = cursor.execute("SELECT user_id, user_name FROM users")
            users = []

            for row in res.fetchall():
                users.append({
                    "user_id": row[0],
                    "user_name": row[1]
                })
            cursor.close()
            sqliteConnection.close()
            return stub.Users(users=users)
        except Exception as error:
            print("Error in Database.GetUser(): ", error)
            return stub.Users(users=[])
        


    def DeleteUser(self, request, context):
        print("DeleteUser()")
        user_id = request.user_id
        try:
            sqliteConnection = sqlite3.connect('db.sqlite')
            cursor = sqliteConnection.cursor()
            cursor.execute("DELETE FROM users WHERE user_id = ?", (user_id,))
            sqliteConnection.commit()
            cursor.close()
            sqliteConnection.close()
            return stub.ResponseMessage(status=True)
        except Exception as error:
            print("Error in Database.DeleteUser(): ", error)
            return stub.ResponseMessage(status=False)

        
if __name__ == '__main__':
    server = grpc.server(Database().executor)
    try:
        service.add_DatabaseServicer_to_server(Database(), server)
        server.add_insecure_port(SERVER_ADDR)
        server.start()

        print(f"Server started at {SERVER_ADDR}")
        server.wait_for_termination()
    except KeyboardInterrupt as error:
        print("\nShutting down server...")
        server.stop(0)

