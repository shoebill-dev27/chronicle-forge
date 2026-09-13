// CONCEPT B — Life + History
//
// THE IDEA: two layers always co-exist. The upper one is the life being lived;
// the lower one is the history stacking up underneath it. Neither is a menu the
// other opens — both are on screen the whole time, and the RATIO between them
// is what the composition uses to say which beat this is.
//
//   juncture   play space takes almost everything; history recedes to a line
//   death      the ratio inverts — history rises, the life dims to a band
//   years      the history strip runs; a year counter carries the elapsed time
//   return     the play space comes back, and the strip has new marks in it
//
// The history layer is the C1 time surface: year runs horizontally, one band
// per life, depth is historical order. It is never a map — the engine emits no
// spatial axis, so there is nothing to place.

using System.Collections.Generic;
using System.Linq;
using ChronicleForge.Core;
using ChronicleForge.Model;
using UnityEngine;
using UnityEngine.UIElements;

namespace ChronicleForge.Concepts
{
    public sealed class ConceptB : ConceptBase
    {
        public override string ConceptName => "B — Life + History";

        private static readonly Color Night = new Color(0.08f, 0.09f, 0.12f);
        private static readonly Color Stage = new Color(0.14f, 0.15f, 0.19f);
        private static readonly Color StageDim = new Color(0.10f, 0.10f, 0.13f);
        private static readonly Color Strip = new Color(0.05f, 0.055f, 0.075f);
        private static readonly Color Warm = new Color(0.93f, 0.90f, 0.83f);
        private static readonly Color WarmSoft = new Color(0.66f, 0.64f, 0.60f);
        private static readonly Color WarmFaint = new Color(0.42f, 0.41f, 0.39f);

        /// How much of the screen the life gets, by beat. This table IS the
        /// concept: every state has its own composition rather than one layout
        /// that swaps its text.
        private float StagePortion => Session.Phase switch
        {
            Phase.Juncture => 0.86f,
            Phase.Sealed => 0.78f,
            Phase.Death => 0.30f,   // the ratio inverts
            Phase.Years => 0.22f,
            Phase.Aftermath => 0.55f,
            Phase.Closing => 0.34f,
            Phase.Trace => 0.62f,
            _ => 0.70f,
        };

        protected override void Render()
        {
            Root.Bg(Night);
            Root.style.flexDirection = FlexDirection.Column;

            var stage = Root.Put(UiKit.Box()).Grow(StagePortion)
                            .Bg(Session.Phase == Phase.Years ? StageDim : Stage)
                            .Pad(40, 64, 32, 64).Named("stage");
            stage.style.justifyContent = Justify.Center;
            var history = Root.Put(UiKit.Box()).Grow(1f - StagePortion)
                              .Bg(Strip).Pad(16, 24, 16, 24).Named("history");
            UiKit.Appear(stage, 0.25f);

            BuildStage(stage);
            BuildHistory(history);
        }

        // -- the upper layer: the life being lived -----------------------------

        private void BuildStage(VisualElement s)
        {
            switch (Session.Phase)
            {
                case Phase.Shelf: Shelf(s); break;
                case Phase.Life: LifeOpens(s); break;
                case Phase.Juncture: JunctureStage(s); break;
                case Phase.Sealed: SealedStage(s); break;
                case Phase.Death: DeathStage(s); break;
                case Phase.Years: YearsStage(s); break;
                case Phase.Aftermath: ReturnStage(s); break;
                case Phase.Closing: ClosingStage(s); break;
                case Phase.Trace: TraceStage(s); break;
            }
        }

        private void Eyebrow(VisualElement s, string t) =>
            s.Put(UiKit.Text(t, 12, WarmFaint).Margin(0, 0, 12, 0));

        private void Shelf(VisualElement s)
        {
            Eyebrow(s, Voice.ShelfEyebrow);
            s.Put(UiKit.Text(Voice.ShelfTitle, 44, Warm));
            s.Put(UiKit.Text(Voice.ShelfInvitation(Session.World.Place, Session.World.MaxYear),
                             18, WarmSoft).Margin(12, 0, 0, 0));
            FocusAfterRender = s.Put(PrimaryButton(Voice.Open)).Margin(28, 0, 0, 0);
        }

        private void LifeOpens(VisualElement s)
        {
            var r = (Rebirth)Session.Current;
            Eyebrow(s, $"{Voice.LifeHeading(r.LifeOrdinal)} · {Voice.Year(r.Year)}");
            s.Put(UiKit.Text(Voice.LifeOpens(r.LifeOrdinal, Session.World.Place, r.Talent, r.Era),
                             32, Warm));
            FocusAfterRender = s.Put(PrimaryButton(Voice.Turn)).Margin(28, 0, 0, 0);
        }

        private void JunctureStage(VisualElement s)
        {
            var j = Session.CurrentJuncture;
            Eyebrow(s, Voice.JunctureWhere(j.Year, j.Age));
            s.Put(UiKit.Text(j.Header, 38, Warm).Margin(0, 0, 24, 0));

            // Choice is the screen's subject here: the options are the largest
            // thing on the stage, side by side, and readable at a glance.
            var row = s.Put(UiKit.Box(FlexDirection.Row)).Grow();
            foreach (Option o in j.Options)
            {
                bool picked = Session.SelectedOption == o.N;
                var card = row.Put(UiKit.Box()).Grow().Margin(0, 8, 0, 8)
                              .Bg(picked ? new Color(0.20f, 0.21f, 0.26f) : new Color(0.17f, 0.18f, 0.22f))
                              .Pad(20, 20, 20, 20).Radius(3);
                card.Border(picked ? Warm : new Color(1, 1, 1, 0.08f), picked ? 2 : 1);
                card.focusable = true;
                int n = o.N;
                card.RegisterCallback<ClickEvent>(_ => { Session.Select(n); Rebuild(); });

                card.Put(UiKit.Text(o.N.ToString(), 13, WarmFaint));
                card.Put(UiKit.Text(o.Label, 22, Warm).Margin(6, 0, 0, 0));
                card.Put(UiKit.Text(Voice.OptionTarget(o.Target), 14, WarmSoft).Margin(10, 0, 0, 0));
                card.Put(UiKit.Text(o.Kind, 12, WarmFaint).Margin(4, 0, 0, 0));
                if (DiscoveryGate.MayShowWhy(o))
                    card.Put(UiKit.Text(Voice.OptionWhy(o.Why), 13, WarmFaint).Margin(6, 0, 0, 0));

                if (j.Recognition != null && j.Recognition.Option == o.N)
                    card.Put(RecognitionBlock(j));
                if (picked) FocusAfterRender = card;
            }

            if (Session.Notice != null)
                s.Put(UiKit.Text(Session.Notice, 13, WarmSoft).Margin(10, 0, 0, 0));
            var seal = s.Put(PrimaryButton(Voice.Seal)).Margin(16, 0, 0, 0);
            seal.SetEnabled(Session.CanSeal);
            seal.style.alignSelf = Align.FlexStart;
            if (Session.CanSeal) FocusAfterRender = seal;
        }

        private VisualElement RecognitionBlock(Juncture j)
        {
            string coord = DvsSession.RecognitionRef(j);
            var box = UiKit.Box().Margin(14, 0, 0, 0).Pad(10, 10, 10, 10)
                           .Bg(new Color(1, 1, 1, 0.04f));
            if (!Session.Gate.Knows(coord))
            {
                box.Put(UiKit.Text(Voice.ThreadHere, 13, WarmSoft));
                var b = box.Put(UiKit.Control(Voice.Inspect,
                    () => { Session.ConfirmRecognition(); Rebuild(); }, Warm, new Color(0, 0, 0, 0f)))
                    .Margin(8, 0, 0, 0);
                b.style.alignSelf = Align.FlexStart;
                b.style.fontSize = 12;
                return box;
            }
            Recognition r = j.Recognition;
            box.style.borderLeftColor = UiKit.Vermilion;
            box.style.borderLeftWidth = 3;
            box.Put(UiKit.Text(r.Name, 16, UiKit.Vermilion));
            box.Put(UiKit.Text(Voice.RecognisedBy(r.FounderLife, r.FounderTalent), 13, Warm)
                        .Margin(4, 0, 0, 0));
            string wording = Session.Gate.SealedActOf(r, coord);
            box.Put(wording != null
                ? UiKit.Text(Voice.SealedAs(wording), 15, UiKit.Vermilion).Margin(6, 0, 0, 0)
                : UiKit.Text(Voice.NoSealedWording, 12, WarmSoft).Margin(6, 0, 0, 0));
            return box;
        }

        private void SealedStage(VisualElement s)
        {
            var o = (Outcome)Session.Current;
            Eyebrow(s, Voice.JunctureWhere(o.Year, o.Age));
            s.Put(UiKit.Text(o.OptionNumber == 0 ? Voice.LetPass : Voice.SealedAs(o.Label), 32, Warm));
            s.Put(UiKit.Text(Voice.Planted(o.Planted), 17, WarmSoft).Margin(16, 0, 0, 0));
            FocusAfterRender = s.Put(PrimaryButton(Voice.Turn)).Margin(26, 0, 0, 0);
        }

        private void DeathStage(VisualElement s)
        {
            var d = (Death)Session.Current;
            s.Put(UiKit.Text(Voice.Died(d.LifeOrdinal, d.Age), 30, WarmSoft));
            s.Put(UiKit.Text(Voice.Pending(d.Pending), 15, WarmFaint).Margin(8, 0, 0, 0));
            FocusAfterRender = s.Put(PrimaryButton(Voice.Turn)).Margin(18, 0, 0, 0);
        }

        private void YearsStage(VisualElement s)
        {
            var y = (Years)Session.Current;
            var row = s.Put(UiKit.Box(FlexDirection.Row));
            row.style.alignItems = Align.FlexEnd;
            row.Put(UiKit.Text(y.Span.ToString(), 140, Warm));
            row.Put(UiKit.Text("年", 24, WarmSoft).Margin(0, 0, 16, 6));
            s.Put(UiKit.Text(y.Events.Count == 0 ? Voice.YearsSilent(y.Span) : Voice.YearsMoved(y.Events.Count),
                             15, WarmFaint));
            FocusAfterRender = s.Put(PrimaryButton(Voice.Turn)).Margin(12, 0, 0, 0);
        }

        private void ReturnStage(VisualElement s)
        {
            var a = Session.CurrentAftermath;
            Eyebrow(s, $"{Voice.ReturnEyebrow} · {Voice.Year(a.Year)}");
            foreach (Change c in a.Changes)
            {
                var line = s.Put(UiKit.Box()).Margin(0, 0, 10, 0).Pad(10, 12, 10, 12)
                            .Bg(new Color(1, 1, 1, 0.03f));
                line.style.borderLeftWidth = 3;
                line.style.borderLeftColor = c.Sealed ? Warm : WarmFaint;
                line.Put(UiKit.Text(c.Sealed ? Voice.SealedAs(c.Act) : $"{Voice.WorldActed}：{c.Act}",
                                    16, Warm));
                line.Put(UiKit.Text($"{c.Consequence} — {Voice.ChangedTimes(c.Times)}", 13, WarmSoft)
                             .Margin(4, 0, 0, 0));
            }
            if (a.Changes.Count == 0)
                s.Put(UiKit.Text(Voice.Hardened(a.Hardened.Count), 16, WarmSoft));
            FocusAfterRender = s.Put(PrimaryButton(Voice.Turn)).Margin(16, 0, 0, 0);
        }

        private void ClosingStage(VisualElement s)
        {
            var c = Session.TheClosing;
            Eyebrow(s, Voice.EndingEyebrow);
            s.Put(UiKit.Text(Voice.EndingLine(c.Year, c.Ending), 30, Warm));
            s.Put(UiKit.Text(Voice.LivesLived(c.Lives), 16, WarmSoft).Margin(6, 0, 0, 14));
            for (int i = 0; i < Mathf.Min(3, c.Cases.Count); i++)
            {
                CausePath p = c.Cases[i];
                int idx = i;
                var b = s.Put(UiKit.Control($"{i + 1}. {Voice.TraceOf(p.Event, p.Year)}",
                    () => { Session.OpenTrace(idx); Rebuild(); },
                    Session.Gate.MayUseVermilion(p.Ref) ? UiKit.Vermilion : Warm,
                    new Color(1, 1, 1, 0.03f))).Margin(0, 0, 6, 0);
                b.style.alignSelf = Align.FlexStart;
                if (i == 0) FocusAfterRender = b;
            }
        }

        private void TraceStage(VisualElement s)
        {
            CausePath p = Session.TracedCase;
            Eyebrow(s, Voice.TraceOf(p.Event, p.Year));
            // The trace rises out of the history layer into the play space: the
            // hops are drawn bottom-up, so the eye travels from the strip below.
            // The consequence is the top line; uncovered intermediates stack
            // beneath it; the origin joins only once the walk reaches it.
            int walked = Session.TraceHopsShown;
            int total = p.Steps.Count + 1;
            s.Put(UiKit.Text($"{p.Year}年 · {p.Event}", 22, Warm).Margin(0, 0, 6, 0));
            for (int i = 0; i < walked; i++)
                s.Put(UiKit.Text($"↑ {p.Steps[i].Year}年 · {p.Steps[i].Phrase}", 16, WarmSoft)
                          .Margin(0, 0, 6, 0));
            if (!Session.TraceAtOrigin)
                s.Put(UiKit.Text(Voice.TraceOriginHidden, 12, WarmFaint));
            s.Put(UiKit.Text(Voice.TraceHop(Session.TraceStepIndex, total), 12, WarmFaint));
            if (DiscoveryGate.SharesCause(p))
                s.Put(UiKit.Text(Voice.SharedCause(p.OtherOrigins), 13, WarmSoft).Margin(8, 0, 0, 0));

            var row = s.Put(UiKit.Box(FlexDirection.Row)).Margin(14, 0, 0, 0);
            if (!Session.TraceAtOrigin) FocusAfterRender = row.Put(PrimaryButton(Voice.Further));
            else if (!Session.Gate.Knows(p.Ref)) FocusAfterRender = row.Put(PrimaryButton(Voice.ConfirmLabel));
            row.Put(UiKit.Control(Voice.Back, () => { Session.CloseTrace(); Rebuild(); },
                                  WarmSoft, new Color(0, 0, 0, 0f))).Margin(0, 0, 0, 10);

            if (Session.Gate.Knows(p.Ref))
            {
                var box = s.Put(UiKit.Box()).Margin(14, 0, 0, 0).Pad(12, 14, 12, 14)
                           .Bg(new Color(1, 1, 1, 0.04f));
                box.style.borderLeftColor = UiKit.Vermilion;
                box.style.borderLeftWidth = 4;
                box.Put(UiKit.Text(Session.Gate.MayCallItYourChoice(p)
                        ? Voice.OriginSealed(p.OriginLife, p.OriginYear)
                        : Voice.OriginAutonomous(p.OriginLife, p.OriginYear), 15, Warm));
                box.Put(UiKit.Text($"「{p.OriginAct}」", 22, UiKit.Vermilion).Margin(6, 0, 0, 0));
            }
        }

        // -- the lower layer: the C1 time surface ------------------------------

        private void BuildHistory(VisualElement h)
        {
            h.Put(UiKit.Text($"{Session.World.Place} · 0–{Session.World.MaxYear}年", 11, WarmFaint));

            var field = h.Put(UiKit.Box()).Grow().Margin(8, 0, 0, 0);
            field.style.position = Position.Relative;
            float span = Mathf.Max(1, Session.World.MaxYear);

            // One band per life, in historical order. Depth is order, not time —
            // the horizontal axis is the only thing that measures years.
            foreach (Life life in Session.World.Lives)
            {
                bool reached = life.Ordinal <= Session.CurrentLifeOrdinal;
                float top = (life.Ordinal - 1) * 40f;
                float x0 = life.BirthYear / span * 100f;
                float w = Mathf.Max(1.5f, (life.DeathYear - life.BirthYear) / span * 100f);

                var band = field.Put(UiKit.Box()).Named($"life-{life.Ordinal}");
                band.style.position = Position.Absolute;
                band.style.top = top;
                band.style.left = Length.Percent(x0);
                band.style.width = Length.Percent(w);
                band.style.height = 24;
                band.Bg(reached
                    ? (life.Ordinal == Session.CurrentLifeOrdinal
                        ? new Color(0.85f, 0.82f, 0.75f)
                        : new Color(0.40f, 0.39f, 0.37f))
                    // A life the reader has not reached is drawn as absence, not
                    // as content: the strip shows the shape of the book, never
                    // its unread future.
                    : new Color(1, 1, 1, 0.05f));

                var tag = field.Put(UiKit.Text(reached ? Voice.Epithet(life.Ordinal) : "——",
                                               10, reached ? WarmSoft : WarmFaint));
                tag.style.position = Position.Absolute;
                tag.style.top = top;
                tag.style.left = Length.Percent(Mathf.Min(92f, x0 + w + 0.6f));
            }

            // The marks the years hardened, placed by the year they were planted.
            // Unattributed ones sit on a neutral line; only a confirmed mark is
            // drawn on its founder's band, and only a confirmed mark wears 朱.
            foreach (Mark m in Session.Beats.Take(Session.Index + 1)
                                     .OfType<Aftermath>().SelectMany(a => a.Hardened))
            {
                bool known = Session.Gate.Knows(m.Ref);
                float x = (m.PlantedYear ?? 0) / span * 100f;
                var dot = field.Put(UiKit.Box()).Size(14, 14).Radius(7);
                dot.style.position = Position.Absolute;
                dot.style.left = Length.Percent(Mathf.Clamp(x, 0f, 99f));
                dot.style.top = known ? (m.FounderLife - 1) * 40f + 5f
                                      : Session.World.Lives.Count * 40f + 8f;
                dot.Bg(known ? UiKit.Vermilion : WarmSoft);
            }
        }

        private Button PrimaryButton(string label) =>
            UiKit.Control(label, () => { base.Primary(); Rebuild(); }, Warm, new Color(1, 1, 1, 0.06f));
    }
}
