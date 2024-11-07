import asyncio

import websockets
import json
# Store room information
rooms = {}

async def handle_client(websocket, path):
    user_room = None
    try:
        async for message in websocket:
            print(f"Received message: {message}")
            try:
                data = json.loads(message)
            except json.JSONDecodeError:
                await websocket.send("Invalid message format.")
                continue

            command = data.get("command")
            username = data.get("username")
            room = data.get("room")

            # Join Room
            if command == "join":
                if room not in rooms:
                    rooms[room] = set()
                rooms[room].add(websocket)
                user_room = room
                await broadcast(room, f"{username} has joined the room.")

            # Send Message
            elif command == "message" and room == user_room:
                await broadcast(room, f"{username}: {data['message']}")
            elif command == "message" and room != user_room:
                await websocket.send("You need to join a room first to send messages.")

            # Leave Room
            elif command == "leave" and room == user_room:
                rooms[room].remove(websocket)
                await broadcast(room, f"{username} has left the room.")
                if not rooms[room]:
                    del rooms[room]
                break
            else:
                await websocket.send("Unknown command or you are not in the specified room.")
    finally:
        if user_room and websocket in rooms.get(user_room, set()):
            rooms[user_room].remove(websocket)

async def broadcast(room, message):
    if room in rooms:
        tasks = [asyncio.create_task(client.send(message)) for client in rooms[room]]
        await asyncio.gather(*tasks)

async def websocket_server():
    async with websockets.serve(handle_client, "localhost", 6790):
        await asyncio.Future()  # Run forever


if __name__ == "__main__":
    asyncio.run(websocket_server())
