// What a surface is allowed to say, and when.
//
// The fixture holds the whole truth — every mark's founder, every path's origin
// — because the reader process needs it to answer questions the moment they are
// earned. The rules below are what stand between holding a fact and drawing it.
// They live in ONE place so that three different presentations cannot each
// invent their own interpretation of D-03.
//
//   D-01  "your past life" belongs to Confirm surfaces only. A juncture may not
//         say a former self is here; that is what Recognition is for, once,
//         where the engine can prove it.
//   D-03  A hardened mark may be drawn and NAMED, never attributed, until its
//         ref is confirmed. Every hardened mark belongs to an older life, so
//         attributing on delivery would hand the player the whole discovery.
//   D-04  Reading earns nothing. Inspecting, tracing and navigating never add a
//         reveal; only Confirm does.
//   C-6   An autonomous origin is traced truthfully and narrated as history. It
//         may never be captioned as a choice the player made.
//   朱     Vermilion means exactly one thing: a CONFIRMED past-life connection.
//         Nothing unconfirmed, pending, or merely interesting may wear it.

using System.Collections.Generic;
using ChronicleForge.Model;

namespace ChronicleForge.Core
{
    public sealed class DiscoveryGate
    {
        // Monotone by construction: there is no Revoke. D-04 makes a reveal
        // permanent, and permanence is cheaper to guarantee than to re-derive.
        private readonly HashSet<string> _known = new HashSet<string>();

        public IReadOnlyCollection<string> Known => _known;
        public int KnownCount => _known.Count;

        /// The only way a fact is ever earned. Returns true when this call is
        /// what earned it, so a surface can play the reveal exactly once.
        public bool Confirm(string coordRef) =>
            !string.IsNullOrEmpty(coordRef) && _known.Add(coordRef);

        /// Side-effect free, deliberately: it is called from render, every frame,
        /// on every mark. If asking could earn, reading would earn (D-04).
        public bool Knows(string coordRef) =>
            !string.IsNullOrEmpty(coordRef) && _known.Contains(coordRef);

        // -- what may be drawn -------------------------------------------------

        /// A hardened mark's founder, or null while it is still unearned (D-03).
        /// Callers must render null as "something gained a name" — never as a
        /// blank where a name would go, and never by falling back to the ordinal.
        public int? FounderOf(Mark mark) =>
            mark != null && Knows(mark.Ref) ? mark.FounderLife : (int?)null;

        /// 朱 is legal on this coordinate. The single predicate every concept
        /// asks before it uses vermilion for anything.
        public bool MayUseVermilion(string coordRef) => Knows(coordRef);

        /// The founding act's exact wording, or null when it may not be shown.
        ///
        /// Two independent refusals, and both matter:
        ///   * unconfirmed  — the reader has not earned this attribution yet;
        ///   * SealedAct null — the engine cannot prove the player chose it, so
        ///     there is no wording to compare against. Borrowing the world's own
        ///     phrase for the same act and calling it a memory is exactly the
        ///     lie C-2 exists to prevent.
        public string SealedActOf(Recognition r, string coordRef) =>
            r != null && Knows(coordRef) ? r.SealedAct : null;

        /// True when this path's origin was the player's own sealed choice AND
        /// the reader has earned it. Anything else is narrated as history (C-6).
        public bool MayCallItYourChoice(CausePath path) =>
            path != null && path.OriginSealed && Knows(path.Ref);

        /// A traced consequence with contributing origins beyond this one must
        /// say so. Drawing a single thread as the whole cause is a lie of
        /// omission the graph itself contradicts.
        public static bool SharesCause(CausePath path) => path != null && path.OtherOrigins > 0;

        /// A juncture option may never carry "your past pulls here" (D-01). The
        /// Python side already nulls it; this is the surface-side assertion, so
        /// a future stream change cannot quietly leak it onto a decision page.
        public static bool MayShowWhy(Option option) =>
            option != null
            && !string.IsNullOrEmpty(option.Why)
            && option.Why.IndexOf("your past", System.StringComparison.OrdinalIgnoreCase) < 0;
    }
}
