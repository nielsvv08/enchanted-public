import asyncio
import os

from motor.motor_asyncio import AsyncIOMotorClient

db_new = AsyncIOMotorClient("!!!! MONGODB SECRET !!!!")

async def main():
    coll = db_new['enchanted-main']['clans']
    coll_users = db_new['enchanted-main']['users']

    while True:
        for clan in coll.find({}):
            all_members = coll_users.find({'user_id': {'$in': clan['members']}})
            clan['power'] = sum(member['power'] for member in all_members)
            coll.update_one({'name': clan["name"]}, {'$set': {'power': clan['power'], "member_count": len(clan['members'])}})

        for clan in coll.find({}):
            clan['key_storage'] += clan['key_factory']
            if clan['key_storage'] > clan['key_storage_max']:
                clan['key_storage'] = clan['key_storage_max']
            clan['coin_storage'] += clan['coin_mint']
            if clan['coin_storage'] > clan['coin_storage_max']:
                clan['coin_storage'] = clan['coin_storage_max']
            clan['ruby_storage'] += clan['ruby_miner']
            if clan['ruby_storage'] > clan['ruby_storage_max']:
                clan['ruby_storage'] = clan['ruby_storage_max']
            coll.update_one({'name': clan['name']}, {'$set': clan})
        await asyncio.sleep(3600)


loop = asyncio.get_event_loop()
loop.run_until_complete(main())
