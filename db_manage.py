from models import *



def create_user_if_not_exist(user_id: int):

    if User.select().where(User.user_id == user_id).exists():
        return
    
    User.create(user_id=user_id)

def create_channel_sponsor(channel_id: int):

    if ChannelSponsor.select().where(ChannelSponsor.channel_id == channel_id).exists():
        return
    
    ChannelSponsor.create(channel_id=channel_id)

def remove_channel_sponsor(channel_id: int) -> None:
    ChannelSponsor.delete().where(ChannelSponsor.channel_id == channel_id).execute()

def get_all_users() -> list:

    users = []

    for user in User.select():
        users.append(user.user_id)

    return users

def get_all_channels_sponsors() -> list:

    channels = []

    for channel in ChannelSponsor.select():
        channels.append(channel.channel_id)

    return channels