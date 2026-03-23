from faststream.rabbit import RabbitBroker

from src.util.config import RMQ_URL

broker = RabbitBroker(RMQ_URL)