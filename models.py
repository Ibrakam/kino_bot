from peewee import *


db = SqliteDatabase('database.db')


class BaseModel(Model):
    class Meta:
        database = db

class User(BaseModel):

    class Meta:
        db_table = 'Users'
    
    user_id = IntegerField()

class ChannelSponsor(BaseModel):

    class Meta:
        db_table = 'ChannelSponsor'
    
    channel_id = IntegerField()

if __name__ == "__main__":

    db.create_tables([User, ChannelSponsor])