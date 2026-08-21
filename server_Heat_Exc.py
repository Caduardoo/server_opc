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
        "HX-100.NodeSet2.xml",
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

    hx_ns = await server.get_namespace_index("http://example.org/opcua/HX-100")

    tube_inlet_temp_node  = server.get_node(ua.NodeId(6000, hx_ns))
    tube_outlet_temp_node = server.get_node(ua.NodeId(6010, hx_ns))
    shell_inlet_temp_node = server.get_node(ua.NodeId(6020, hx_ns))
    shell_outlet_temp_node= server.get_node(ua.NodeId(6030, hx_ns))
    tube_flow_node        = server.get_node(ua.NodeId(6040, hx_ns))
    shell_flow_node       = server.get_node(ua.NodeId(6050, hx_ns))
    tube_dp_node          = server.get_node(ua.NodeId(6060, hx_ns))
    shell_dp_node         = server.get_node(ua.NodeId(6070, hx_ns))
    heat_duty_node        = server.get_node(ua.NodeId(6080, hx_ns))
    fouling_node          = server.get_node(ua.NodeId(6090, hx_ns))
    sp_node               = server.get_node(ua.NodeId(6100, hx_ns))
    mode_node             = server.get_node(ua.NodeId(6110, hx_ns))

    mode = 1  # 0: Offline, 1: InService, 2: Bypass
    fouling = 8.0
    await mode_node.write_value(ua.DataValue(ua.Variant(mode, ua.VariantType.Int32)))

    async with server:
        _logger.info("Started O-PAS Server, press Ctrl+C to stop.")
        step = 0.0
        
        while True:
            sp_val = await sp_node.read_value()

            noise = 0.5 * math.sin(step * 3)
            tube_inlet = 180.0 + 2.0 * math.sin(step) + noise
            shell_inlet = 30.0 + 1.0 * math.cos(step)
            tube_flow = 140.0 + 5.0 * math.sin(step * 0.5)

            if mode == 1:  # InService
                fouling = min(100.0, fouling + 0.005)
                
                target_shell_flow = max(20.0, min(280.0, 180.0 + (100.0 - sp_val) * 3.5))
                shell_flow = target_shell_flow + noise * 2

                tube_outlet = sp_val + noise
                shell_outlet = shell_inlet + (tube_inlet - tube_outlet) * (tube_flow / max(shell_flow, 1.0)) * 0.4
                
                heat_duty = max(0.0, (tube_inlet - tube_outlet) * tube_flow * 0.27)

                tube_dp = 25.0 + (tube_flow / 140.0) * 10.0 + (fouling * 0.4)
                shell_dp = 15.0 + (shell_flow / 180.0) * 13.0

            elif mode == 2:  # Bypass
                tube_outlet = tube_inlet
                shell_flow = 0.0
                shell_outlet = shell_inlet
                heat_duty = 0.0
                tube_dp = 5.0
                shell_dp = 0.0
                fouling = max(0.0, fouling - 0.1) 
            else:  # Offline
                tube_outlet = 25.0
                shell_outlet = 25.0
                tube_flow = 0.0
                shell_flow = 0.0
                heat_duty = 0.0
                tube_dp = 0.0
                shell_dp = 0.0

            await tube_inlet_temp_node.write_value(ua.DataValue(ua.Variant(float(tube_inlet), ua.VariantType.Double)))
            await tube_outlet_temp_node.write_value(ua.DataValue(ua.Variant(float(tube_outlet), ua.VariantType.Double)))
            await shell_inlet_temp_node.write_value(ua.DataValue(ua.Variant(float(shell_inlet), ua.VariantType.Double)))
            await shell_outlet_temp_node.write_value(ua.DataValue(ua.Variant(float(shell_outlet), ua.VariantType.Double)))
            await tube_flow_node.write_value(ua.DataValue(ua.Variant(float(tube_flow), ua.VariantType.Double)))
            await shell_flow_node.write_value(ua.DataValue(ua.Variant(float(shell_flow), ua.VariantType.Double)))
            await tube_dp_node.write_value(ua.DataValue(ua.Variant(float(tube_dp), ua.VariantType.Double)))
            await shell_dp_node.write_value(ua.DataValue(ua.Variant(float(shell_dp), ua.VariantType.Double)))
            await heat_duty_node.write_value(ua.DataValue(ua.Variant(float(heat_duty), ua.VariantType.Double)))
            await fouling_node.write_value(ua.DataValue(ua.Variant(float(fouling), ua.VariantType.Double)))

            step += 0.05
            await asyncio.sleep(0.25)

if __name__ == "__main__":
    asyncio.run(main()) 
    