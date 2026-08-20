import asyncio
import logging
import os

from asyncua import Server

logging.basicConfig(level=logging.INFO)
_logger = logging.getLogger("OPAS_Server")

server_endpoint = "opc.tcp://localhost:4840/opas/server/"

async def main():
    server = Server()
    await server.init()

    server.set_endpoint(server_endpoint)
    server.set_server_name("O-PAS Test Server")

    base_dir = os.path.dirname(os.path.abspath(__file__))
    nodeset_dir = os.path.join(base_dir, "nodeset-opas")

    nodeset_files = [
        "Opc.Ua.Di.NodeSet2.xml",
        "Opc.Ua.IRDI.NodeSet2.xml",
        "Opc.Ua.PADIM.NodeSet2.xml",
        "OPAS_P4.xml",
        "OPAS_P6_2.xml",
        "OPAS_P6_4.xml",
        "OPAS_P6_6.xml",
    ]

    nodeset_dir = os.path.join(base_dir, "nodeset-opas")

    _logger.info("Importing O-PAS models...")

    for nodeset in nodeset_files:
        file_path = os.path.join(nodeset_dir, nodeset)

        if not os.path.exists(file_path):
            _logger.error(f"Path not found: {file_path}")
            continue
        
        try:
            _logger.info(f"Loading: {nodeset}")
            await server.import_xml(file_path)
            _logger.info(f"{nodeset} loaded.")
        except FileNotFoundError:
            _logger.warning(f"File {nodeset} not found.")
        except Exception as e:
            _logger.error(f"Error importing {nodeset}: {e}")

    async with server:
        _logger.info(f"O-PAS Server started at: {server_endpoint}")
        _logger.info("Press Ctrl+C to end process")

        while True:
            await asyncio.sleep(1)

if __name__ == "__main__":
    asyncio.run(main()) 
    