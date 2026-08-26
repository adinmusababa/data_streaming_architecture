"""Kafka backend for the Message Broker service.

Maps the SAS-07 concepts onto Kafka primitives:

    Exchange     -> Kafka topic derived from the exchange name
    Routing key  -> topic binding (exchange/routing_key -> queue)
    Queue        -> Kafka topic that consumers subscribe to

The REST facade stays compatible with shared_sdk.clients.BrokerClient.
"""

from __future__ import annotations

import asyncio
import json
import time
import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any

from aiokafka import AIOKafkaProducer, AIOKafkaConsumer
from aiokafka.admin import AIOKafkaAdminClient, NewTopic
from aiokafka.errors import KafkaError
from aiokafka.structs import TopicPartition

from shared_sdk.logger import get_logger

logger = get_logger("kafka_backend")

# exchange name -> routing_key is collapsed into a single topic so one
# binding table entry covers the whole publish path.
_BINDING_SEPARATOR = "__"
_DLQ_SUFFIX = "dlq"


def topic_for(exchange: str, routing_key: str) -> str:
    """Resolve (exchange, routing_key) to a Kafka topic name."""
    return f"{exchange}{_BINDING_SEPARATOR}{routing_key}".lower().replace("-", "_")


def dlq_topic_for(queue: str) -> str:
    """Dead letter topic for a queue: <queue>__dlq."""
    return f"{queue}{_BINDING_SEPARATOR}{_DLQ_SUFFIX}"


@dataclass
class _Delivery:
    """A message handed to a consumer awaiting acknowledgement."""

    consumer_key: tuple[str, str]
    topic: str
    partition: int
    offset: int
    payload: Any


@dataclass
class BrokerStats:
    """Cumulative broker statistics."""

    total_publish: int = 0
    total_consume: int = 0
    total_failed: int = 0
    last_message_at: datetime | None = None
    started_at: float = field(default_factory=time.monotonic)
    errors: list[dict[str, Any]] = field(default_factory=list)

    def record_publish(self) -> None:
        self.total_publish += 1
        self.last_message_at = datetime.now(timezone.utc)

    def record_consume(self, count: int = 1) -> None:
        self.total_consume += count
        if count:
            self.last_message_at = datetime.now(timezone.utc)

    def record_failure(self, error: str) -> None:
        self.total_failed += 1
        self.errors.append({"time": datetime.now(timezone.utc).isoformat(), "error": error})
        if len(self.errors) > 100:
            self.errors.pop(0)

    @property
    def total_message(self) -> int:
        return self.total_publish + self.total_consume

    @property
    def processing_rate_per_sec(self) -> float:
        elapsed = max(time.monotonic() - self.started_at, 1e-6)
        return round(self.total_message / elapsed, 3)


class KafkaBackend:
    """Async Kafka producer/consumer/admin wrapper.

    A single long-lived producer serves every publish call.

    Consumers follow the SAS-07 workflow: subscribe -> receive ->
    acknowledge. Each (queue, group_id) pair owns one long-lived consumer;
    fetch returns messages whose offsets stay uncommitted until ack/nack.
    """

    def __init__(self, bootstrap_servers: str) -> None:
        self.bootstrap_servers = bootstrap_servers
        self._producer: AIOKafkaProducer | None = None
        self._admin: AIOKafkaAdminClient | None = None
        self._lock = asyncio.Lock()
        self.stats = BrokerStats()
        self._consumers: dict[tuple[str, str], AIOKafkaConsumer] = {}

    async def start(self) -> None:
        async with self._lock:
            if self._producer is not None and self._producer._closed is False:
                return
            self._producer = AIOKafkaProducer(
                bootstrap_servers=self.bootstrap_servers,
                value_serializer=lambda v: json.dumps(v).encode("utf-8"),
                acks="all",
                enable_idempotence=True,
            )
            self._admin = AIOKafkaAdminClient(bootstrap_servers=self.bootstrap_servers)
            try:
                await self._producer.start()
                await self._admin.start()
                logger.info("Kafka connected", bootstrap=self.bootstrap_servers)
            except Exception as exc:
                self.stats.record_failure(f"startup: {exc}")
                await self._stop_unlocked()
                raise

    async def _stop_unlocked(self) -> None:
        for consumer in self._consumers.values():
            try:
                await asyncio.wait_for(consumer.stop(), timeout=5.0)
            except Exception:
                pass
        self._consumers.clear()
        if self._producer is not None:
            try:
                await self._producer.stop()
            except Exception:
                pass
            self._producer = None
        if self._admin is not None:
            try:
                await self._admin.close()
            except Exception:
                pass
            self._admin = None

    async def stop(self) -> None:
        async with self._lock:
            await self._stop_unlocked()

    @property
    def connected(self) -> bool:
        return self._producer is not None and getattr(self._producer, "_closed", True) is False

    async def ensure_topic(self, topic: str) -> bool:
        """Create the topic when missing. Returns True when it exists afterwards."""
        if self._admin is None:
            return False
        try:
            metadata = await self._admin.describe_topics([topic])
            if metadata:
                return True
        except Exception as exc:
            logger.warning("Topic describe failed", topic=topic, error=str(exc))
        try:
            await self._admin.create_topics([NewTopic(name=topic, num_partitions=1, replication_factor=1)])
            logger.info("Topic created", topic=topic)
            return True
        except Exception as exc:
            # Topic may have been created concurrently; treat as existing.
            logger.debug("Topic create returned", topic=topic, error=str(exc))
            return True

    async def publish(
        self,
        exchange: str,
        routing_key: str,
        message: dict[str, Any],
        retry_count: int = 3,
    ) -> dict[str, Any]:
        """Publish a message through the exchange binding.

        Returns partition/offset metadata on success, raises on final failure.
        """
        topic = topic_for(exchange, routing_key)
        await self.ensure_topic(topic)

        last_error: Exception | None = None
        for attempt in range(max(retry_count, 1)):
            try:
                if not self.connected:
                    await self.start()
                assert self._producer is not None
                meta = await self._producer.send_and_wait(topic, value=message)
                self.stats.record_publish()
                logger.debug(
                    "Message published",
                    topic=topic,
                    partition=meta.partition,
                    offset=meta.offset,
                )
                return {"partition": meta.partition, "offset": meta.offset}
            except KafkaError as exc:
                last_error = exc
                self.stats.record_failure(f"publish attempt {attempt + 1}: {exc}")
                await asyncio.sleep(min(2 ** attempt, 5))
        raise RuntimeError(f"Publish failed after retries: {last_error}") from last_error

    async def consume(
        self,
        queue: str,
        max_messages: int = 10,
        timeout_ms: int = 1000,
    ) -> list[dict[str, Any]]:
        """Read up to max_messages from a queue without committing offsets.

        Non-destructive peek semantics fit the monitoring use case; the Online
        ML Engine will run its own committed consumer group.
        """
        await self.ensure_topic(queue)

        def _deserialize(v: bytes | None) -> Any:
            return json.loads(v.decode("utf-8")) if v is not None else None

        # Ephemeral group per request so partitions get assigned immediately;
        # offsets are never committed, so reads stay non-destructive.
        # getmany() instead of `async for` — the iterator form ignores
        # consumer_timeout_ms and can hang on quiet topics.
        consumer = AIOKafkaConsumer(
            queue,
            bootstrap_servers=self.bootstrap_servers,
            auto_offset_reset="earliest",
            enable_auto_commit=False,
            group_id=f"broker-peek-{uuid.uuid4().hex[:8]}",
            value_deserializer=_deserialize,
        )
        messages: list[dict[str, Any]] = []
        try:
            await consumer.start()
            while len(messages) < max_messages:
                batch = await consumer.getmany(
                    timeout_ms=max(timeout_ms, 100),
                    max_records=max_messages - len(messages),
                )
                if not batch:
                    break
                for _tps, records in batch.items():
                    for msg in records:
                        payload = msg.value
                        if isinstance(payload, dict):
                            payload["_meta"] = {
                                "topic": msg.topic,
                                "partition": msg.partition,
                                "offset": msg.offset,
                            }
                        messages.append(payload)
                        self.stats.record_consume()
                        if len(messages) >= max_messages:
                            break
                    if len(messages) >= max_messages:
                        break
        finally:
            try:
                await asyncio.wait_for(consumer.stop(), timeout=5.0)
            except Exception:
                pass
        return messages

    # ------------------------------------------------------------------
    # SAS-07 consumer workflow: subscribe -> receive -> acknowledge
    # ------------------------------------------------------------------

    def dlq_topic(self, queue: str) -> str:
        return dlq_topic_for(queue)

    async def subscribe(self, queue: str, group_id: str, prefetch_count: int = 100) -> None:
        """Register a persistent consumer for (queue, group_id).

        Auto-commit stays off: offsets only move on ack()/nack().
        """
        await self.ensure_topic(queue)
        key = (queue, group_id)
        if key in self._consumers:
            return

        def _deserialize(v: bytes | None) -> Any:
            return json.loads(v.decode("utf-8")) if v is not None else None

        consumer = AIOKafkaConsumer(
            queue,
            bootstrap_servers=self.bootstrap_servers,
            auto_offset_reset="earliest",
            enable_auto_commit=False,
            max_poll_records=max(prefetch_count, 1),
            group_id=group_id,
            value_deserializer=_deserialize,
        )
        try:
            await consumer.start()
            # Force metadata + partition assignment now so the first fetch
            # does not return empty while the group is still rebalancing.
            for _ in range(20):
                if consumer.assignment():
                    break
                await asyncio.sleep(0.1)
        except Exception:
            try:
                await consumer.stop()
            except Exception:
                pass
            raise
        self._consumers[key] = consumer
        logger.info(
            "Consumer subscribed",
            queue=queue,
            group=group_id,
            partitions=sorted(str(tp) for tp in consumer.assignment()),
        )

    def _get_consumer(self, queue: str, group_id: str) -> AIOKafkaConsumer:
        consumer = self._consumers.get((queue, group_id))
        if consumer is None:
            raise KeyError(f"No subscription for queue='{queue}' group='{group_id}'")
        return consumer

    @staticmethod
    def _tp(topic: str, partition: int) -> TopicPartition:
        return TopicPartition(topic, partition)

    async def fetch(
        self,
        queue: str,
        group_id: str,
        max_messages: int = 10,
        timeout_ms: int = 1000,
    ) -> list[dict[str, Any]]:
        """Receive up to max_messages without committing their offsets.

        Each message carries a delivery_tag that must be passed to ack()
        or nack() afterwards.
        """
        consumer = self._get_consumer(queue, group_id)
        batch = await consumer.getmany(
            timeout_ms=max(timeout_ms, 100),
            max_records=max(max_messages, 1),
        )
        messages: list[dict[str, Any]] = []
        for _tps, records in batch.items():
            for msg in records:
                payload = msg.value if isinstance(msg.value, dict) else {"value": msg.value}
                payload["_delivery"] = {
                    "delivery_tag": f"{msg.topic}:{msg.partition}:{msg.offset}",
                    "topic": msg.topic,
                    "partition": msg.partition,
                    "offset": msg.offset,
                    "queue": queue,
                    "group_id": group_id,
                }
                messages.append(payload)
                self.stats.record_consume()
                if len(messages) >= max_messages:
                    break
            if len(messages) >= max_messages:
                break
        return messages

    async def ack(self, queue: str, group_id: str, delivery_tag: str) -> dict[str, Any]:
        """Commit the offset of a delivered message — acknowledgement."""
        topic, partition_s, offset_s = delivery_tag.split(":")
        consumer = self._get_consumer(queue, group_id)
        tp = self._tp(topic, int(partition_s))
        consumer.seek(tp, int(offset_s) + 1)
        await consumer.commit({tp: int(offset_s) + 1})
        return {"acknowledged": True, "delivery_tag": delivery_tag}

    async def nack(
        self,
        queue: str,
        group_id: str,
        delivery_tag: str,
        requeue: bool = False,
        reason: str = "",
    ) -> dict[str, Any]:
        """Negative acknowledgement.

        requeue=True  -> seek back so the message redelivers to the group.
        requeue=False -> copy the message into the dead letter topic and
                         commit past it.
        """
        topic, partition_s, offset_s = delivery_tag.split(":")
        partition, offset = int(partition_s), int(offset_s)
        consumer = self._get_consumer(queue, group_id)
        tp = self._tp(topic, partition)

        if not requeue:
            payload = await self._read_raw(topic, partition, offset)
            dead_letter = {**(payload or {}), "_dead_letter": {
                "source_topic": topic,
                "partition": partition,
                "offset": offset,
                "reason": reason or "rejected",
                "failed_at": datetime.now(timezone.utc).isoformat(),
            }}
            await self.publish_to(dlq_topic_for(queue), dead_letter)

        # requeue=True rewinds to the same offset so the group redelivers it;
        # dead-lettering commits past the failed message.
        resume_offset = offset if requeue else offset + 1
        consumer.seek(tp, resume_offset)
        await consumer.commit({tp: resume_offset})
        result = {"nacked": True, "delivery_tag": delivery_tag, "requeued": requeue}
        if not requeue:
            result["dlq_topic"] = dlq_topic_for(queue)
        return result

    async def _read_raw(self, topic: str, partition: int, offset: int) -> Any:
        """Read one raw record for dead-lettering without touching groups."""

        def _sync_read() -> Any:
            import json as _json
            from kafka import KafkaConsumer as SyncKafkaConsumer
            from kafka.structs import TopicPartition as SyncTP

            consumer = SyncKafkaConsumer(bootstrap_servers=self.bootstrap_servers)
            try:
                tp = SyncTP(topic, partition)
                consumer.assign([tp])
                consumer.seek(tp, offset)
                records = consumer.poll(timeout_ms=2000, max_records=1)
                for msgs in records.values():
                    for rec in msgs:
                        if rec.value is None:
                            return None
                        return _json.loads(rec.value.decode("utf-8"))
                return None
            finally:
                consumer.close()

        try:
            return await asyncio.to_thread(_sync_read)
        except Exception as exc:
            logger.warning("Dead letter read failed", topic=topic, offset=offset, error=str(exc))
            return None

    async def publish_to(self, topic: str, message: dict[str, Any]) -> dict[str, Any]:
        """Publish directly to a topic (used for dead letter routing)."""
        await self.ensure_topic(topic)
        if not self.connected:
            await self.start()
        assert self._producer is not None
        meta = await self._producer.send_and_wait(topic, value=message)
        self.stats.record_publish()
        return {"partition": meta.partition, "offset": meta.offset}

    async def active_consumer_count(self) -> int:
        return len(self._consumers)

    async def unsubscribe(self, queue: str, group_id: str) -> bool:
        """Stop and drop a subscription. Returns True when it existed."""
        key = (queue, group_id)
        consumer = self._consumers.pop(key, None)
        if consumer is None:
            return False
        try:
            await asyncio.wait_for(consumer.stop(), timeout=5.0)
        except Exception:
            pass
        logger.info("Consumer unsubscribed", queue=queue, group=group_id)
        return True

    async def queue_size(self, topic: str) -> int | None:
        """Approximate backlog for a topic across all partitions."""
        def _sync_queue_size(t: str) -> int | None:
            from kafka import KafkaConsumer as SyncKafkaConsumer
            from kafka.structs import TopicPartition

            consumer = SyncKafkaConsumer(bootstrap_servers=self.bootstrap_servers)
            try:
                partitions = consumer.partitions_for_topic(t)
                if not partitions:
                    return None
                tps = [TopicPartition(t, p) for p in partitions]
                beginning = consumer.beginning_offsets(tps)
                end = consumer.end_offsets(tps)
                return sum(end[tp] - beginning[tp] for tp in tps)
            finally:
                consumer.close()

        try:
            return await asyncio.to_thread(_sync_queue_size, topic)
        except Exception as exc:
            logger.debug("queue_size failed", topic=topic, error=str(exc))
            return None

    async def topic_bindings(self, exchange: str) -> list[str]:
        """List known queues bound under an exchange prefix."""
        topics = await self.list_topics()
        prefix = f"{exchange.lower()}{_BINDING_SEPARATOR}"
        return sorted(t[len(prefix):] for t in topics if t.startswith(prefix))

    async def list_topics(self) -> list[str]:
        if self._admin is None:
            return []
        try:
            return sorted(await self._admin.list_topics())
        except Exception as exc:
            logger.debug("list_topics failed", error=str(exc))
            return []

    async def close_consumer_client(self) -> None:
        pass
