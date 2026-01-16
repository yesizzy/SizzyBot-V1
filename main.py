import json
import aiohttp
import rebootpy
from rebootpy.ext import commands
import platform
import os
import sys
from pathlib import Path

configFile = "config.json"
Api = "https://fortnite-api.com/v2/cosmetics/br/search/all"

cosmeticMap = {
    'outfit': {'backendType': 'AthenaCharacter', 'methodName': 'set_outfit'},
    'emote': {'backendType': 'AthenaDance', 'methodName': 'set_emote'},
    'backpack': {'backendType': 'AthenaBackpack', 'methodName': 'set_backpack'},
    'pickaxe': {'backendType': 'AthenaPickaxe', 'methodName': 'set_pickaxe'},
    'sidekick': {'backendType': 'AthenaPet', 'methodName': 'set_pet'},
    'shoes': {'backendType': 'AthenaShoes', 'methodName': 'set_shoes'},
    'glider': {'backendType': 'AthenaGlider', 'methodName': 'set_glider'},
    'contrail': {'backendType': 'AthenaContrail', 'methodName': 'set_contrail'}
}

def grabConfig():
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

async def findCosmeticId(itemName, cosmeticType):
    if cosmeticType not in cosmeticMap:
        return None
    
    searchParams = {
        'name': itemName,
        'backendType': cosmeticMap[cosmeticType]['backendType']
    }
    
    async with aiohttp.ClientSession() as session:
        try:
            async with session.get(Api, params=searchParams) as resp:
                if resp.status == 200:
                    apiData = await resp.json()
                    if apiData['data']:
                        return apiData['data'][0]['id']
        except:
            pass
    return None

def setupBot(config):
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

def wipeConsole():
    if platform.system() == 'Windows':
        os.system('cls')
    else:
        os.system('clear')

async def changeCosmetic(bot, cosmeticType, itemName):
    cosmeticId = await findCosmeticId(itemName, cosmeticType)
    
    if cosmeticId and bot.party:
        methodToCall = cosmeticMap[cosmeticType]['methodName']
        cosmeticMethod = getattr(bot.party.me, methodToCall)
        await cosmeticMethod(cosmeticId)
    
async def loadDefaults(bot, config):
    if not bot.party:
        return
    
    defaultItems = config['Cosmetic']  # Changed from 'defaultCosmetic' to 'Cosmetic'
    
    if defaultItems.get('cid'):
        await bot.party.me.set_outfit(defaultItems['cid'])
    
    if defaultItems.get('eid'):
        await bot.party.me.set_emote(defaultItems['eid'])
    
    if defaultItems.get('backpack'):
        await bot.party.me.set_backpack(defaultItems['backpack'])
    
    if defaultItems.get('pickaxe'):
        await bot.party.me.set_pickaxe(defaultItems['pickaxe'])
    
    if defaultItems.get('sidekick'):
        await bot.party.me.set_pet(defaultItems['sidekick'])
    
    if defaultItems.get('shoes'):
        await bot.party.me.set_shoes(defaultItems['shoes'])
    
    if defaultItems.get('glider'):
        await bot.party.me.set_glider(defaultItems['glider'])
    
    if defaultItems.get('contrail'):
        await bot.party.me.set_contrail(defaultItems['contrail'])
    
    bannerSettings = config['banner']
    if bannerSettings.get('icon'):
        await bot.party.me.set_banner(
            icon=bannerSettings['icon'],
            color=bannerSettings.get('color', 'DefaultColor')
        )

async def joinUserParty(bot, username):
    try:
        userProfile = await bot.fetch_user(user=username, cache=True)
        if not userProfile:
            return
        
        friendConnection = bot.get_friend(userProfile.id)
        if friendConnection:
            await friendConnection.join_party()
    except:
        pass

def showCommands():
    pass

async def handleInput(bot, config):
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
                wipeConsole()
            elif command == 'outfit':
                await changeCosmetic(bot, 'outfit', ' '.join(arguments))
            elif command == 'emote':
                await changeCosmetic(bot, 'emote', ' '.join(arguments))
            elif command == 'backpack':
                await changeCosmetic(bot, 'backpack', ' '.join(arguments))
            elif command == 'pickaxe':
                await changeCosmetic(bot, 'pickaxe', ' '.join(arguments))
            elif command == 'sidekick':
                await changeCosmetic(bot, 'sidekick', ' '.join(arguments))
            elif command == 'shoes':
                await changeCosmetic(bot, 'shoes', ' '.join(arguments))
            elif command == 'glider':
                await changeCosmetic(bot, 'glider', ' '.join(arguments))
            elif command == 'contrail':
                await changeCosmetic(bot, 'contrail', ' '.join(arguments))
            elif command == 'join':
                await joinUserParty(bot, ' '.join(arguments))
            elif command == 'leave':
                await bot.party.me.leave()
            elif command == 'help':
                showCommands()
            elif command == 'exit':
                sys.exit()
                
        except KeyboardInterrupt:
            break
        except:
            pass

async def onBotReady(bot, config):
    await loadDefaults(bot, config)
    await handleInput(bot, config)

def launchBot():
    config = grabConfig()
    bot = setupBot(config)
    
    @bot.event
    async def event_ready():
        await onBotReady(bot, config)
    
    try:
        bot.run()
    except:
        sys.exit(1)

if __name__ == "__main__":
    launchBot()
