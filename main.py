import json
import aiohttp
import rebootpy
from rebootpy.ext import commands
import platform
import os
import sys
from pathlib import Path

configFile = "config.json"
API = "https://fortnite-api.com/v2/cosmetics/br/search/all"

Type = {
    'outfit': {'backendType': 'AthenaCharacter', 'name': 'outfit'},
    'emote': {'backendType': 'AthenaDance', 'name': 'emote'},
    'backpack': {'backendType': 'AthenaBackpack', 'name': 'backpack'},
    'pickaxe': {'backendType': 'AthenaPickaxe', 'name': 'pickaxe'},
    'glider': {'backendType': 'AthenaGlider', 'name': 'glider'},
    'contrail': {'backendType': 'AthenaContrail', 'name': 'contrail'}
}

def Config():
    if not Path(configFile).exists():
        sys.exit(1)
    
    with open(configFile, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    auth = data.get('auth', {})
    bot = data.get('bot', {})
    fortnite = data.get('fortnite', {})
    
    return {
        'device': auth.get('device', ''),
        'accountId': auth.get('accountId', ''),
        'secretKey': auth.get('secret', ''),
        'status': bot.get('status', 'SizzyBotV1'),
        'platformType': bot.get('platform', 'Windows'),
        'prefix': bot.get('prefix', '!'),
        'Cosmetic': fortnite.get('cosmetic', {}),
        'banner': fortnite.get('banner', {}),
        'party': fortnite.get('party', {}),
        'addUsers': fortnite.get('party', {}).get('add_users', True)
    }

async def Cosmetics(itemName, cosmeticType):
    if cosmeticType not in Type:
        return None
    
    searchParams = {
        'name': itemName,
        'backendType': Type[cosmeticType]['backendType']
    }
    
    async with aiohttp.ClientSession() as session:
        try:
            async with session.get(API, params=searchParams) as resp:
                if resp.status == 200:
                    apiData = await resp.json()
                    if apiData['data']:
                        return apiData['data'][0]['id']
        except:
            pass
    return None

def setup(config):
    if config['device'] and config['secretKey'] and config['accountId']:
        authMethod = rebootpy.DeviceAuth(
            device_id=config['device'],
            secret=config['secretKey'],
            account_id=config['accountId']
        )
    else:
        authMethod = rebootpy.AdvancedAuth(prompt_device_code=True)
    
    botInstance = commands.Bot(
        auth=authMethod,
        command_prefix=config['prefix'],
        status=config['status']
    )
    
    return botInstance

def console():
    if platform.system() == 'Windows':
        os.system('cls')
    else:
        os.system('clear')

async def cosmetics(bot, cosmeticType, itemName):
    cosmeticId = await Cosmetics(itemName, cosmeticType)
    
    if cosmeticId and bot.party:
        methodToCall = Type[cosmeticType]['name']
        cosmeticMethod = getattr(bot.party.me, methodToCall)
        await cosmeticMethod(cosmeticId)

async def load(bot, config):
    if not bot.party:
        return
    
    Items = config['Cosmetic']  
    
    if Items.get('cid'):
        await bot.party.me.outfit(Items['cid'])
    
    if Items.get('eid'):
        await bot.party.me.emote(Items['eid'])
    
    if Items.get('backpack'):
        await bot.party.me.backpack(Items['backpack'])
    
    if Items.get('pickaxe'):
        await bot.party.me.pickaxe(Items['pickaxe'])
    
    if Items.get('glider'):
        await bot.party.me.glider(Items['glider'])
    
    if Items.get('contrail'):
        await bot.party.me.contrail(Items['contrail'])
    
    bannerSettings = config['banner']
    if bannerSettings.get('icon'):
        await bot.party.me.set_banner(
            icon=bannerSettings['icon'],
            color=bannerSettings.get('color', 'DefaultColor')
        )

async def join(bot, username):
    try:
        userProfile = await bot.fetch_user(user=username, cache=True)
        if not userProfile:
            return
        
        connections = bot.get_friend(userProfile.id)
        if connections:
            await connections.join_party()
    except:
        pass

async def Input(bot, config):
    while bot.party:
        try:
            userInput = input("\nSizzyBot > ").strip()
            if not userInput:
                continue
            
            if userInput[0] != '!':
                continue
            
            splitInput = userInput[1:].split()
            if not splitInput:
                continue
            
            command = splitInput[0].lower()
            arguments = splitInput[1:]
            
            if command in ['clear', 'cls']:
                console()
            elif command == 'outfit':
                await cosmetics(bot, 'outfit', ' '.join(arguments))
            elif command == 'emote':
                await cosmetics(bot, 'emote', ' '.join(arguments))
            elif command == 'backpack':
                await cosmetics(bot, 'backpack', ' '.join(arguments))
            elif command == 'pickaxe':
                await cosmetics(bot, 'pickaxe', ' '.join(arguments))
            elif command == 'glider':
                await cosmetics(bot, 'glider', ' '.join(arguments))
            elif command == 'contrail':
                await cosmetics(bot, 'contrail', ' '.join(arguments))
            elif command == 'join':
                await join(bot, ' '.join(arguments))
            elif command == 'leave':
                await bot.party.me.leave()
            elif command == 'exit':
                sys.exit()
                
        except KeyboardInterrupt:
            break
        except:
            pass

async def Ready(bot, config):
    await load(bot, config)
    await Input(bot, config)

def launch():
    config = Config()
    bot = setup(config)
    
    @bot.event
    async def event_ready():
        await Ready(bot, config)
    
    try:
        bot.run()
    except:
        sys.exit(1)

if __name__ == "__main__":
    launch()
