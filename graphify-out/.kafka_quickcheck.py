"""Quick connectivity check: Kafka from host, via aiokafka."""

import asyncio
import json

from aiokafka import AIOKafkaProducer, AIOKafkaConsumer
from aiokafka.admin import AIOKafkaAdminClient, NewTopic


async def main() -> None:
    bootstrap = "localhost:9092"
    topic = "smoke_check_topic"

    admin = AIOKafkaAdminClient(bootstrap_servers=bootstrap)
    await admin.start()
    try:
        await admin.create_topics([NewTopic(name=topic, num_partitions=1, replication_factor=1)])
        print("topic created:", topic)
    except Exception as exc:
        print("create skipped:", type(exc).__name__)
    finally:
        await admin.close()

    producer = AIOKafkaProducer(bootstrap_servers=bootstrap,
                                value_serializer=lambda v: json.dumps(v).encode())
    await producer.start()
    meta = await producer.send_and_wait(topic, value={"hello": "kafka"})
    print("produced:", meta.partition, meta.offset)
    await producer.stop()

    consumer = AIOKafkaConsumer(topic, bootstrap_servers=bootstrap,
                                auto_offset_reset="earliest",
                                consumer_timeout_ms=3000)
    await consumer.start()
    got = []
    async for msg in consumer:
        got.append(msg.value)
        if len(got) >= 1:
            break
    await consumer.stop()
    print("consumed:", got)


asyncio.run(main())
