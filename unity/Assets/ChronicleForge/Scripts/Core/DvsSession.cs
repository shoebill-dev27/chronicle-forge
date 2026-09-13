// The DVS spine: one walk through one recorded world, shared by all three
// concepts.
//
// WHY IT IS SHARED
//   Three presentations that each kept their own notion of "where are we" would
//   be three chances to disagree with the engine. This class owns the position,
//   the selection, and the gate; a concept owns only how those look. That is
//   also what makes the three honestly comparable — they are the same session.
//
// WHAT IT DOES NOT DO
//   It does not simulate. It walks a beat list the engine already produced. It
//   draws no RNG, infers no causality, and cannot invent an option, a mark or a
//   path. Every Advance is a step along a recording.

using System;
using System.Collections.Generic;
using System.Linq;
using ChronicleForge.Model;

namespace ChronicleForge.Core
{
    public enum Phase
    {
        Shelf,       // 1. opening
        Life,        // 2. current life
        Juncture,    // 3/4. readable juncture, selection
        Sealed,      // 5. the recorded sealed act
        Death,       // 6.
        Years,       // 7. years passing
        Aftermath,   // 8/9/10. changed-world return, digest, unconfirmed consequence
        Closing,     // 14. ending
        Trace,       // 12/13. investigation and confirmation
    }

    public sealed class DvsSession
    {
        public readonly DvsFixture Fixture;
        public readonly DiscoveryGate Gate = new DiscoveryGate();

        private int _index = -1;          // position in the beat list
        private int _tracedCase = -1;     // index into Closing.Cases while tracing
        private int _traceStep;           // how far back along the path we have walked
        private Phase _beforeTrace = Phase.Closing;

        public DvsSession(DvsFixture fixture)
        {
            Fixture = fixture ?? throw new ArgumentNullException(nameof(fixture));
            if (fixture.Stream == null || fixture.Stream.Beats.Count == 0)
                throw new ArgumentException("a fixture with no beats describes no world");
        }

        public Phase Phase { get; private set; } = Phase.Shelf;

        /// How far into the recording the reader has walked. The page may draw
        /// beats up to here and not one past: a surface that read ahead would be
        /// showing a future the reader has not reached.
        public int Index => _index;
        public Beat Current => _index >= 0 && _index < Beats.Count ? Beats[_index] : null;
        public List<Beat> Beats => Fixture.Stream.Beats;
        public WorldBeats World => Fixture.Stream;

        /// The option the reader has picked but not committed to. Selection is
        /// not commitment (UX-R8): it moves nothing, persists nothing, and is
        /// cleared by leaving the juncture.
        public int SelectedOption { get; private set; }

        /// A truthful one-liner the surface should show, or null. Used for the
        /// one thing a fixture genuinely cannot do — see Seal().
        public string Notice { get; private set; }

        /// Lives whose pages are already behind the reader. Drives the
        /// "accumulated lives" of every concept, and is a count of beats walked,
        /// never a guess.
        public IEnumerable<Life> ArchivedLives =>
            World.Lives.Where(l => l.Ordinal < CurrentLifeOrdinal);

        public int CurrentLifeOrdinal { get; private set; }

        public Life CurrentLife =>
            World.Lives.FirstOrDefault(l => l.Ordinal == CurrentLifeOrdinal);

        // -- walking -----------------------------------------------------------

        public void Open()
        {
            if (Phase != Phase.Shelf) return;
            _index = -1;
            Step();
        }

        /// True when the reader may move on from here under their own power.
        /// A juncture is the one place that refuses: the page is a question, and
        /// turning past a question would answer it by default.
        public bool CanAdvance => Phase != Phase.Shelf && Phase != Phase.Juncture && Phase != Phase.Trace;

        public void Advance()
        {
            if (!CanAdvance) return;
            Step();
        }

        private void Step()
        {
            Notice = null;
            SelectedOption = 0;
            if (_index + 1 >= Beats.Count) return;
            _index++;
            switch (Current)
            {
                case Rebirth r:
                    CurrentLifeOrdinal = r.LifeOrdinal;
                    Phase = Phase.Life;
                    break;
                case Juncture j:
                    CurrentLifeOrdinal = j.LifeOrdinal;
                    Phase = Phase.Juncture;
                    break;
                case Outcome o:
                    CurrentLifeOrdinal = o.LifeOrdinal;
                    Phase = Phase.Sealed;
                    break;
                case Death d:
                    CurrentLifeOrdinal = d.LifeOrdinal;
                    Phase = Phase.Death;
                    break;
                case Years _:
                    Phase = Phase.Years;
                    break;
                case Aftermath _:
                    Phase = Phase.Aftermath;
                    break;
                case Closing _:
                    Phase = Phase.Closing;
                    break;
            }
        }

        // -- the juncture ------------------------------------------------------

        public Juncture CurrentJuncture => Current as Juncture;

        /// The option this recorded book was actually sealed under. A fixture is
        /// ONE history; the engine is the only thing that can say what a
        /// different answer would have done.
        public int RecordedOption =>
            (Beats.ElementAtOrDefault(_index + 1) as Outcome)?.OptionNumber ?? 0;

        /// Pick an option. Earns nothing, moves nothing, persists nothing.
        public void Select(int n)
        {
            if (Phase != Phase.Juncture) return;
            SelectedOption = n;
            Notice = n == RecordedOption ? null : Voice.UnrecordedChoice;
        }

        public bool CanSeal => Phase == Phase.Juncture && SelectedOption == RecordedOption
                               && RecordedOption != 0;

        /// Commit. Only the recorded option can be sealed.
        ///
        /// ponytail: a hard rail, and the honest one for a fixture. Sealing an
        /// unrecorded option would leave the page with no consequence to show —
        /// and stitching the recorded consequence onto a different act is the
        /// one thing this whole design exists to prevent. A live Python bridge
        /// removes the rail; a fixture cannot.
        public bool Seal()
        {
            if (!CanSeal) return false;
            Step();
            return true;
        }

        /// The recognition standing at this juncture, once the reader has earned
        /// it. Before that the surface may say a thread runs through this option
        /// — the engine proved that much — but not whose it is (D-01/D-03).
        public Recognition EarnedRecognition =>
            CurrentJuncture?.Recognition is { } r && Gate.Knows(RecognitionRef(CurrentJuncture))
                ? r
                : null;

        public static string RecognitionRef(Juncture j)
        {
            if (j?.Recognition == null) return null;
            Option carrier = j.Options.FirstOrDefault(o => o.N == j.Recognition.Option);
            // The heritage id is the stable handle for the thing recognised; it
            // is the same coordinate the exporter locked.
            return carrier?.HeritageId ?? $"recognition:{j.LifeOrdinal}:{j.Year}";
        }

        // -- investigation -----------------------------------------------------

        public Aftermath CurrentAftermath => Current as Aftermath;
        public Closing TheClosing => Beats.OfType<Closing>().FirstOrDefault();

        public CausePath TracedCase =>
            _tracedCase >= 0 ? TheClosing?.Cases.ElementAtOrDefault(_tracedCase) : null;

        /// How many hops back from the consequence have been walked. Position 0
        /// is the consequence itself, positions 1..Steps.Count are the
        /// intermediate events, and Steps.Count + 1 is the origin. The origin is
        /// only reachable at the end of the walk: an investigation that handed
        /// over its answer on the first click would not be one.
        public int TraceStepIndex => _traceStep;

        /// Intermediate hops the reader has uncovered so far (0..Steps.Count).
        public int TraceHopsShown =>
            TracedCase == null ? 0 : Math.Min(_traceStep, TracedCase.Steps.Count);

        public bool TraceAtOrigin =>
            TracedCase != null && _traceStep >= TracedCase.Steps.Count + 1;

        public void OpenTrace(int caseIndex)
        {
            if (TheClosing == null) return;
            if (caseIndex < 0 || caseIndex >= TheClosing.Cases.Count) return;
            _beforeTrace = Phase;
            _tracedCase = caseIndex;
            _traceStep = 0;
            Phase = Phase.Trace;
            Notice = null;
        }

        /// Walk one real edge further back. Reading earns nothing (D-04).
        public void TraceStep()
        {
            if (Phase != Phase.Trace || TracedCase == null) return;
            if (_traceStep < TracedCase.Steps.Count + 1) _traceStep++;
        }

        /// The one action that earns. Legal only at the end of the walk.
        public bool ConfirmTrace()
        {
            if (Phase != Phase.Trace || TracedCase == null || !TraceAtOrigin) return false;
            return Gate.Confirm(TracedCase.Ref);
        }

        public void CloseTrace()
        {
            if (Phase != Phase.Trace) return;
            _tracedCase = -1;
            _traceStep = 0;
            Phase = _beforeTrace;
        }

        /// S-02: confirm one hardened mark's origin from the return page. The
        /// other earning surface, and the earlier one — it is how a reader first
        /// learns that a mark has an owner at all.
        public bool ConfirmMark(Mark mark) => mark != null && Gate.Confirm(mark.Ref);

        /// The recognition climax. Earned by inspecting, never by arriving.
        public bool ConfirmRecognition()
        {
            string coord = RecognitionRef(CurrentJuncture);
            return coord != null && Gate.Confirm(coord);
        }
    }
}
