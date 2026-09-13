// Builds the three concept scenes from script.
//
// Authored here rather than by hand because .unity and .asset files are YAML
// with GUID cross-references: writing them by hand from outside the Editor is
// how you get a scene that opens empty. Running this is idempotent — it is the
// definition of the scenes, not a one-off migration.
//
//   Unity.exe -batchmode -quit -executeMethod ChronicleForge.EditorTools.CfSetup.BuildAll

using System.IO;
using ChronicleForge.Concepts;
using UnityEditor;
using UnityEditor.SceneManagement;
using UnityEngine;
using UnityEngine.UIElements;

namespace ChronicleForge.EditorTools
{
    public static class CfSetup
    {
        private const string Root = "Assets/ChronicleForge";
        private const string ScenesDir = Root + "/Scenes";
        private const string PanelAsset = Root + "/UI/CfPanelSettings.asset";

        [MenuItem("Chronicle Forge/Build concept scenes")]
        public static void BuildAll()
        {
            PanelSettings panel = EnsurePanel();
            Build<ConceptA>("ConceptA", panel);
            Build<ConceptB>("ConceptB", panel);
            Build<ConceptC>("ConceptC", panel);
            AssetDatabase.SaveAssets();
            AssetDatabase.Refresh();
            Debug.Log("[CfSetup] three concept scenes built");
        }

        private static PanelSettings EnsurePanel()
        {
            Directory.CreateDirectory(Root + "/UI");
            var panel = AssetDatabase.LoadAssetAtPath<PanelSettings>(PanelAsset);
            if (panel == null)
            {
                panel = ScriptableObject.CreateInstance<PanelSettings>();
                AssetDatabase.CreateAsset(panel, PanelAsset);
            }
            // Scale with the window rather than snapping to a fixed size: the
            // concepts are compared at several desktop aspect ratios, and a
            // constant-pixel panel would letterbox instead of reflowing.
            panel.scaleMode = PanelScaleMode.ScaleWithScreenSize;
            panel.referenceResolution = new Vector2Int(1600, 900);
            panel.screenMatchMode = PanelScreenMatchMode.MatchWidthOrHeight;
            panel.match = 0.5f;
            EditorUtility.SetDirty(panel);
            AssetDatabase.SaveAssets();
            // Re-read the asset. The instance CreateAsset was given is replaced
            // by the imported one on the first save/import cycle; holding the
            // original across three scene saves left scenes two and three with
            // a null panel reference (m_PanelSettings: {fileID: 0}).
            return AssetDatabase.LoadAssetAtPath<PanelSettings>(PanelAsset);
        }

        private static void Build<T>(string sceneName, PanelSettings panel) where T : MonoBehaviour
        {
            Directory.CreateDirectory(ScenesDir);
            var scene = EditorSceneManager.NewScene(NewSceneSetup.EmptyScene, NewSceneMode.Single);

            var camera = new GameObject("Camera", typeof(Camera));
            camera.GetComponent<Camera>().clearFlags = CameraClearFlags.SolidColor;
            camera.GetComponent<Camera>().backgroundColor = Color.black;

            var go = new GameObject(sceneName, typeof(UIDocument));
            var doc = go.GetComponent<UIDocument>();
            // Through the serialized field, not the property. NOTE: a batchmode
            // Editor still serialises this as {fileID: 0} — UIDocument clears the
            // reference when it cannot create a runtime panel — so BuildAll is
            // only trustworthy from the menu in a GUI Editor. The committed scene
            // files carry the reference; if one ever shows {fileID: 0}, this is
            // why. ponytail: patch the YAML after save if batchmode builds matter.
            var so = new SerializedObject(doc);
            so.FindProperty("m_PanelSettings").objectReferenceValue = panel;
            so.ApplyModifiedPropertiesWithoutUndo();
            go.AddComponent<T>();

            string path = $"{ScenesDir}/{sceneName}.unity";
            EditorSceneManager.SaveScene(scene, path);

            // Every concept is in the build list so a Play Mode run can switch
            // between them without re-opening the Editor.
            var list = new System.Collections.Generic.List<EditorBuildSettingsScene>(
                EditorBuildSettings.scenes);
            if (!list.Exists(s => s.path == path))
                list.Add(new EditorBuildSettingsScene(path, true));
            EditorBuildSettings.scenes = list.ToArray();
        }
    }
}
