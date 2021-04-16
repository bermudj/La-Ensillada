'''
Translator module
14/04/21
Jesús A Bermúdez Silva
'''

'''
pyinstaller --onefile -w translator.py
'''
import socket
import sys
import net

ENGLISH_SPANISH = "1"
SPANISH_ENGLISH = "2"

WORD_NOT_FOUND = "No translation"

SERVER_HOST = socket.gethostbyname(socket.gethostname())

Words = [("Hello", "Hola"),
         ("Bye",  "Adios"),
         ("Tomorrow",  "Mañana"),
         ("Good", "Bien"),
         ("Thanks", "Gracias"),
         ("Now", "Ahora"),
         ("Later", "Después")]

transType = sys.argv[1]
addrSpeaker = sys.argv[2]
portSpeaker = sys.argv[3]

spk = net.getConnectedReqRepSocket(SERVER_HOST, (addrSpeaker, int(portSpeaker)))
spk.send(b"Translator's whereabouts ")

while True:

    reply = WORD_NOT_FOUND
    word = spk.recv(net.BUFFER_SIZE)
    word = word.decode()
    if transType == ENGLISH_SPANISH:
        for w in Words:
            if word == w[0]:
                reply = w[1]
                break
    else:
        for w in Words:
            if word == w[1]:
                reply = w[0]
                break


    spk.send(reply.encode())


#if want to use google translate
'''    
def translate_text(target, text):
    """Translates text into the target language.

    Target must be an ISO 639-1 language code.
    See https://g.co/cloud/translate/v2/translate-reference#supported_languages
    """
    import six
    from google.cloud import translate_v2 as translate

    translate_client = translate.Client()

    if isinstance(text, six.binary_type):
        text = text.decode("utf-8")

    # Text can also be a sequence of strings, in which case this method
    # will return a sequence of results for each text.
    result = translate_client.translate(text, target_language=target)

    return result["translatedText"]
'''
