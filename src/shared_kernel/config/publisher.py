import topology

import aio_pika


async def declare_topology(connection: aio_pika.Connection):
    """
    Declares topology of RabbitMQ based on `topology.py`

    All operations done are idempotent
    """

    async with connection:
        channel = await connection.channel()

        for exchange in topology.EXCHANGES.values():
            await channel.declare_exchange(
                name=exchange.name, type=exchange.type, durable=exchange.durable
            )

        declared_queues = {}

        for binding in topology.BINDINGS:
            if binding.queue.name not in declared_queues:
                queue = await channel.declare_queue(
                    name=binding.queue.name,
                    durable=binding.queue.durable,
                    arguments=binding.queue.arguments,
                )

                declared_queues[binding.queue.name] = queue

            await declared_queues[binding.queue.name].bind(
                exchange=binding.exchange.name,
                routing_key=binding.routing_key,
            )
