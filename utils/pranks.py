import random
import sys
import time


async def scramble_nickname(user):
    sys.stdout.write(f'scrambling {user.display_name}...\n')
    sys.stdout.flush()
    new_nick = list(user.display_name)
    random.shuffle(new_nick)    # Shuffles in-place
    new_nick = ''.join(new_nick)
    await user.edit(nick=new_nick)

async def random_swap_all_nicknames(user_list):
    display_names = [u.display_name for u in user_list]
    random.shuffle(display_names)
    for user in user_list:
        new_nick = display_names.pop()
        await user.edit(nick=new_nick)

def isAprFool():
    return time.strftime('%d-%b') == '01-Apr'