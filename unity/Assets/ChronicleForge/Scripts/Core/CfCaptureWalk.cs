// Walk one concept through the DVS chain and photograph each beat.
//
// Attached at runtime (by the capture driver, over MCP execute_code) to the
// scene's concept object. It drives the session only through Drive(), so the
// pictures are of states a reader can actually reach by the same verbs.
//
// Output: <dir>/<concept>-<nn>-<state>.png, one per required beat.

using System.Collections;
using System.IO;
using UnityEngine;
using UnityEngine.UIElements;

namespace ChronicleForge.Core
{
    public sealed class CfCaptureWalk : MonoBehaviour
    {
        public string Dir = "C:/Users/shiny/cf-shots";
        public string Tag = "x";
        public int Width = 1600, Height = 900;
        public static bool Done;

        // The panel is rendered into this texture rather than the Game view,
        // so a capture does not depend on there being a focused window — or any
        // window: it works the same in a batchmode Editor.
        private RenderTexture _rt;
        private Texture2D _tex;

        // Seed 1, beat by beat (see the fixture): the first aftermath hardens
        // nothing, the second hardens eight marks, and the third life's first
        // juncture carries the recognition. "seal" needs the recorded option
        // selected first — selection is not commitment, so it is its own verb.
        private static readonly (string state, string[] verbs)[] Script =
        {
            ("01-opening",             new string[0]),
            ("02-life",                new[] { "primary" }),
            ("03-juncture",            new[] { "primary" }),
            ("04-choice",              new[] { "select:1" }),
            ("05-sealed",              new[] { "seal" }),
            ("06-death",               new[] { "primary" }),
            ("07-years",               new[] { "primary" }),
            ("08-return-digest",       new[] { "primary" }),
            ("09-mark-unconfirmed",    new[] { "primary", "primary", "select:1", "seal",
                                               "primary", "select:1", "seal",
                                               "primary", "select:1", "seal",
                                               "primary", "primary", "primary" }),
            ("10-mark-confirmed",      new[] { "mark:0" }),
            ("11-recognition-hidden",  new[] { "primary", "primary", "select:1" }),
            ("12-recognition-confirmed", new[] { "recognise" }),
            ("13-ending",              new[] { "seal", "primary", "select:1", "seal",
                                               "primary", "select:1", "seal",
                                               "primary", "select:1", "seal",
                                               "primary", "primary", "primary", "primary" }),
            ("14-investigation",       new[] { "trace:0" }),
            ("15-trace-deeper",        new[] { "step" }),
            // seed 1's paths are consequence -> one intermediate -> origin, so
            // the second step arrives; extra steps are ignored at the end.
            ("16-confirmation",        new[] { "step", "step", "confirm" }),
        };

        /// A batchmode Editor never repaints runtime panels on its own — there
        /// is no camera pass to hang the repaint on — so the walker asks the
        /// internal utility to paint every offscreen (target-texture) panel now.
        /// ponytail: reflection on an internal; pin to the Unity version.
        private static void RepaintOffscreen()
        {
            var t = typeof(UIDocument).Assembly.GetType("UnityEngine.UIElements.UIElementsRuntimeUtility");
            const System.Reflection.BindingFlags F =
                System.Reflection.BindingFlags.Static | System.Reflection.BindingFlags.NonPublic
                | System.Reflection.BindingFlags.Public;
            t?.GetMethod("UpdateRuntimePanels", F)?.Invoke(null, null);
            t?.GetMethod("RepaintOffscreenPanels", F)?.Invoke(null, null);
        }

        private IEnumerator Start()
        {
            Done = false;
            Directory.CreateDirectory(Dir);
            var concept = GetComponent<ConceptBase>();
            if (concept == null) { Debug.LogError("[CfCaptureWalk] no concept here"); yield break; }

            var doc = GetComponent<UIDocument>();
            // A runtime copy: assigning a target texture to the shared asset
            // would dirty it and leak into the next Editor session.
            var panel = Instantiate(doc.panelSettings);
            _rt = new RenderTexture(Width, Height, 24);
            panel.targetTexture = _rt;
            panel.scaleMode = PanelScaleMode.ConstantPixelSize;
            doc.panelSettings = panel;
            _tex = new Texture2D(Width, Height, TextureFormat.RGB24, false);

            // Let the first frame lay out before the first picture.
            yield return null; yield return null;

            foreach (var (state, verbs) in Script)
            {
                foreach (string v in verbs)
                {
                    // Walking past the closing is harmless; Drive ignores what
                    // the phase refuses, which is exactly what a key press does.
                    concept.Drive(v);
                    yield return null;
                }
                // Two frames: one for layout, one for the fade to land.
                yield return null; yield return new WaitForSecondsRealtime(0.45f);
                string file = $"{Dir}/{Tag}-{state}-{concept.Session.Phase.ToString().ToLower()}.png";
                // Plain frame waits: WaitForEndOfFrame never fires in a batchmode
                // Editor, and the panel repaints into its texture during the
                // player loop regardless of whether a window exists.
                yield return null; yield return null;
                RepaintOffscreen();
                RenderTexture.active = _rt;
                _tex.ReadPixels(new Rect(0, 0, Width, Height), 0, 0);
                _tex.Apply();
                RenderTexture.active = null;
                File.WriteAllBytes(file, _tex.EncodeToPNG());
                Debug.Log($"[CfCaptureWalk] {file}");
            }
            Done = true;
            Debug.Log("[CfCaptureWalk] done");
        }
    }
}
