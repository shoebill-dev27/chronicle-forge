// What the Unity surface may say, asserted.
//
// These are the rules that stop a presentation from lying about the world, so
// they are tested at the gate rather than at each of the three concepts — three
// copies of an assertion is three chances to relax one of them.

using System.Linq;
using ChronicleForge.Core;
using ChronicleForge.Model;
using NUnit.Framework;
using UnityEngine;

namespace ChronicleForge.Tests
{
    public class DiscoveryGateTests
    {
        private static DvsFixture Load() =>
            FixtureLoader.Parse(Resources.Load<TextAsset>(FixtureLoader.ResourcePath).text);

        [Test]
        public void TheShippedFixtureLoads()
        {
            DvsFixture f = Load();
            Assert.AreEqual(FixtureLoader.ExpectedEngineVersion, f.EngineVersion);
            Assert.IsNotEmpty(f.CanonicalHash);
            Assert.Greater(f.Stream.Beats.Count, 0);
            // Every beat kind resolved to a real type; BeatConverter throws on
            // anything it does not know, so reaching here is the assertion.
            Assert.IsTrue(f.Stream.Beats.All(b => b != null));
        }

        [Test]
        public void AFixtureFromAnotherEngineIsRefused()
        {
            string json = Resources.Load<TextAsset>(FixtureLoader.ResourcePath).text
                .Replace(FixtureLoader.ExpectedEngineVersion, "9.9.9-not-this-engine");
            Assert.Throws<System.InvalidOperationException>(() => FixtureLoader.Parse(json));
        }

        [Test]
        public void AnUnknownBeatKindIsRefusedRatherThanGuessedAt()
        {
            string json = Resources.Load<TextAsset>(FixtureLoader.ResourcePath).text
                .Replace("\"t\": \"rebirth\"", "\"t\": \"prophecy\"");
            Assert.Throws<System.InvalidOperationException>(() => FixtureLoader.Parse(json));
        }

        [Test]
        public void AMarkHasNoFounderUntilItIsConfirmed()
        {
            var s = new DvsSession(Load());
            Mark mark = s.Beats.OfType<Aftermath>().SelectMany(a => a.Hardened).First();

            Assert.IsNull(s.Gate.FounderOf(mark), "D-03: attributed on delivery");
            Assert.IsFalse(s.Gate.MayUseVermilion(mark.Ref), "朱 on an unconfirmed mark");

            s.ConfirmMark(mark);
            Assert.AreEqual(mark.FounderLife, s.Gate.FounderOf(mark));
            Assert.IsTrue(s.Gate.MayUseVermilion(mark.Ref));
        }

        [Test]
        public void AskingWhetherSomethingIsKnownDoesNotEarnIt()
        {
            var s = new DvsSession(Load());
            Mark mark = s.Beats.OfType<Aftermath>().SelectMany(a => a.Hardened).First();
            for (int i = 0; i < 5; i++) s.Gate.Knows(mark.Ref);
            Assert.AreEqual(0, s.Gate.KnownCount, "D-04: reading earned something");
        }

        [Test]
        public void ConfirmingIsMonotoneAndIdempotent()
        {
            var s = new DvsSession(Load());
            Mark mark = s.Beats.OfType<Aftermath>().SelectMany(a => a.Hardened).First();
            Assert.IsTrue(s.ConfirmMark(mark));
            Assert.IsFalse(s.ConfirmMark(mark), "a second confirm reported as newly earned");
            Assert.AreEqual(1, s.Gate.KnownCount);
        }

        [Test]
        public void NoJunctureOptionNamesThePlayersOwnPast()
        {
            foreach (Juncture j in Load().Stream.Beats.OfType<Juncture>())
                foreach (Option o in j.Options)
                    Assert.IsFalse(
                        (o.Why ?? "").ToLowerInvariant().Contains("your past"),
                        $"D-01 leak at {j.Year}: {o.Why}");
        }

        [Test]
        public void TheSealedWordingIsWithheldUntilTheConnectionIsConfirmed()
        {
            DvsFixture f = Load();
            Juncture j = f.Stream.Beats.OfType<Juncture>().First(x => x.Recognition != null);
            string coord = DvsSession.RecognitionRef(j);
            var gate = new DiscoveryGate();

            Assert.IsNull(gate.SealedActOf(j.Recognition, coord));
            gate.Confirm(coord);
            // C-2: the exact wording, and only when the engine could prove it.
            Assert.AreEqual(j.Recognition.SealedAct, gate.SealedActOf(j.Recognition, coord));
        }

        [Test]
        public void AnAutonomousOriginIsNeverCalledTheReadersChoice()
        {
            DvsFixture f = Load();
            var gate = new DiscoveryGate();
            foreach (CausePath p in f.Stream.Beats.OfType<Closing>().SelectMany(c => c.Cases))
            {
                gate.Confirm(p.Ref);
                if (!p.OriginSealed)
                    Assert.IsFalse(gate.MayCallItYourChoice(p),
                                   "C-6: the world's own act captioned as a choice");
            }
        }

        [Test]
        public void EveryCausePathIsAnOrderedPathOfRealEdges()
        {
            // C-3: Steps are the events BETWEEN the consequence and the origin.
            // The walk a surface draws is consequence -> steps -> origin, and
            // the years along it must run backwards.
            foreach (CausePath p in Load().Stream.Beats.OfType<Closing>().SelectMany(c => c.Cases))
            {
                int last = p.Year;
                foreach (CauseStep st in p.Steps)
                {
                    Assert.LessOrEqual(st.Year, last, "a hop that runs forward in time");
                    Assert.IsNotEmpty(st.Phrase);
                    last = st.Year;
                }
                Assert.LessOrEqual(p.OriginYear, last, "an origin later than its consequence");
            }
        }

        [Test]
        public void AnOriginIsOnlyReachableAtTheEndOfTheWalk()
        {
            var s = new DvsSession(Load());
            Closing c = s.TheClosing;
            // Any case with at least one intermediate event needs more than one
            // step to reach its origin; seed 1 has twelve of them.
            int idx = c.Cases.FindIndex(p => p.Steps.Count > 0);
            if (idx < 0) Assert.Ignore("this world has no multi-hop path to walk");

            s.OpenTrace(idx);
            Assert.IsFalse(s.TraceAtOrigin);
            Assert.IsFalse(s.ConfirmTrace(), "confirmed before the walk reached the origin");
            while (!s.TraceAtOrigin) s.TraceStep();
            Assert.IsTrue(s.ConfirmTrace());
            Assert.IsTrue(s.Gate.MayUseVermilion(c.Cases[idx].Ref));
        }

        [Test]
        public void SelectingAnOptionCommitsNothing()
        {
            var s = new DvsSession(Load());
            s.Open();
            while (s.Phase != Phase.Juncture) s.Advance();
            int before = s.Index;

            s.Select(s.RecordedOption == 1 ? 2 : 1);
            Assert.AreEqual(before, s.Index, "selection moved the reader");
            Assert.IsFalse(s.CanSeal, "an unrecorded option was sealable");
            Assert.IsNotNull(s.Notice, "the page did not say the choice is unrecorded");

            s.Select(s.RecordedOption);
            Assert.IsTrue(s.CanSeal);
            Assert.IsTrue(s.Seal());
            Assert.AreEqual(Phase.Sealed, s.Phase);
        }

        [Test]
        public void AJunctureCannotBeTurnedPast()
        {
            var s = new DvsSession(Load());
            s.Open();
            while (s.Phase != Phase.Juncture) s.Advance();
            int at = s.Index;
            s.Advance();
            Assert.AreEqual(at, s.Index, "a question was answered by turning the page");
        }

        [Test]
        public void TheWholeChainIsReachable()
        {
            // opening -> choice -> recorded act -> death -> years -> return ->
            // investigation -> confirmation -> ending, walked end to end.
            var s = new DvsSession(Load());
            s.Open();
            Assert.AreEqual(Phase.Life, s.Phase);

            var seen = new System.Collections.Generic.HashSet<Phase> { s.Phase };
            for (int guard = 0; guard < 500 && s.Phase != Phase.Closing; guard++)
            {
                if (s.Phase == Phase.Juncture) { s.Select(s.RecordedOption); s.Seal(); }
                else s.Advance();
                seen.Add(s.Phase);
            }
            Assert.AreEqual(Phase.Closing, s.Phase, "the book never closed");
            foreach (Phase p in new[] { Phase.Life, Phase.Juncture, Phase.Sealed,
                                        Phase.Death, Phase.Years, Phase.Aftermath })
                Assert.Contains(p, seen.ToList(), $"never reached {p}");

            s.OpenTrace(0);
            Assert.AreEqual(Phase.Trace, s.Phase);
            while (!s.TraceAtOrigin) s.TraceStep();
            Assert.IsTrue(s.ConfirmTrace());
            s.CloseTrace();
            Assert.AreEqual(Phase.Closing, s.Phase);
        }

        [Test]
        public void TheReaderNeverHoldsABeatTheyHaveNotReached()
        {
            var s = new DvsSession(Load());
            s.Open();
            Assert.AreEqual(0, s.Index, "the walk started ahead of the first beat");
            Assert.Less(s.Index, s.Beats.Count);
        }
    }
}
