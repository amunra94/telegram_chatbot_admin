TOKEN = '' # bot token
GROUP_ID = 2 # id of chat telegram
DATABASE = 'database.sqlite' # name db

WEBHOOK_HOST = '' # your ip server
WEBHOOK_PORT = 443  # 443, 80, 88, 8443
WEBHOOK_LISTEN = '' # your ip server

WEBHOOK_SSL_CERT = './webhook_cert.pem'  # path to certificate
WEBHOOK_SSL_PRIV = './webhook_pkey.pem'  # path to private key

WEBHOOK_URL_BASE = "https://%s:%s" % (WEBHOOK_HOST, WEBHOOK_PORT)
WEBHOOK_URL_PATH = "/%s/" % settings.TOKEN