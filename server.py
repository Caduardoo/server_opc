import asyncio
import logging
import os
import math

from asyncua import Server, ua

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

    padim_ns = await server.get_namespace_index("http://opcfoundation.org/UA/PADIM/")
    di_ns = await server.get_namespace_index("http://opcfoundation.org/UA/DI/")
    app_ns = await server.register_namespace("urn:opas:plant:demo")

    padim_type_node = server.get_node(ua.NodeId(1009, padim_ns))
    analog_signal_type = server.get_node(ua.NodeId(1022, padim_ns))

    objects_folder = server.nodes.objects
    transmitter = await objects_folder.add_object(
        ua.NodeId("FT_101_Transmitter", app_ns),
        "FT_101_FlowTransmitter",
        objecttype=padim_type_node
    )
    
    mfr_node = await transmitter.get_child([f"{di_ns}:Manufacturer"])
    await mfr_node.write_value(ua.LocalizedText("Open Process Automation UFCG Demo Corp"))
    
    model_node = await transmitter.get_child([f"{di_ns}:Model"])
    await model_node.write_value(ua.LocalizedText("O-PAS Flow Sensor v1.0"))

    flow_signal = await transmitter.add_object(
        ua.NodeId("FT_101_Flow_PV", app_ns),
        "FlowRate_PV",
        objecttype=analog_signal_type
    )
    
    pv_value_node = await flow_signal.add_variable(
        ua.NodeId("FT_101_Flow_PV_ActualValue", app_ns),
        "ActualValue",
        0.0,
        varianttype=ua.VariantType.Float
    )

    async with server:
        _logger.info(f"O-PAS Server started at: {server_endpoint}")
        _logger.info("Press Ctrl+C to end process")
        step = 0.0
        
        while True:
            simulated_pv = 50.0 + 10.0 * math.sin(step)
            await pv_value_node.write_value(float(simulated_pv), ua.VariantType.Float)
            step += 0.2
            await asyncio.sleep(1)

if __name__ == "__main__":
    asyncio.run(main()) 
    