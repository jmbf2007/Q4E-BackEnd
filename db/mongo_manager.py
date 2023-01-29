import logging
from pymongo import MongoClient
from pymongo.database import Database


class MongoManager:
    client: MongoClient = None
    db: Database = None

    def connect_to_database(self, path: str):
        logging.info("Connecting to MongoDB.")
        self.client = MongoClient(path)
        self.db = self.client['db']
        logging.info("Connected to MongoDB.")

    def close_database_connection(self):
        logging.info("Closing connection with MongoDB.")
        self.client.close()
        logging.info("Closed connection with MongoDB.")

    def get_users(self):
        users_query = self.db.users.find({}, {'_id': 0})
        return list(users_query)