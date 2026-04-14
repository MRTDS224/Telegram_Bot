from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, MessageHandler, filters, CallbackQueryHandler, CallbackContext
import speech_recognition as sr
from pydub import AudioSegment
from translate import Translator
import os
import logging
import nest_asyncio
from dotenv import load_dotenv
import pyttsx3

# Configure nest_asyncio pour éviter les erreurs de boucle d'événements dans Jupyter Notebook
nest_asyncio.apply()
# Configure logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# Languages available
LANGUAGES = {
    'en': 'English',
    'fr': 'Français',
    'es': 'Español',
    'ar': 'العربية',
    'de': 'Deutsch'
}

def text_to_speech(text: str, lang: str, filename: str) -> None:
    """Convert text to speech."""
    try:
        # Initialize the text-to-speech engine
        engine = pyttsx3.init()
        voices = engine.getProperty('voices')
        engine.setProperty('voice', voices[0].id)  # Choose a voice 
        engine.setProperty('rate', 150)  # Speed of speech
        engine.setProperty('volume', 0.9)  # Volume level
        
        engine.save_to_file(text, filename)
        engine.runAndWait()
    except Exception as e:
        logger.error(f"An error occurred during text-to-speech conversion: {e}")

def translate_text(text: str, from_lang: str, to_lang: str) -> str:
    if from_lang not in LANGUAGES or to_lang not in LANGUAGES:
        return "Invalid language code"
    
    logging.info("Translating text from %s to %s: %s", from_lang, to_lang, text)
    try:
        translator = Translator(from_lang=from_lang, to_lang=to_lang)
        translation = translator.translate(text)
        logging.info("Translation successful: %s", translation)
        return translation
    except Exception as e:
        logging.error("Error during translation: %s", e)
        return "Error translating text"

async def start(update: Update, context: CallbackContext) -> None:
    keyboard = [
        [
            InlineKeyboardButton("English", callback_data='en'),
            InlineKeyboardButton("Français", callback_data='fr'),
            InlineKeyboardButton("Español", callback_data='es'),
            InlineKeyboardButton("العربية", callback_data='ar'),
            InlineKeyboardButton("Deutsch", callback_data='de')
        ]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text('Please choose your language:', reply_markup=reply_markup)

async def language_selection(update: Update, context: CallbackContext) -> None:
    query = update.callback_query
    await query.answer()

    if '_transcribe' in query.data:
        # Set the transcribe language
        language_code = query.data.replace('_transcribe', '')
        context.user_data['to_lang'] = language_code
        language_name = LANGUAGES.get(language_code, 'Unknown language')
        message = translate_text("Your audio message will be transcribed to: {}. \nNow, send me your audio message", 'en', context.user_data.get('from_lang', 'en'))
        await query.edit_message_text(message.format(language_name))
    else:
        # Set the user's language
        language_code = query.data
        context.user_data['from_lang'] = language_code
        language_name = LANGUAGES.get(language_code, 'Unknown language')
        message = translate_text("Language set to: ", 'en', language_code)
        await query.edit_message_text(f"{message} {language_name}")

        # Menu to choose the language to transcribe to
        keyboard = [
            [
                InlineKeyboardButton("English", callback_data='en_transcribe'),
                InlineKeyboardButton("Français", callback_data='fr_transcribe'),
                InlineKeyboardButton("Español", callback_data='es_transcribe'),
                InlineKeyboardButton("العربية", callback_data='ar_transcribe'),
                InlineKeyboardButton("Deutsch", callback_data='de_transcribe')
            ]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        await query.edit_message_text(translate_text('Choose your translation language:', 'en', language_code), reply_markup=reply_markup)

async def transcribe_audio(update: Update, context: CallbackContext) -> None:
    voice_path = 'voice_message.ogg'
    wav_path = 'voice_message.wav'
    try:
        # Download the voice message
        voice_file = await update.message.voice.get_file()
        await voice_file.download_to_drive(voice_path)
        logger.info("Voice message downloaded successfully.")
        
        # Convert the voice message to wav
        voice = AudioSegment.from_file(voice_path, format='ogg')
        voice.export(wav_path, format='wav')
        logger.info("Voice message converted to wav successfully.")
        
        # Transcribe the audio message
        with sr.AudioFile(wav_path) as source:
            r = sr.Recognizer()
            audio = r.record(source)
            from_lang = context.user_data.get('from_lang', 'en')
            text = r.recognize_google(audio, language=from_lang)
            logger.info("Audio message transcribed successfully.")
            
            #storing the original transcription in the user_data
            context.user_data['original_transcription'] = text
            
            # Send the transcription to the user with the keyboard to translate it or transcribe another audio
            message = translate_text("Original transcription", from_lang, context.user_data.get('to_lang', 'en'))
            response = f"📝 {message} ({from_lang}):\n{text}"
            
            #create the keyboard
            keyboard = [
                [
                    InlineKeyboardButton("Translate", callback_data='translate'),
                    InlineKeyboardButton("Transcribe another audio", callback_data='transcribe'),
                    InlineKeyboardButton("It's OK", callback_data='ok')
                ]
            ]
            reply_markup = InlineKeyboardMarkup(keyboard)
            
            await update.message.reply_text(response, reply_markup=reply_markup)
        
    except sr.UnknownValueError:
        logger.error("Google Speech Recognition could not understand the audio")
        await update.message.reply_text(translate_text("Sorry, I could not understand the audio", 'en', context.user_data.get('to_lang', 'en')))
    except sr.RequestError as e:
        logger.error("Could not request results from Google Speech Recognition service; {0}".format(e))
        await update.message.reply_text(translate_text("Sorry, an error occurred while processing the audio", 'en', context.user_data.get('to_lang', 'en')))
    except Exception as e:
        logger.error("An error occurred while processing the audio; {0}".format(e))
        await update.message.reply_text(translate_text("Sorry, an error occurred while processing the audio", 'en', context.user_data.get('to_lang', 'en')))
    finally:
        # Delete the audio files
        try:
            if os.path.exists(voice_path):
                os.remove(voice_path)
            if os.path.exists(wav_path):
                os.remove(wav_path)
            logger.info("Audio files deleted successfully.")
        except Exception as e:
            logger.error("An error occurred while deleting the audio files; {0}".format(e))

async def button_handler(update: Update, context: CallbackContext) -> None:
    query = update.callback_query
    await query.answer()
        
    if query.data == 'translate':
            # Get the original transcription
            original_text = context.user_data.get('original_transcription', query.message.text)
            from_lang = context.user_data.get('from_lang', 'en')
            to_lang = context.user_data.get('to_lang', 'en')
            
            if not original_text:
                await update.message.reply_text(translate_text("Please send me an audio message first", 'en', context.user_data.get('to_lang', 'en')))
                return
                
            #translate the transcription
            translated_text = translate_text(original_text, from_lang, to_lang)
            message = translate_text("Translation", from_lang, to_lang)
            await context.bot.send_message(chat_id=query.message.chat_id,  # ID du chat
            text=f"🔄️ {message} ({to_lang}):\n{translated_text}"    )
            
            text_to_speech(translated_text, to_lang, 'output.ogg')
            await context.bot.send_voice(chat_id=query.message.chat.id, voice=open('output.ogg', 'rb'))
     
    elif query.data == 'transcribe':
        # Get the previous transcription
        previous_transcription = query.message.text

        # Send a message to the user to send a new audio message
        await context.bot.send_message(
            chat_id=query.message.chat_id,
            text=translate_text(
                "Please send me a new audio message. The previous transcription was:\n\n{}",
                'en',
                context.user_data.get('to_lang', 'en')
            ).format(previous_transcription)
        )
            
    elif query.data == 'ok':
            await context.bot.send_message(chat_id=query.message.chat_id, text=translate_text("OK, I'm here if you need me", 'en', context.user_data.get('to_lang', 'en')))

def main():
    load_dotenv()
    token = os.getenv('TELEGRAM_TOKEN')
    if not token:
        raise ValueError("You must set the TELEGRAM_TOKEN environment variable")
    # Start the bot
    try:
        # Create the Application instance
        app = Application.builder().token(token=token).build()
        app.add_handler(CommandHandler('start', start))
        app.add_handler(CallbackQueryHandler(language_selection, pattern="^(en|fr|es|ar|de)"))
        app.add_handler(CallbackQueryHandler(button_handler, pattern="^(translate|transcribe|ok)$"))
        app.add_handler(MessageHandler(filters.VOICE, transcribe_audio))
        
        # Start the bot
        app.run_polling()
        logger.info("Bot started successfully.")
    except Exception as e:
        logger.error("Failed to start bot; {0}".format(e))

if __name__ == '__main__':
    # main()
    text = """Here’s a concise summary of the presentation titled **“GSM & GPRS: The Evolution of Mobile Communication”** by Prof. Khalid Souissi, Diallo Mamadou Tahirou, Lamrani Ahmed, and Compaoré Moustapha:

### 📱 Main Topics Covered
- **GSM (Global System for Mobile Communications):**
  - Origins and development as a 2G mobile standard
  - Key features: digital voice transmission, SMS, international roaming
  - Network architecture: Base Station Subsystem (BSS), Network Switching Subsystem (NSS), and Operation Support Subsystem (OSS)

- **GPRS (General Packet Radio Service):**
  - Enhancement of GSM for data services (2.5G)
  - Packet-switched data transmission enabling mobile internet
  - Applications: email, web browsing, multimedia messaging

- **Technological Evolution:**
  - Transition from circuit-switched to packet-switched networks
  - Role of GPRS in paving the way for 3G and beyond

- **Impact on Society:**
  - Expansion of mobile connectivity
  - Foundation for mobile data services and modern smartphones

If you’d like, I can help you turn this into speaker notes, quiz questions, or even a visual timeline."""
    text_to_speech(text, 'en', 'output.ogg')