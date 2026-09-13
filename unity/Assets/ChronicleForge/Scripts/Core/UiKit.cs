// Small helpers so three concepts can be built in C# without three copies of
// the same twenty lines of style plumbing.
//
// Built in code rather than UXML/USS on purpose: the whole project is authored
// from outside the Editor, and a tree built in C# has no GUIDs to go stale and
// no import step between writing it and running it.
//
// 朱 IS DEFINED ONCE, HERE. Vermilion means a confirmed past-life connection and
// nothing else. If a second definition ever appears in a concept file, that is
// the bug: it is the one colour in this client that carries a claim.

using UnityEngine;
using UnityEngine.UIElements;

namespace ChronicleForge.Core
{
    public static class UiKit
    {
        // The one claim-bearing colour. Confirmed past-life connection only.
        public static readonly Color Vermilion = new Color(0.76f, 0.15f, 0.17f);
        // Everything unconfirmed wears ink, never 朱.
        public static readonly Color Ink = new Color(0.10f, 0.10f, 0.11f);
        public static readonly Color InkSoft = new Color(0.36f, 0.35f, 0.34f);
        public static readonly Color InkFaint = new Color(0.58f, 0.57f, 0.55f);

        /// One lever for the whole client. The first captures at 1600x900 read
        /// as a document seen from across the room: the sizes below were chosen
        /// for a browser page, and a game frame needs roughly 1.7x that to put
        /// a focal object in front of the reader at 292px.
        public const float TypeScale = 1.7f;

        private static Font _serif;

        public static Font Serif =>
            _serif != null ? _serif : _serif = Resources.Load<Font>("NotoSerifJP");

        /// Apply the book's face. Through unityFontDefinition, not unityFont:
        /// in UI Toolkit 2022.2+ the definition takes precedence, and the panel's
        /// default definition is always set — so a bare unityFont is silently
        /// ignored and the page renders in a face with no Japanese glyphs.
        public static T Face<T>(this T el) where T : VisualElement
        {
            if (Serif != null) el.style.unityFontDefinition = FontDefinition.FromFont(Serif);
            return el;
        }

        public static T Named<T>(this T el, string name) where T : VisualElement
        {
            el.name = name;
            return el;
        }

        /// Add a child AND return it, so a tree can be built by chaining.
        /// Named Put rather than Add because VisualElement.Add is an instance
        /// method returning void, and C# prefers it over any extension.
        public static T Put<T>(this VisualElement parent, T child) where T : VisualElement
        {
            parent.Add(child);
            return child;
        }

        public static VisualElement Box(FlexDirection dir = FlexDirection.Column)
        {
            var e = new VisualElement();
            e.style.flexDirection = dir;
            return e;
        }

        public static Label Text(string s, int size, Color color, FontStyle style = FontStyle.Normal)
        {
            var l = new Label(s ?? "");
            l.style.fontSize = size * TypeScale;
            l.style.color = color;
            l.style.unityFontStyleAndWeight = style;
            l.style.whiteSpace = WhiteSpace.Normal;
            return l.Face();
        }

        public static T Pad<T>(this T el, float t, float r, float b, float l) where T : VisualElement
        {
            el.style.paddingTop = t; el.style.paddingRight = r;
            el.style.paddingBottom = b; el.style.paddingLeft = l;
            return el;
        }

        public static T Margin<T>(this T el, float t, float r, float b, float l) where T : VisualElement
        {
            el.style.marginTop = t; el.style.marginRight = r;
            el.style.marginBottom = b; el.style.marginLeft = l;
            return el;
        }

        public static T Bg<T>(this T el, Color c) where T : VisualElement
        {
            el.style.backgroundColor = c;
            return el;
        }

        public static T Border<T>(this T el, Color c, float w) where T : VisualElement
        {
            el.style.borderTopColor = c; el.style.borderRightColor = c;
            el.style.borderBottomColor = c; el.style.borderLeftColor = c;
            el.style.borderTopWidth = w; el.style.borderRightWidth = w;
            el.style.borderBottomWidth = w; el.style.borderLeftWidth = w;
            return el;
        }

        public static T Radius<T>(this T el, float r) where T : VisualElement
        {
            el.style.borderTopLeftRadius = r; el.style.borderTopRightRadius = r;
            el.style.borderBottomLeftRadius = r; el.style.borderBottomRightRadius = r;
            return el;
        }

        public static T Abs<T>(this T el, float? left, float? top, float? right = null, float? bottom = null)
            where T : VisualElement
        {
            el.style.position = Position.Absolute;
            if (left.HasValue) el.style.left = left.Value;
            if (top.HasValue) el.style.top = top.Value;
            if (right.HasValue) el.style.right = right.Value;
            if (bottom.HasValue) el.style.bottom = bottom.Value;
            return el;
        }

        public static T Size<T>(this T el, float? w, float? h) where T : VisualElement
        {
            if (w.HasValue) el.style.width = w.Value;
            if (h.HasValue) el.style.height = h.Value;
            return el;
        }

        public static T Grow<T>(this T el, float g = 1f) where T : VisualElement
        {
            el.style.flexGrow = g;
            return el;
        }

        /// A control. Focusable and keyboard-operable by construction — every
        /// affordance in every concept goes through here, so "can a keyboard
        /// reach it" is answered once rather than three times.
        public static Button Control(string label, System.Action onClick, Color fg, Color bg)
        {
            var b = new Button(onClick) { text = label };
            b.style.fontSize = 15 * TypeScale;
            b.style.color = fg;
            b.style.backgroundColor = bg;
            b.style.unityFontStyleAndWeight = FontStyle.Normal;
            b.Face().Pad(12, 26, 12, 26).Radius(2).Border(fg, 1);
            b.style.alignSelf = Align.FlexStart;
            b.focusable = true;
            return b;
        }

        /// Reduced motion, read from the OS. Every concept must ask before it
        /// animates; a transition that cannot be turned off is an accessibility
        /// defect, not a flourish.
        ///
        /// ponytail: Unity exposes no cross-platform reduced-motion query, so
        /// this reads an explicit opt-out (CF_REDUCE_MOTION=1) and otherwise
        /// assumes motion is welcome. Swap in a platform query when one exists.
        public static bool ReduceMotion =>
            System.Environment.GetEnvironmentVariable("CF_REDUCE_MOTION") == "1"
            || PlayerPrefs.GetInt("cf.reduceMotion", 0) == 1;

        /// Fade a newly-attached element in, unless motion is reduced — in which
        /// case it is simply present. "Settle then continue" must collapse to
        /// "continue", never to a wait for an animation that will not run.
        public static void Appear(VisualElement el, float seconds = 0.35f)
        {
            if (ReduceMotion) { el.style.opacity = 1f; return; }
            el.style.opacity = 0f;
            el.experimental.animation
              .Start(0f, 1f, (int)(seconds * 1000), (e, v) => e.style.opacity = v);
        }
    }
}
