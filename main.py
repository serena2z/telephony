# Standard library imports
import logging
import os
import sys

# Third-party imports
from fastapi import FastAPI, Request
from vocode.streaming.models.telephony import TwilioConfig
from pyngrok import ngrok
from vocode.streaming.telephony.config_manager.redis_config_manager import (
    RedisConfigManager,
)
from vocode.streaming.models.agent import ChatGPTAgentConfig
from vocode.streaming.models.message import BaseMessage
# from vocode.streaming.telephony.server.base import (
#     TwilioInboundCallConfig,
    #   TelephonyServer,
# )

from telephony_server import TelephonyServer, TwilioInboundCallConfig


from dotenv import load_dotenv, find_dotenv

from info_agent import (
    InformationCollectorAgentConfig,
    InformationCollectorAgentFactory,
)

from vocode.streaming.models.synthesizer import ElevenLabsSynthesizerConfig, StreamElementsSynthesizerConfig
import sqlite3

# if running from python, this will load the local .env
# docker-compose will load the .env file by itself
load_dotenv('.env', override=True)

app = FastAPI(docs_url=None)

logging.basicConfig()
logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)

config_manager = RedisConfigManager(
    logger=logger,
)

BASE_URL = os.getenv("BASE_URL")
if not BASE_URL:
    ngrok_auth = os.environ.get("NGROK_AUTH_TOKEN")
    if ngrok_auth is not None:
        ngrok.set_auth_token(ngrok_auth)
    port = sys.argv[sys.argv.index("--port") + 1] if "--port" in sys.argv else 3000

    # Open a ngrok tunnel to the dev server
    BASE_URL = ngrok.connect(port).public_url.replace("https://", "")
    logger.info('ngrok tunnel "{}" -> "http://127.0.0.1:{}"'.format(BASE_URL, port))

if not BASE_URL:
    raise ValueError("BASE_URL must be set in environment if not using pyngrok")

SYNTH_CONFIG = ElevenLabsSynthesizerConfig.from_telephone_output_device(
  api_key=os.getenv("ELEVEN_LABS_API_KEY") or "")


telephony_server = TelephonyServer(
    base_url=BASE_URL,
    config_manager=config_manager,
    inbound_call_configs=[
        TwilioInboundCallConfig(
            url="/inbound_call",
            agent_config=InformationCollectorAgentConfig(
                initial_message=BaseMessage(text="Welcome to my medical center. I'm your mom and I'll be helping you out today. How are you doing today?"),
                generate_responses=False,
            ),
            twilio_config=TwilioConfig(
                account_sid=os.environ["TWILIO_ACCOUNT_SID"],
                auth_token=os.environ["TWILIO_AUTH_TOKEN"],
            ),
            synthesizer_config=SYNTH_CONFIG,
            logger=logger,
        )
    ],
    # agent_factory=SpellerAgentFactory(),
    agent_factory=InformationCollectorAgentFactory(),
    logger=logger,
)

    

app.include_router(telephony_server.get_router())
