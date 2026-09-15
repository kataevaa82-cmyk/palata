import bpy


def start_mcp_server():
    scene = bpy.context.scene
    scene.blendermcp_port = 9876
    if not getattr(scene, "blendermcp_server_running", False):
        bpy.ops.blendermcp.start_server()
    return None


bpy.app.timers.register(start_mcp_server, first_interval=1.0)
