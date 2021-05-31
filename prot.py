'''
Client-Server protocol codes
'''
# Request Codes to main server
REGISTER_USER       = "1"
DE_REGISTER_USER    = "2"
GET_USER            = "3"
CALL_USER           = "4"
GET_TRANSLATOR      = "5"
BUFFER_MESSAGE      = "6"
DOWNLOAD_MESSAGES   = "7"
SET_LANGUAGE        = "8"
GET_LANGUAGE        = "9"
ACCEPT_CALL_USER    = "10"
SHUTDOWN_SERVER     = "11"

# Reply Codes from main server
USER_REGISTERED         = "0"
UNABLE_TO_REGISTER      = "1"
USER_NOT_REG            = "2"
USER_IS                 = "3"
FINISH_DOWNLOAD         = "4"
DE_REGISTERED_COMPLETE  = "5"
SENDING_MESSAGE         = "6"
LANGUAGE_USED           = "7"
USER_CALLING            = "8"
USER_ACCEPTED_CALL      = "9"

# Request Codes to translator
TRANSLATE_CMD           = "0"
STOP_TRANSLATING_CMD    = "1"

# Reply Codes from translator
I_AM_YOUR_TRANSLATOR    = "0"