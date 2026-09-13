// CONCEPT A — Living Chronicle
//
// THE IDEA: lives are physical records that pile up on a desk. The book is an
// object ON the desk, never the screen itself — so the accumulation, not the
// page, is what the reader sees growing.
//
// Composition: the archive stack on the left grows by one sheet per death; the
// current life is one large sheet in the centre; loose slips on the right are
// the marks the years hardened. The dominant focal object is always the centre
// sheet, except during a trace, when it is the pair of sheets and the thread
// between them.
//
// Why not a parchment website: nothing here is a document with a scrollbar. The
// sheets are rotated, offset and shadowed; depth and count carry the meaning.

using System.Collections.Generic;
using System.Linq;
using ChronicleForge.Core;
using ChronicleForge.Model;
using UnityEngine;
using UnityEngine.UIElements;

namespace ChronicleForge.Concepts
{
    public sealed class ConceptA : ConceptBase
    {
        public override string ConceptName => "A — Living Chronicle";

        private static readonly Color Desk = new Color(0.13f, 0.10f, 0.07f);
        private static readonly Color DeskDim = new Color(0.07f, 0.055f, 0.04f);
        private static readonly Color Sheet = new Color(0.91f, 0.87f, 0.79f);
        private static readonly Color SheetOld = new Color(0.80f, 0.76f, 0.68f);
        private static readonly Color Slip = new Color(0.85f, 0.81f, 0.72f);

        protected override void Render()
        {
            bool dim = Session.Phase == Phase.Years;
            Root.Bg(dim ? DeskDim : Desk);
            Root.style.flexDirection = FlexDirection.Row;
            Root.style.paddingTop = 28; Root.style.paddingBottom = 28;
            Root.style.paddingLeft = 28; Root.style.paddingRight = 28;

            BuildStack(Root.Put(UiKit.Box()).Size(360, null).Named("archive"));
            var centre = Root.Put(UiKit.Box()).Grow().Margin(0, 24, 0, 24).Named("centre");
            // The sheet is a thing lying on the desk, not the desk: it takes the
            // height its words need and sits in the middle of the free space.
            centre.style.justifyContent = Justify.Center;
            centre.style.alignItems = Align.Center;
            BuildCentre(centre);
            BuildFragments(Root.Put(UiKit.Box()).Size(320, null).Named("fragments"));
        }

        // -- left: the lives that are already behind the reader -----------------

        private void BuildStack(VisualElement col)
        {
            col.Put(UiKit.Text(Voice.ShelfEyebrow, 12, new Color(0.55f, 0.48f, 0.38f))
                        .Margin(0, 0, 12, 4));

            List<Life> done = Session.ArchivedLives.ToList();
            if (done.Count == 0)
            {
                col.Put(UiKit.Text("——", 24, new Color(0.30f, 0.26f, 0.20f)).Margin(8, 0, 0, 4));
                return;
            }

            // Physical accumulation: each older sheet sits a little lower, a
            // little further left, and a little more turned. The pile IS the
            // count — the reader never has to read a number to feel it.
            var pile = col.Put(UiKit.Box()).Grow();
            for (int i = 0; i < done.Count; i++)
            {
                Life life = done[i];
                var sheet = pile.Put(UiKit.Box()).Bg(i == done.Count - 1 ? Sheet : SheetOld);
                sheet.Abs(6 + i * 6, i * 118).Size(320, 140).Pad(18, 20, 18, 20).Radius(2);
                sheet.style.rotate = new Rotate(Angle.Degrees(-2.2f + i * 1.4f));
                sheet.style.borderBottomColor = new Color(0, 0, 0, 0.35f);
                sheet.style.borderBottomWidth = 3;

                sheet.Put(UiKit.Text(Voice.LifeHeading(life.Ordinal), 16, UiKit.Ink));
                sheet.Put(UiKit.Text($"{life.BirthYear}–{life.DeathYear} · {life.Talent}",
                                     12, UiKit.InkSoft).Margin(4, 0, 0, 0));
            }
        }

        // -- centre: whatever the reader is living through now ------------------

        private void BuildCentre(VisualElement col)
        {
            var sheet = col.Put(UiKit.Box()).Bg(Sheet).Pad(48, 56, 44, 56).Radius(3);
            sheet.style.width = Length.Percent(92);
            sheet.style.maxHeight = Length.Percent(100);
            sheet.style.borderBottomColor = new Color(0, 0, 0, 0.45f);
            sheet.style.borderBottomWidth = 6;
            UiKit.Appear(sheet);

            switch (Session.Phase)
            {
                case Phase.Shelf: Shelf(sheet); break;
                case Phase.Life: LifeOpens(sheet); break;
                case Phase.Juncture: JunctureSheet(sheet); break;
                case Phase.Sealed: SealedSheet(sheet); break;
                case Phase.Death: DeathSheet(sheet); break;
                case Phase.Years: YearsSheet(sheet); break;
                case Phase.Aftermath: ReturnSheet(sheet); break;
                case Phase.Closing: ClosingSheet(sheet); break;
                case Phase.Trace: TraceSheet(sheet); break;
            }
        }

        private void Eyebrow(VisualElement s, string t) =>
            s.Put(UiKit.Text(t, 13, UiKit.InkFaint).Margin(0, 0, 14, 0));

        private void Shelf(VisualElement s)
        {
            Eyebrow(s, Voice.ShelfEyebrow);
            s.Put(UiKit.Text(Voice.ShelfTitle, 40, UiKit.Ink));
            s.Put(UiKit.Text(Voice.ShelfInvitation(Session.World.Place, Session.World.MaxYear),
                             18, UiKit.InkSoft).Margin(14, 0, 0, 0));
            FocusAfterRender = s.Put(PrimaryButton(Voice.Open)).Margin(32, 0, 0, 0);
        }

        private void LifeOpens(VisualElement s)
        {
            var r = (Rebirth)Session.Current;
            Eyebrow(s, Voice.LifeHeading(r.LifeOrdinal));
            s.Put(UiKit.Text(Voice.LifeOpens(r.LifeOrdinal, Session.World.Place, r.Talent, r.Era),
                             30, UiKit.Ink));
            s.Put(UiKit.Text(Voice.Year(r.Year), 16, UiKit.InkSoft).Margin(16, 0, 0, 0));
            FocusAfterRender = s.Put(PrimaryButton(Voice.Turn)).Margin(32, 0, 0, 0);
        }

        private void JunctureSheet(VisualElement s)
        {
            var j = Session.CurrentJuncture;
            Eyebrow(s, Voice.JunctureWhere(j.Year, j.Age));
            // The engine's own framing phrase, printed, never paraphrased.
            s.Put(UiKit.Text(j.Header, 32, UiKit.Ink).Margin(0, 0, 22, 0));

            foreach (Option o in j.Options)
            {
                bool picked = Session.SelectedOption == o.N;
                var slip = s.Put(UiKit.Box()).Bg(picked ? Color.white : Slip)
                            .Pad(14, 18, 14, 18).Margin(0, 0, 10, 0).Radius(2);
                slip.style.rotate = new Rotate(Angle.Degrees(picked ? 0f : -0.4f + o.N * 0.35f));
                slip.Border(picked ? UiKit.Ink : new Color(0, 0, 0, 0.12f), picked ? 2 : 1);
                slip.focusable = true;
                int n = o.N;
                slip.RegisterCallback<ClickEvent>(_ => { Session.Select(n); Rebuild(); });

                slip.Put(UiKit.Text($"{o.N}. {o.Label}", 19, UiKit.Ink));
                var meta = slip.Put(UiKit.Box(FlexDirection.Row)).Margin(6, 0, 0, 0);
                meta.Put(UiKit.Text(Voice.OptionTarget(o.Target), 13, UiKit.InkSoft));
                // D-01: "why" is dropped rather than substituted when the reason
                // is the reader's own past.
                if (DiscoveryGate.MayShowWhy(o))
                    meta.Put(UiKit.Text(Voice.OptionWhy(o.Why), 13, UiKit.InkFaint)
                                 .Margin(0, 0, 0, 10));

                // A thread runs through this option. Whose, only once earned.
                if (j.Recognition != null && j.Recognition.Option == o.N)
                    slip.Put(RecognitionBlock(j));

                if (picked) FocusAfterRender = slip;
            }

            if (Session.Notice != null)
                s.Put(UiKit.Text(Session.Notice, 13, UiKit.InkSoft).Margin(8, 0, 0, 0));

            var row = s.Put(UiKit.Box(FlexDirection.Row)).Margin(20, 0, 0, 0);
            var seal = row.Put(PrimaryButton(Voice.Seal));
            seal.SetEnabled(Session.CanSeal);
            if (Session.CanSeal) FocusAfterRender = seal;
        }

        /// The recognition, and the exact wording it can prove (C-2).
        private VisualElement RecognitionBlock(Juncture j)
        {
            string coord = DvsSession.RecognitionRef(j);
            var box = UiKit.Box().Margin(10, 0, 0, 0).Pad(10, 12, 10, 12);
            box.Bg(new Color(0, 0, 0, 0.04f));

            if (!Session.Gate.Knows(coord))
            {
                // Confirm tier not yet earned: the page says a thread is here —
                // the engine proved that much — and refuses to say whose.
                box.Put(UiKit.Text(Voice.ThreadHere, 14, UiKit.InkSoft));
                var b = box.Put(UiKit.Control(Voice.Inspect, () =>
                {
                    Session.ConfirmRecognition();
                    Rebuild();
                }, UiKit.Ink, new Color(0, 0, 0, 0f))).Margin(8, 0, 0, 0);
                b.style.alignSelf = Align.FlexStart;
                return box;
            }

            Recognition r = j.Recognition;
            // Earned. 朱 is legal here and only here.
            box.style.borderLeftColor = UiKit.Vermilion;
            box.style.borderLeftWidth = 3;
            box.Put(UiKit.Text(Voice.RecognisedName(r.Name), 17, UiKit.Vermilion));
            box.Put(UiKit.Text(Voice.RecognisedBy(r.FounderLife, r.FounderTalent), 14, UiKit.Ink)
                        .Margin(4, 0, 0, 0));
            if (r.PlantedYear.HasValue)
                box.Put(UiKit.Text(Voice.RecognisedYear(r.PlantedYear.Value), 13, UiKit.InkSoft));

            string wording = Session.Gate.SealedActOf(r, coord);
            box.Put(wording != null
                ? UiKit.Text(Voice.SealedAs(wording), 16, UiKit.Vermilion).Margin(8, 0, 0, 0)
                // C-2: no proof the player chose it, so the page says so rather
                // than borrowing the world's phrase and calling it a memory.
                : UiKit.Text(Voice.NoSealedWording, 13, UiKit.InkSoft).Margin(8, 0, 0, 0));
            return box;
        }

        private void SealedSheet(VisualElement s)
        {
            var o = (Outcome)Session.Current;
            Eyebrow(s, Voice.JunctureWhere(o.Year, o.Age));
            s.Put(UiKit.Text(o.OptionNumber == 0 ? Voice.LetPass : Voice.SealedAs(o.Label),
                             30, UiKit.Ink));

            // The wax seal — an object, not an icon. Ink, not 朱: sealing an act
            // is not a confirmed past-life connection.
            var wax = s.Put(UiKit.Box()).Size(64, 64).Radius(32).Margin(24, 0, 0, 0);
            wax.Bg(new Color(0.32f, 0.22f, 0.18f));
            wax.style.alignItems = Align.Center;
            wax.style.justifyContent = Justify.Center;
            wax.Put(UiKit.Text(o.Kind_.Substring(0, 1), 22, new Color(0.85f, 0.80f, 0.72f)));

            s.Put(UiKit.Text(Voice.Planted(o.Planted), 16, UiKit.InkSoft).Margin(18, 0, 0, 0));
            FocusAfterRender = s.Put(PrimaryButton(Voice.Turn)).Margin(28, 0, 0, 0);
        }

        private void DeathSheet(VisualElement s)
        {
            var d = (Death)Session.Current;
            Eyebrow(s, Voice.Year(d.Year));
            s.Put(UiKit.Text(Voice.Died(d.LifeOrdinal, d.Age), 34, UiKit.Ink));
            s.Put(UiKit.Text(d.Title, 18, UiKit.InkSoft).Margin(10, 0, 0, 0));
            s.Put(UiKit.Text(Voice.Pending(d.Pending), 15, UiKit.InkFaint).Margin(18, 0, 0, 0));
            // The sheet is already leaving the centre for the pile.
            s.style.rotate = new Rotate(Angle.Degrees(-1.6f));
            FocusAfterRender = s.Put(PrimaryButton(Voice.Turn)).Margin(28, 0, 0, 0);
        }

        private void YearsSheet(VisualElement s)
        {
            var y = (Years)Session.Current;
            s.Bg(SheetOld);
            Eyebrow(s, $"{y.FromYear} → {y.ToYear}");
            // Elapsed time, legible without reading a sentence.
            s.Put(UiKit.Text(y.Span.ToString(), 150, UiKit.Ink));
            s.Put(UiKit.Text(y.Events.Count == 0 ? Voice.YearsSilent(y.Span) : Voice.YearsFalling(y.Span),
                             20, UiKit.InkSoft).Margin(-8, 0, 0, 0));
            if (y.Events.Count > 0)
                s.Put(UiKit.Text(Voice.YearsMoved(y.Events.Count), 15, UiKit.InkFaint)
                          .Margin(10, 0, 0, 0));
            FocusAfterRender = s.Put(PrimaryButton(Voice.Turn)).Margin(28, 0, 0, 0);
        }

        private void ReturnSheet(VisualElement s)
        {
            var a = Session.CurrentAftermath;
            Eyebrow(s, Voice.ReturnEyebrow);
            s.Put(UiKit.Text(Voice.Year(a.Year), 28, UiKit.Ink).Margin(0, 0, 16, 0));

            // P-10's digest: an ordinary, unconfirmed consequence of an act.
            foreach (Change c in a.Changes)
            {
                var line = s.Put(UiKit.Box()).Margin(0, 0, 12, 0).Pad(10, 12, 10, 12);
                line.Bg(new Color(0, 0, 0, 0.04f));
                line.style.borderLeftWidth = 3;
                // C-6: the world's own acts are not the reader's choices, and
                // neither wears 朱 — nothing here is confirmed yet.
                line.style.borderLeftColor = c.Sealed ? UiKit.Ink : UiKit.InkFaint;
                line.Put(UiKit.Text(c.Sealed ? Voice.SealedAs(c.Act) : $"{Voice.WorldActed}：{c.Act}",
                                    16, UiKit.Ink));
                line.Put(UiKit.Text($"{c.Consequence} — {Voice.ChangedTimes(c.Times)}, {c.FirstYear}年",
                                    14, UiKit.InkSoft).Margin(4, 0, 0, 0));
            }
            if (a.Changes.Count == 0)
                s.Put(UiKit.Text(Voice.Hardened(a.Hardened.Count), 16, UiKit.InkSoft));

            FocusAfterRender = s.Put(PrimaryButton(Voice.Turn)).Margin(24, 0, 0, 0);
        }

        private void ClosingSheet(VisualElement s)
        {
            var c = Session.TheClosing;
            Eyebrow(s, Voice.EndingEyebrow);
            s.Put(UiKit.Text(Voice.EndingLine(c.Year, c.Ending), 34, UiKit.Ink));
            s.Put(UiKit.Text(Voice.LivesLived(c.Lives), 18, UiKit.InkSoft).Margin(8, 0, 0, 24));

            s.Put(UiKit.Text(Voice.Reread, 14, UiKit.InkFaint).Margin(0, 0, 8, 0));
            var threads = s.Put(UiKit.Box());
            for (int i = 0; i < Mathf.Min(3, c.Cases.Count); i++)
            {
                CausePath p = c.Cases[i];
                int idx = i;
                var row = threads.Put(UiKit.Control(
                    $"{i + 1}. {Voice.TraceOf(p.Event, p.Year)} — {Voice.InvestigateHint}",
                    () => { Session.OpenTrace(idx); Rebuild(); },
                    // Already-confirmed threads keep their 朱; the rest are ink.
                    InkFor(p.Ref), new Color(0, 0, 0, 0.03f)));
                row.Margin(0, 0, 8, 0);
                row.style.alignSelf = Align.FlexStart;
                if (i == 0) FocusAfterRender = row;
            }
        }

        private void TraceSheet(VisualElement s)
        {
            CausePath p = Session.TracedCase;
            Eyebrow(s, Voice.TraceOf(p.Event, p.Year));

            // The walk back. Position 0 is the consequence itself; each further
            // hop is one intermediate event the graph really holds; the origin is
            // the last position and appears only once the walk reaches it.
            int walked = Session.TraceHopsShown;
            int total = p.Steps.Count + 1;
            var head = s.Put(UiKit.Box()).Margin(0, 0, 6, 0);
            head.Put(UiKit.Text($"{p.Year}年 · {p.Event}", 20, UiKit.Ink));
            for (int i = 0; i < walked; i++)
            {
                CauseStep st = p.Steps[i];
                s.Put(UiKit.Text("↑", 14, UiKit.InkFaint));
                s.Put(UiKit.Text($"{st.Year}年 · {st.Phrase}", 17, UiKit.Ink).Margin(0, 0, 6, 0));
            }
            if (!Session.TraceAtOrigin)
                s.Put(UiKit.Text(Voice.TraceOriginHidden, 13, UiKit.InkFaint));
            s.Put(UiKit.Text(Voice.TraceHop(Session.TraceStepIndex, total), 13, UiKit.InkFaint)
                      .Margin(6, 0, 0, 0));

            if (DiscoveryGate.SharesCause(p))
                s.Put(UiKit.Text(Voice.SharedCause(p.OtherOrigins), 14, UiKit.InkSoft)
                          .Margin(10, 0, 0, 0));
            if (p.Posthumous)
                s.Put(UiKit.Text(Voice.Posthumous, 13, UiKit.InkFaint).Margin(4, 0, 0, 0));

            var row = s.Put(UiKit.Box(FlexDirection.Row)).Margin(20, 0, 0, 0);
            if (!Session.TraceAtOrigin)
            {
                FocusAfterRender = row.Put(PrimaryButton(Voice.Further));
            }
            else if (!Session.Gate.Knows(p.Ref))
            {
                FocusAfterRender = row.Put(PrimaryButton(Voice.ConfirmLabel));
            }
            else
            {
                // Confirmed. The origin sheet is pulled out and laid beside this
                // one, with the 朱 thread between them.
                s.Put(OriginBlock(p));
            }
            row.Put(UiKit.Control(Voice.Back, () => { Session.CloseTrace(); Rebuild(); },
                                  UiKit.InkSoft, new Color(0, 0, 0, 0f)))
               .Margin(0, 0, 0, 10);
        }

        private VisualElement OriginBlock(CausePath p)
        {
            var box = UiKit.Box().Margin(16, 0, 0, 0).Pad(14, 16, 14, 16).Bg(Color.white);
            box.style.borderLeftColor = UiKit.Vermilion;
            box.style.borderLeftWidth = 4;
            box.Put(UiKit.Text(Voice.TraceAtOrigin, 13, UiKit.InkFaint));
            // C-6: an autonomous origin is narrated as history, never as a choice.
            box.Put(UiKit.Text(
                Session.Gate.MayCallItYourChoice(p)
                    ? Voice.OriginSealed(p.OriginLife, p.OriginYear)
                    : Voice.OriginAutonomous(p.OriginLife, p.OriginYear),
                16, UiKit.Ink).Margin(6, 0, 0, 0));
            // The exact wording, in 朱, because this connection is now confirmed.
            box.Put(UiKit.Text($"「{p.OriginAct}」", 22, UiKit.Vermilion).Margin(8, 0, 0, 0));
            return box;
        }

        // -- right: what the years hardened ------------------------------------

        private void BuildFragments(VisualElement col)
        {
            // Only the marks the reader has actually reached. Reading ahead in
            // the recording would put names on the desk before the years that
            // hardened them had passed.
            var marks = Session.Beats.Take(Session.Index + 1)
                               .OfType<Aftermath>()
                               .SelectMany(a => a.Hardened).ToList();
            col.Put(UiKit.Text(Voice.ReturnEyebrow, 12, new Color(0.55f, 0.48f, 0.38f))
                        .Margin(0, 0, 12, 4));
            if (marks.Count == 0)
            {
                col.Put(UiKit.Text("——", 24, new Color(0.30f, 0.26f, 0.20f)).Margin(8, 0, 0, 4));
                return;
            }

            foreach (Mark m in marks.Take(4))
            {
                var slip = col.Put(UiKit.Box()).Bg(Slip).Pad(16, 18, 16, 18).Margin(0, 0, 14, 0);
                slip.style.rotate = new Rotate(Angle.Degrees(-1.5f + m.Reach % 3));
                slip.focusable = true;
                // 朱 only once this mark's origin has been confirmed.
                slip.style.borderLeftWidth = 3;
                slip.style.borderLeftColor = InkFor(m.Ref);
                slip.Put(UiKit.Text(m.Name, 15, UiKit.Ink));
                slip.Put(UiKit.Text(MarkCaption(m), 12, UiKit.InkSoft).Margin(4, 0, 0, 0));

                if (!Session.Gate.Knows(m.Ref))
                {
                    Mark captured = m;
                    var b = slip.Put(UiKit.Control(Voice.Inspect, () =>
                    {
                        Session.ConfirmMark(captured);
                        Rebuild();
                    }, UiKit.InkSoft, new Color(0, 0, 0, 0f))).Margin(6, 0, 0, 0);
                    b.style.alignSelf = Align.FlexStart;
                    b.style.fontSize = 12;
                }
            }
        }

        private Button PrimaryButton(string label) =>
            UiKit.Control(label, () => { base.Primary(); Rebuild(); }, UiKit.Ink, new Color(0, 0, 0, 0.05f));
    }
}
