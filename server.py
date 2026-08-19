import asyncio
from asyncua import Client, Server, ua

server_address = "opc.tcp://localhost:4840"

async def main():
    url = server_address
    async with Client(url=url) as client:
        node = client.get_node("ns=2;i=10")
        value = await node.read_value()

if __name__ == "__main__":
    asyncio.run(main()) 
    