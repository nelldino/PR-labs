import asyncio
import websockets

connected_clients = set()

async def handle_client(websocket, path):
    # Register the new client
    connected_clients.add(websocket)
    try:
        async for message in websocket:
            # Broadcast the message to all connected clients
            await asyncio.wait([asyncio.create_task(client.send(message)) for client in connected_clients])
    finally:
        # Unregister the client
        connected_clients.remove(websocket)

async def notify_users(message):
    if connected_clients:  # asyncio.wait doesn't accept an empty list
        await asyncio.wait([client.send(message) for client in connected_clients])
async def main():
    server = await websockets.serve(handle_client, "localhost", 6789)
    await server.wait_closed()

if __name__ == "__main__":
    asyncio.run(main())
