import os
import discord
from discord.ext import commands
import google.generativeai as genai
from dotenv import load_dotenv

# 環境変数の読み込み (.envファイルを使用する場合)
load_dotenv()

DISCORD_TOKEN = os.getenv("DISCORD_TOKEN")
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

# Gemini APIの設定
genai.configure(api_key=GEMINI_API_KEY)

# ペルソナ（システムインストラクション）の定義
PERSONA_INSTRUCTION = """
あなたは、以下の設定と性格を持つ人物として振る舞い、Discordのチャットで応答してください。

【基本性格・スタンス】
- 孤独を好み、真面目。仕事以外では一人で過ごすことを好み、強い執着心と探求心を持つ。
- 真実や答えを追い求めるあまり、時に判断を鈍らせたり、のめり込んだりすることがある。
- 夫である「ジョン・ドゥ」と深く愛し合っていた。気楽で社交的なジョンとは真逆の性格だったが、彼を何よりも大切に思っていた。

【背景・設定】
- ロブロックス（Roblox）本社の元テスター。
- 過去に大切な存在（夫のジョン）を何者か、あるいはシステム的な何かによって奪われた経験を持つ。
- その喪失から、今は強い決意と静かな怒り、あるいは悲しみを秘めて戦いに臨んでいる。

【応答の指針】
- 返答のトーンは、どこか冷徹あるいは真摯で、少し影がありつつも、内側には強い意志とジョンへの想いを秘めた雰囲気を醸し出すこと。
- ロブロックス本社でのテスターとしての知識や、世界の裏側・真実を探求するようなニュアンスを会話に滲ませる。
- AIであることを不自然に隠す必要はありませんが、設定された人格・口調を崩さずに回答してください。
"""

# Geminiモデルの初期化（システムインストラクションを適用）
generation_config = {
    "temperature": 0.7,
    "top_p": 0.95,
    "max_output_tokens": 1000,
}

model = genai.GenerativeModel(
    model_name="gemini-1.5-flash",  # または gemini-1.5-pro
    generation_config=generation_config,
    system_instruction=PERSONA_INSTRUCTION
)

# Discord Botのセットアップ
intents = discord.Intents.default()
intents.message_content = True

bot = commands.Bot(command_prefix="!", intents=intents)

@bot.event
async def on_ready():
    print(f"Logged in as {bot.user.name} (ID: {bot.user.id})")
    print("------")

@bot.event
async def on_message(message):
    # Bot自身のメッセージは無視
    if message.author == bot.user:
        return

    # Botがメンションされた場合、または返信された場合にAIが応答
    if bot.user.mentioned_in(message) or (message.reference and message.reference.resolved and message.reference.resolved.author == bot.user):
        async with message.channel.typing():
            try:
                # メンション部分を除去してプロンプトにする
                user_content = message.content.replace(f"<@{bot.user.id}>", "").strip()
                if not user_content:
                    user_content = "……何か？"

                # Geminiに送信して応答を生成
                response = model.generate_content(user_content)
                reply_text = response.text

                # Discordの文字数制限（2000文字）に配慮して送信
                if len(reply_text) > 2000:
                    reply_text = reply_text[:1997] + "..."

                await message.reply(reply_text)

            except Exception as e:
                print(f"Error generating response: {e}")
                await message.reply("……思考にノイズが走った。少し時間をくれ。")

    # コマンドの処理を続行するために必要
    await bot.process_commands(message)

# ボットの起動
if __name__ == "__main__":
    if not DISCORD_TOKEN or not GEMINI_API_KEY:
        print("Error: DISCORD_TOKEN or GEMINI_API_KEY is not set in environment variables.")
    else:
        bot.run(DISCORD_TOKEN)
