// Start the MCP bridge when the Editor loads.
//
// The MCP for Unity window has a "Start Bridge" button; this project is driven
// from outside the Editor, where there is nobody to click it.
//
// It calls StdioBridgeHost.Start() rather than the higher-level
// IBridgeControlService.StartAsync(): that service resolves a *preferred*
// transport which defaults to HTTP, while the MCP server this project talks to
// runs in stdio mode and discovers editors by the port file the stdio host
// writes. Starting the matching host is what makes the two find each other —
// going through the service brought an HTTP transport up and left the server
// reporting "No Unity Editor instances found".

using MCPForUnity.Editor.Services.Transport.Transports;
using UnityEditor;
using UnityEngine;

namespace ChronicleForge.EditorTools
{
    [InitializeOnLoad]
    public static class CfBridgeBoot
    {
        static CfBridgeBoot()
        {
            // Deferred: the host touches editor services that are not ready
            // while the static constructor itself is running.
            EditorApplication.delayCall += Start;
        }

        [MenuItem("Chronicle Forge/Start MCP bridge")]
        public static void Start()
        {
            try
            {
                StdioBridgeHost.Start();
                Debug.Log($"[CfBridgeBoot] stdio bridge on port {StdioBridgeHost.GetCurrentPort()}");
            }
            catch (System.Exception exc)
            {
                // Never take the Editor down over this: the concepts run fine
                // without a bridge, it is only the remote control that is lost.
                Debug.LogWarning($"[CfBridgeBoot] could not start bridge: {exc.Message}");
            }
        }
    }
}
