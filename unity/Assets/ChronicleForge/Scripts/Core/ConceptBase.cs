// What all three concepts share: the session, the keyboard, and the focus.
//
// A concept subclass decides what a phase LOOKS like. It never decides what a
// phase IS, what may be attributed, or what a key does — those are here, once,
// so that comparing the three compares presentation and nothing else.

using System;
using ChronicleForge.Model;
using UnityEngine;
using UnityEngine.UIElements;

namespace ChronicleForge.Core
{
    [RequireComponent(typeof(UIDocument))]
    public abstract class ConceptBase : MonoBehaviour
    {
        public DvsSession Session { get; private set; }
        protected VisualElement Root;

        /// Where focus should land after this render. A view change that leaves
        /// focus on the document body strands a keyboard reader at the top of
        /// the page and makes the next Tab start over.
        protected VisualElement FocusAfterRender;

        public abstract string ConceptName { get; }

        protected virtual void OnEnable()
        {
            var doc = GetComponent<UIDocument>();
            Root = doc.rootVisualElement;
            Root.focusable = true;

            try
            {
                Session = new DvsSession(FixtureLoader.Load());
            }
            catch (Exception exc)
            {
                // Fail visibly. A concept that silently rendered an empty page
                // would look like a design choice.
                Root.Clear();
                Root.Bg(new Color(0.1f, 0.02f, 0.02f));
                Root.Put(UiKit.Text($"fixture error: {exc.Message}", 18, Color.white)
                             .Pad(24, 24, 24, 24));
                Debug.LogError($"[{ConceptName}] {exc}");
                return;
            }

            Root.RegisterCallback<KeyDownEvent>(OnKey);
            // Start on the shelf. Opening the book is the reader's first act,
            // not something that happens to them on load.
            Rebuild();
        }

        /// Clears and rebuilds the tree, then puts focus where the concept asked.
        public void Rebuild()
        {
            if (Session == null) return;
            FocusAfterRender = null;
            Root.Clear();
            Render();
            // Deferred: an element cannot take focus until it has been laid out.
            Root.schedule.Execute(() =>
            {
                VisualElement target = FocusAfterRender ?? Root;
                target.Focus();
            }).StartingIn(0);
        }

        protected abstract void Render();

        // -- keyboard ----------------------------------------------------------

        /// One key map for all three concepts. Every affordance a mouse has is
        /// reachable from here; a concept that needed its own key would be a
        /// concept with an affordance the other two cannot be compared against.
        private void OnKey(KeyDownEvent e)
        {
            if (Session == null) return;
            bool handled = true;
            switch (e.keyCode)
            {
                case KeyCode.Return:
                case KeyCode.KeypadEnter:
                case KeyCode.Space:
                    Primary();
                    break;
                case KeyCode.Escape:
                    Secondary();
                    break;
                case KeyCode.Alpha1: SelectOrInspect(1); break;
                case KeyCode.Alpha2: SelectOrInspect(2); break;
                case KeyCode.Alpha3: SelectOrInspect(3); break;
                default:
                    handled = false;
                    break;
            }
            if (handled)
            {
                e.StopPropagation();
                Rebuild();
            }
        }

        /// Enter: seal if a juncture is answered, walk the path if tracing,
        /// otherwise turn the page.
        protected virtual void Primary()
        {
            switch (Session.Phase)
            {
                case Phase.Shelf:
                    Session.Open();
                    break;
                case Phase.Juncture:
                    Session.Seal();
                    break;
                case Phase.Trace:
                    // Walk back one real edge, and at the origin, confirm.
                    if (Session.TraceAtOrigin) Session.ConfirmTrace();
                    else Session.TraceStep();
                    break;
                default:
                    Session.Advance();
                    break;
            }
        }

        protected virtual void Secondary()
        {
            if (Session.Phase == Phase.Trace) Session.CloseTrace();
        }

        protected virtual void SelectOrInspect(int n)
        {
            if (Session.Phase == Phase.Juncture) Session.Select(n);
            else if (Session.Phase == Phase.Closing) Session.OpenTrace(n - 1);
        }

        // -- scripted control --------------------------------------------------

        /// Drive the session from outside (tests, the capture walker, MCP
        /// execute_code). Every verb here is one the keyboard already has, so
        /// a scripted walk exercises exactly the path a reader would.
        public void Drive(string verb)
        {
            if (Session == null) return;
            string[] parts = verb.Split(':');
            int n = parts.Length > 1 && int.TryParse(parts[1], out int v) ? v : 0;
            switch (parts[0])
            {
                case "open": Session.Open(); break;
                case "advance": Session.Advance(); break;
                case "select": Session.Select(n); break;
                case "seal": Session.Seal(); break;
                case "recognise": Session.ConfirmRecognition(); break;
                case "mark":
                    if (Session.CurrentAftermath is { } a && a.Hardened.Count > n)
                        Session.ConfirmMark(a.Hardened[n]);
                    break;
                case "trace": Session.OpenTrace(n); break;
                case "step": Session.TraceStep(); break;
                case "confirm": Session.ConfirmTrace(); break;
                case "close": Session.CloseTrace(); break;
                case "primary": Primary(); break;
            }
            Rebuild();
        }

        // -- shared, gated readings -------------------------------------------

        /// What a hardened mark may say right now. Never returns a blank where a
        /// name would go: an unearned mark says that something gained a name.
        protected string MarkCaption(Mark m)
        {
            int? founder = Session.Gate.FounderOf(m);
            return founder.HasValue ? Voice.MarkOwner(founder.Value) : Voice.MarkUnattributed;
        }

        /// The colour a coordinate is allowed to wear. 朱 only once confirmed.
        protected Color InkFor(string coordRef) =>
            Session.Gate.MayUseVermilion(coordRef) ? UiKit.Vermilion : UiKit.InkSoft;
    }
}
