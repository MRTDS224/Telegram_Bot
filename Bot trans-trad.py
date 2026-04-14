from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, MessageHandler, filters, CallbackQueryHandler, CallbackContext
import speech_recognition as sr
from pydub import AudioSegment
from translate import Translator
import os
import logging
import nest_asyncio
from dotenv import load_dotenv

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

class VoiceTranscriptionBot:
    def __init__(self, token: str):
        """Initialize the bot with the given token."""
        self.token = token
        self.recognizer = sr.Recognizer()
        self.from_lang = None
        self.to_lang = None
        logging.info("Bot initialized with token: %s", token)

    def translate_text(self, text: str, from_lang: str, to_lang: str) -> str:
        logging.info("Translating text from %s to %s: %s", from_lang, to_lang, text)
        try:
            translator = Translator(from_lang=from_lang, to_lang=to_lang)
            translation = translator.translate(text)
            logging.info("Translation successful: %s", translation)
            return translation
        except Exception as e:
            logging.error("Error during translation: %s", e)
            return ""

    async def start(self, update: Update, context: CallbackContext) -> None:
        # Menu de choix de langue
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
        await update.message.reply_text('Choose your language:', reply_markup=reply_markup)
                
    async def set_language(self, update: Update, context: CallbackContext) -> None:
        query = update.callback_query
        await query.answer()
        language_code = query.data
        language_name = LANGUAGES.get(language_code, "Langue inconnue")

        context.user_data['language'] = language_code

        self.from_lang = language_code

        language_name = self.translate_text(language_name, 'fr', self.from_lang)
        message = self.translate_text("Language set to", 'en', self.from_lang)
    
    
        await query.edit_message_text(f"{message} {language_name}.")
    
        # Menu de choix de langue de transcription
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
        await update.callback_query.message.reply_text(self.translate_text('Choose your translation language:', 'en', self.from_lang), reply_markup=reply_markup)
    
    async def to_language(self, update: Update, context: CallbackContext) -> None:
        query = update.callback_query
        await query.answer()
        
        # Définir la langue de transcription
        language_code = query.data.replace('_transcribe', '')
        language_name = LANGUAGES.get(language_code, "Langue inconnue")

        context.user_data['transcribe_language'] = language_code
        self.to_lang = language_code

        # Traduire le message
        language_name = self.translate_text(language_name, 'fr', self.from_lang)
        message1 = self.translate_text("Your audio message will be transcribed in", 'en', self.from_lang)
        message2 = self.translate_text("Now, send me your audio message", 'en', self.from_lang)
        await query.edit_message_text(f"{message1} {language_name} \n{message2}")
    
    async def transcribe_audio(self, update: Update, context: CallbackContext) -> None:
        voice_path = None
        wav_path = None
        try:
            # Télécharger le fichier audio
            voice_file = await update.message.voice.get_file()
            voice_path = 'voice_message.ogg'
            wav_path = 'voice_message.wav'
        
            await update.message.reply_text(self.translate_text("Traitement de votre message vocal...", 'fr', self.from_lang))
    
            # Télécharger et convertir le fichier
            await voice_file.download_to_drive(voice_path)
            logger.info('Voice message downloaded successfully.')
    
            # Convertir OGG en WAV
            audio = AudioSegment.from_ogg(voice_path)
            audio.export(wav_path, format="wav")
            logger.info('Audio converted to WAV successfully.')
    
            # Transcrire l'audio
            with sr.AudioFile(wav_path) as source:
                audio_data = self.recognizer.record(source)
                try:
                    # Transcrire
                    original_text = self.recognizer.recognize_google(audio_data, language=self.from_lang)
                    logger.info('Transcription successful.')
            
                    # Traduire
                    translated_text = self.translate_text(original_text, self.from_lang, self.to_lang)
                    message1 = self.translate_text("Transcription originale", 'fr', self.from_lang)
                    message2 = self.translate_text("Traduction", 'fr', self.from_lang)
                    response = (
                        f"📝 {message1} ({self.from_lang}):\n{original_text}\n"
                        f"🔄 {message2} ({self.to_lang}):\n{translated_text}"
                    )
            
                    await update.message.reply_text(response)
            
                except sr.UnknownValueError:
                    await update.message.reply_text(self.translate_text("Désolé, je n'ai pas pu comprendre l'audio. Assurez-vous que l'enregistrement est clair.", 'fr', self.from_lang)
                    )
                    logger.error('SpeechRecognition could not understand the audio.')
                except sr.RequestError as e:
                    await update.message.reply_text(
                    self.translate_text(f"Erreur d'accès au service de reconnaissance vocale : {str(e)}", 'fr', self.from_lang)
                    )
                    logger.error(f'SpeechRecognition error: {e}')
        
        except Exception as e:
            logger.error(f"An error occurred: {e}")
            await update.message.reply_text(
                self.translate_text("Désolé, une erreur s'est produite lors du traitement de votre audio. Veuillez réessayer.", 'fr', self.from_lang)
            )
            
        finally:
            # Nettoyer les fichiers temporaires
            try:
                if voice_path and os.path.exists(voice_path):
                    os.remove(voice_path)
                if wav_path and os.path.exists(wav_path):
                    os.remove(wav_path)
            except Exception as e:
                logger.error(f"Error cleaning up files: {e}")
    
    def run(self):
        """Start the bot."""
        try:
            # Créer l'application
            application = Application.builder().token(self.token).build()
        
            # Ajouter les gestionnaires
            application.add_handler(CommandHandler("start", self.start))
            application.add_handler(MessageHandler(filters.VOICE, self.transcribe_audio))
            application.add_handler(CallbackQueryHandler(self.set_language, pattern="^(?!.*_transcribe$).*$"))
            application.add_handler(CallbackQueryHandler(self.to_language, pattern=".*_transcribe$"))
        
            # Démarrer le bot
            logger.info("Starting bot...")
            application.run_polling()
        
        except Exception as e:
            logger.error(f"Failed to start bot: {e}")
    
def main():
    # Remplacer par votre jeton de bot    
    load_dotenv() 
    TOKEN = os.getenv("TELEGRAM_TOKEN")
        
    if not TOKEN:
        logger.error("Le jeton TELEGRAM_TOKEN n'est pas défini.")
        return
    
    bot = VoiceTranscriptionBot(TOKEN)
    bot.run()
    
if __name__ == "__main__":
    main()

