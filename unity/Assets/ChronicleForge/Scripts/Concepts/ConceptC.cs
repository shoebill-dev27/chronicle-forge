// CONCEPT C — Causal Archive
//
// THE IDEA: lives, acts and events are fragments in a dark archive. Causality
// is not a picture you are given — it is something you dig out, one real edge
// at a time, and only when you ask.
//
// The rule that shapes the whole composition: DURING A LIFE THE NETWORK IS NOT
// DRAWN. Showing the graph while the reader is still living would hand them
// every attribution at once and leave nothing to discover (D-03/D-04). So the
// field stays a scatter of unreadable fragments until a consequence is
// inspected — and then it unfolds, hop by hop, along edges the graph really
// holds.
//
// It is deliberately not a deduction puzzle: nothing is hidden that the reader
// could be tricked about, there is no wrong answer to submit, and the origin is
// stated plainly once reached. The work is excavation, not inference.

using System.Collections.Generic;
using System.Linq;
using ChronicleForge.Core;
using ChronicleForge.Model;
using UnityEngine;
using UnityEngine.UIElements;

namespace ChronicleForge.Concepts
{
    public sealed class ConceptC : ConceptBase
    {
        public override string ConceptName => "C — Causal Archive";

        private static readonly Color Void_ = new Color(0.043f, 0.051f, 0.063f);
        private static readonly Color Card = new Color(0.11f, 0.12f, 0.145f);
        private static readonly Color CardLit = new Color(0.18f, 0.19f, 0.23f);
        private static readonly Color Glass = new Color(0.86f, 0.88f, 0.92f);
        private static readonly Color GlassSoft = new Color(0.58f, 0.60f, 0.65f);
        private static readonly Color GlassFaint = new Color(0.34f, 0.36f, 0.40f);

        protected override void Render()
        {
            Root.Bg(Void_);
            Root.style.flexDirection = FlexDirection.Column;

            var field = Root.Put(UiKit.Box()).Grow().Named("field");
            field.style.position = Position.Relative;

            if (Session.Phase == Phase.Trace) BuildExcavation(field);
            else BuildField(field);

            BuildFocus(Root.Put(UiKit.Box()).Named("focus"));
        }

        // -- the archive floor -------------------------------------------------

        /// Fragments the reader has reached, scattered. Deliberately not
        /// arranged by cause: the arrangement is what inspection reveals.
        private void BuildField(VisualElement field)
        {
            var reached = Session.Beats.Take(Session.Index + 1).ToList();
            var fragments = new List<(string top, string sub, string coord, int seedX, int seedY)>();

            foreach (Beat b in reached)
            {
                switch (b)
                {
                    case Outcome o when o.OptionNumber != 0:
                        fragments.Add((o.Label, $"{o.Year}年 · {Voice.Epithet(o.LifeOrdinal)}",
                                       null, o.Year * 37, o.LifeOrdinal * 53));
                        break;
                    case Years y:
                        foreach (WorldEvent e in y.Events.Take(4))
                            fragments.Add((e.Phrase, $"{e.Year}年 · {e.Scale}", null,
                                           e.Year * 41, e.Phrase.Length * 29));
                        break;
                    case Aftermath a:
                        foreach (Mark m in a.Hardened)
                            fragments.Add((m.Name, MarkCaption(m), m.Ref,
                                           (m.PlantedYear ?? 0) * 43, m.Reach * 31));
                        break;
                }
            }

            if (fragments.Count == 0)
            {
                var empty = field.Put(UiKit.Text(Voice.ShelfTitle, 34, GlassFaint));
                empty.Abs(64, null, null, 48);
                return;
            }

            // A stable pseudo-scatter: derived from the fragment's own numbers,
            // so the same world lays out the same way every run. Position here
            // carries NO causal claim — it is a floor, not a graph.
            for (int i = 0; i < fragments.Count && i < 14; i++)
            {
                var f = fragments[i];
                var c = field.Put(UiKit.Box()).Bg(Card).Pad(10, 12, 10, 12).Radius(2);
                c.Abs(4 + (f.seedX % 72), 8 + (f.seedY % 60) + i * 6);
                c.style.left = Length.Percent(3 + (f.seedX % 70));
                c.style.top = 12 + ((f.seedY + i * 37) % 60) * 6;
                c.style.maxWidth = 380;
                c.Pad(16, 20, 16, 20);
                c.Border(new Color(1, 1, 1, 0.10f), 1);
                c.style.opacity = 0.70f + 0.07f * (i % 4);   // depth, not meaning
                c.style.rotate = new Rotate(Angle.Degrees(-1.2f + (f.seedX % 5) * 0.6f));

                // 朱 only where a connection has actually been confirmed.
                if (f.coord != null && Session.Gate.MayUseVermilion(f.coord))
                {
                    c.style.opacity = 1f;
                    c.Bg(CardLit);
                    c.style.borderLeftColor = UiKit.Vermilion;
                    c.style.borderLeftWidth = 3;
                }
                c.Put(UiKit.Text(f.top, 14, Glass));
                c.Put(UiKit.Text(f.sub, 11, GlassFaint).Margin(4, 0, 0, 0));
            }
        }

        // -- the excavation ----------------------------------------------------

        /// One real path, unfolded as far as it has been dug. Each hop is one
        /// CausalEdge; nothing between two hops may be drawn as a link.
        private void BuildExcavation(VisualElement field)
        {
            CausePath p = Session.TracedCase;
            field.Pad(36, 48, 24, 48);
            field.Put(UiKit.Text(Voice.TraceOf(p.Event, p.Year), 13, GlassFaint));

            // Position 0 is the consequence; each dug hop adds one intermediate
            // node with one edge; the origin node is added only at the end.
            int walked = Session.TraceHopsShown;
            int total = p.Steps.Count + 1;
            var chain = field.Put(UiKit.Box()).Margin(18, 0, 0, 0);
            void Node(string phrase, int year, bool head)
            {
                var node = chain.Put(UiKit.Box()).Bg(head ? CardLit : Card)
                                .Pad(12, 16, 12, 16).Radius(2).Border(new Color(1, 1, 1, 0.08f), 1);
                node.style.alignSelf = Align.FlexStart;
                node.style.maxWidth = 520;
                node.Put(UiKit.Text(phrase, head ? 22 : 16, head ? Glass : GlassSoft));
                node.Put(UiKit.Text($"{year}年", 12, GlassFaint).Margin(4, 0, 0, 0));
                UiKit.Appear(node, 0.2f);
            }
            void Edge()
            {
                // A real edge. Drawn as one segment because the graph holds
                // exactly one between these two.
                chain.Put(UiKit.Box()).Size(2, 26).Bg(new Color(1, 1, 1, 0.22f)).Margin(2, 0, 2, 22);
            }
            Node(p.Event, p.Year, walked == 0 && !Session.TraceAtOrigin);
            for (int i = 0; i < walked; i++)
            {
                Edge();
                Node(p.Steps[i].Phrase, p.Steps[i].Year, i == walked - 1 && !Session.TraceAtOrigin);
            }
            if (!Session.TraceAtOrigin)
            {
                // The next hop exists but has not been dug: a stub, not a node.
                chain.Put(UiKit.Box()).Size(2, 14).Bg(new Color(1, 1, 1, 0.10f)).Margin(2, 0, 0, 22);
                field.Put(UiKit.Text(Voice.TraceOriginHidden, 12, GlassFaint).Margin(6, 0, 0, 0));
            }

            field.Put(UiKit.Text(Voice.TraceHop(Session.TraceStepIndex, total), 12, GlassFaint)
                          .Margin(14, 0, 0, 0));

            // Other contributing origins exist. Drawn as truthful stubs — real
            // in number, unnamed, because the path the reader dug is not the
            // only one and the page may not imply that it is.
            if (DiscoveryGate.SharesCause(p))
            {
                var row = field.Put(UiKit.Box(FlexDirection.Row)).Margin(10, 0, 0, 0);
                for (int i = 0; i < Mathf.Min(4, p.OtherOrigins); i++)
                    row.Put(UiKit.Box()).Size(22, 2).Bg(new Color(1, 1, 1, 0.16f)).Margin(8, 6, 0, 0);
                row.Put(UiKit.Text(Voice.SharedCause(p.OtherOrigins), 13, GlassSoft));
            }
            if (p.Posthumous)
                field.Put(UiKit.Text(Voice.Posthumous, 12, GlassFaint).Margin(6, 0, 0, 0));

            if (Session.Gate.Knows(p.Ref))
            {
                var origin = field.Put(UiKit.Box()).Margin(20, 0, 0, 0).Pad(16, 20, 16, 20)
                                  .Bg(new Color(0.14f, 0.10f, 0.11f)).Radius(2);
                origin.style.alignSelf = Align.FlexStart;
                origin.style.borderLeftColor = UiKit.Vermilion;
                origin.style.borderLeftWidth = 4;
                origin.Put(UiKit.Text(Voice.TraceAtOrigin, 12, GlassFaint));
                // C-6: autonomous origins are narrated as history.
                origin.Put(UiKit.Text(Session.Gate.MayCallItYourChoice(p)
                        ? Voice.OriginSealed(p.OriginLife, p.OriginYear)
                        : Voice.OriginAutonomous(p.OriginLife, p.OriginYear), 15, Glass)
                    .Margin(6, 0, 0, 0));
                // C-2: the exact wording the act was sealed under.
                origin.Put(UiKit.Text($"「{p.OriginAct}」", 26, UiKit.Vermilion).Margin(10, 0, 0, 0));
                UiKit.Appear(origin, 0.45f);
            }
        }

        // -- the focus bar: what the reader is doing right now ------------------

        private void BuildFocus(VisualElement bar)
        {
            bar.Bg(new Color(0.02f, 0.025f, 0.035f)).Pad(28, 64, 32, 64);
            bar.style.minHeight = Length.Percent(38);
            bar.style.borderTopColor = new Color(1, 1, 1, 0.07f);
            bar.style.borderTopWidth = 1;

            switch (Session.Phase)
            {
                case Phase.Shelf:
                    bar.Put(UiKit.Text(Voice.ShelfInvitation(Session.World.Place, Session.World.MaxYear),
                                       18, Glass));
                    FocusAfterRender = bar.Put(PrimaryButton(Voice.Open)).Margin(14, 0, 0, 0);
                    break;

                case Phase.Life:
                {
                    var r = (Rebirth)Session.Current;
                    bar.Put(UiKit.Text(Voice.LifeOpens(r.LifeOrdinal, Session.World.Place, r.Talent, r.Era),
                                       22, Glass));
                    FocusAfterRender = bar.Put(PrimaryButton(Voice.Turn)).Margin(14, 0, 0, 0);
                    break;
                }

                case Phase.Juncture:
                {
                    var j = Session.CurrentJuncture;
                    bar.Put(UiKit.Text(j.Header, 26, Glass));
                    bar.Put(UiKit.Text(Voice.JunctureWhere(j.Year, j.Age), 12, GlassFaint)
                                .Margin(4, 0, 12, 0));
                    var row = bar.Put(UiKit.Box(FlexDirection.Row));
                    foreach (Option o in j.Options)
                    {
                        bool picked = Session.SelectedOption == o.N;
                        var card = row.Put(UiKit.Box()).Grow().Margin(0, 8, 0, 0)
                                      .Bg(picked ? CardLit : Card).Pad(12, 14, 12, 14).Radius(2);
                        card.Border(picked ? Glass : new Color(1, 1, 1, 0.08f), picked ? 2 : 1);
                        card.focusable = true;
                        int n = o.N;
                        card.RegisterCallback<ClickEvent>(_ => { Session.Select(n); Rebuild(); });
                        card.Put(UiKit.Text($"{o.N}. {o.Label}", 17, Glass));
                        card.Put(UiKit.Text(Voice.OptionTarget(o.Target), 12, GlassSoft)
                                     .Margin(6, 0, 0, 0));
                        if (j.Recognition != null && j.Recognition.Option == o.N)
                            card.Put(RecognitionBlock(j));
                        if (picked) FocusAfterRender = card;
                    }
                    if (Session.Notice != null)
                        bar.Put(UiKit.Text(Session.Notice, 12, GlassSoft).Margin(8, 0, 0, 0));
                    var seal = bar.Put(PrimaryButton(Voice.Seal)).Margin(12, 0, 0, 0);
                    seal.SetEnabled(Session.CanSeal);
                    seal.style.alignSelf = Align.FlexStart;
                    if (Session.CanSeal) FocusAfterRender = seal;
                    break;
                }

                case Phase.Sealed:
                {
                    var o = (Outcome)Session.Current;
                    bar.Put(UiKit.Text(o.OptionNumber == 0 ? Voice.LetPass : Voice.SealedAs(o.Label),
                                       22, Glass));
                    bar.Put(UiKit.Text(Voice.Planted(o.Planted), 14, GlassSoft).Margin(6, 0, 0, 0));
                    FocusAfterRender = bar.Put(PrimaryButton(Voice.Turn)).Margin(12, 0, 0, 0);
                    break;
                }

                case Phase.Death:
                {
                    var d = (Death)Session.Current;
                    bar.Put(UiKit.Text(Voice.Died(d.LifeOrdinal, d.Age), 24, GlassSoft));
                    bar.Put(UiKit.Text(Voice.Pending(d.Pending), 13, GlassFaint).Margin(6, 0, 0, 0));
                    FocusAfterRender = bar.Put(PrimaryButton(Voice.Turn)).Margin(12, 0, 0, 0);
                    break;
                }

                case Phase.Years:
                {
                    var y = (Years)Session.Current;
                    var row = bar.Put(UiKit.Box(FlexDirection.Row));
                    row.style.alignItems = Align.FlexEnd;
                    row.Put(UiKit.Text(y.Span.ToString(), 110, Glass));
                    row.Put(UiKit.Text("年", 18, GlassSoft).Margin(0, 0, 10, 6));
                    FocusAfterRender = bar.Put(PrimaryButton(Voice.Turn)).Margin(8, 0, 0, 0);
                    break;
                }

                case Phase.Aftermath:
                {
                    var a = Session.CurrentAftermath;
                    bar.Put(UiKit.Text($"{Voice.ReturnEyebrow} · {Voice.Year(a.Year)}", 12, GlassFaint));
                    foreach (Change c in a.Changes.Take(2))
                        bar.Put(UiKit.Text(
                            $"{(c.Sealed ? Voice.SealedAs(c.Act) : Voice.WorldActed + "：" + c.Act)} → {c.Consequence}",
                            15, Glass).Margin(6, 0, 0, 0));
                    if (a.Changes.Count == 0)
                        bar.Put(UiKit.Text(Voice.Hardened(a.Hardened.Count), 15, GlassSoft));
                    // The investigate affordance is visible on the return page,
                    // not buried behind the ending.
                    var marks = a.Hardened.Where(m => !Session.Gate.Knows(m.Ref)).ToList();
                    if (marks.Count > 0)
                    {
                        Mark m = marks[0];
                        var b = bar.Put(UiKit.Control($"{m.Name} — {Voice.Inspect}",
                            () => { Session.ConfirmMark(m); Rebuild(); }, Glass, Card))
                            .Margin(12, 0, 0, 0);
                        b.style.alignSelf = Align.FlexStart;
                        FocusAfterRender = b;
                    }
                    var next = bar.Put(PrimaryButton(Voice.Turn)).Margin(10, 0, 0, 0);
                    next.style.alignSelf = Align.FlexStart;
                    if (marks.Count == 0) FocusAfterRender = next;
                    break;
                }

                case Phase.Closing:
                {
                    var c = Session.TheClosing;
                    bar.Put(UiKit.Text(Voice.EndingLine(c.Year, c.Ending), 24, Glass));
                    bar.Put(UiKit.Text($"{Voice.LivesLived(c.Lives)} · {Voice.Reread}", 13, GlassFaint)
                                .Margin(4, 0, 10, 0));
                    var row = bar.Put(UiKit.Box(FlexDirection.Row));
                    for (int i = 0; i < Mathf.Min(3, c.Cases.Count); i++)
                    {
                        CausePath p = c.Cases[i];
                        int idx = i;
                        var b = row.Put(UiKit.Control($"{i + 1}. {p.Event} — {p.Year}年",
                            () => { Session.OpenTrace(idx); Rebuild(); },
                            Session.Gate.MayUseVermilion(p.Ref) ? UiKit.Vermilion : Glass, Card))
                            .Margin(0, 8, 0, 0);
                        if (i == 0) FocusAfterRender = b;
                    }
                    break;
                }

                case Phase.Trace:
                {
                    CausePath p = Session.TracedCase;
                    var row = bar.Put(UiKit.Box(FlexDirection.Row));
                    if (!Session.TraceAtOrigin)
                        FocusAfterRender = row.Put(PrimaryButton(Voice.Further));
                    else if (!Session.Gate.Knows(p.Ref))
                        FocusAfterRender = row.Put(PrimaryButton(Voice.ConfirmLabel));
                    row.Put(UiKit.Control(Voice.Back, () => { Session.CloseTrace(); Rebuild(); },
                                          GlassSoft, new Color(0, 0, 0, 0f))).Margin(0, 0, 0, 10);
                    break;
                }
            }
        }

        private VisualElement RecognitionBlock(Juncture j)
        {
            string coord = DvsSession.RecognitionRef(j);
            var box = UiKit.Box().Margin(10, 0, 0, 0).Pad(8, 10, 8, 10).Bg(new Color(1, 1, 1, 0.04f));
            if (!Session.Gate.Knows(coord))
            {
                box.Put(UiKit.Text(Voice.ThreadHere, 12, GlassSoft));
                var b = box.Put(UiKit.Control(Voice.Inspect,
                    () => { Session.ConfirmRecognition(); Rebuild(); }, Glass, new Color(0, 0, 0, 0f)))
                    .Margin(6, 0, 0, 0);
                b.style.alignSelf = Align.FlexStart;
                b.style.fontSize = 12;
                return box;
            }
            Recognition r = j.Recognition;
            box.style.borderLeftColor = UiKit.Vermilion;
            box.style.borderLeftWidth = 3;
            box.Put(UiKit.Text(r.Name, 15, UiKit.Vermilion));
            box.Put(UiKit.Text(Voice.RecognisedBy(r.FounderLife, r.FounderTalent), 12, Glass)
                        .Margin(4, 0, 0, 0));
            string wording = Session.Gate.SealedActOf(r, coord);
            box.Put(wording != null
                ? UiKit.Text(Voice.SealedAs(wording), 14, UiKit.Vermilion).Margin(6, 0, 0, 0)
                : UiKit.Text(Voice.NoSealedWording, 11, GlassSoft).Margin(6, 0, 0, 0));
            return box;
        }

        private Button PrimaryButton(string label) =>
            UiKit.Control(label, () => { base.Primary(); Rebuild(); }, Glass, CardLit);
    }
}
