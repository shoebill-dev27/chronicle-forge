// The Unity client's own words — the ONE inventory of copy it writes itself.
//
// Everything the engine supplies (place names, talents, eras, option labels,
// kinds, event phrases, legacy names) is printed exactly as the stream returns
// it and never appears here. Those are English, and stay English: the engine
// emits unbounded English proper nouns, which is the evidence ADR-004 settles
// 横書き on. What is here is the book's furniture and the sentences the page
// composes AROUND engine fields.
//
// D-3 §7 — the epithet table is CLOSED. A former self is 最初のあなた /
// N度目のあなた and nothing else. No other phrasing may enter this file.
//
// Two rules this file is audited against:
//   * every method takes its numbers from the stream; none invents a quantity;
//   * no decorative English. English appears only where an engine field does.

using System.Collections.Generic;

namespace ChronicleForge.Core
{
    public static class Voice
    {
        private static readonly string[] Numerals =
            { "", "", "二", "三", "四", "五", "六", "七", "八", "九", "十" };

        /// D-3 §7. Beyond the tenth life the rule holds and only the numeral changes.
        public static string Epithet(int ordinal)
        {
            if (ordinal < 1) return "あなた";
            if (ordinal == 1) return "最初のあなた";
            string n = ordinal < Numerals.Length ? Numerals[ordinal] : ordinal.ToString();
            return n + "度目のあなた";
        }

        // -- non-diegetic UI labels (A-1 exemption: these are controls, not voice)
        public const string Open = "ひらく";
        public const string Turn = "めくる";
        public const string Seal = "記す";
        public const string Inspect = "調べる";
        public const string Back = "戻る";
        public const string Further = "さらに遡る";
        public const string ConfirmLabel = "確かめる";
        public const string ToNow = "今の頁へ";
        public const string Reread = "歴史を読み返す";
        public const string Shelf = "本棚へ";

        // -- the shelf
        public const string ShelfEyebrow = "書棚";
        public const string ShelfTitle = "まだ書かれていない世界";
        public static string ShelfInvitation(string place, int span) =>
            $"{place} — {span}年の記録";

        // -- a life
        public static string LifeOpens(int ordinal, string place, string talent, string era) =>
            $"{Epithet(ordinal)}が{place}に生まれる。{talent}として、{era}に。";
        public static string LifeHeading(int ordinal) => $"{Epithet(ordinal)}の生";
        public static string Age(int age) => $"{age}歳";
        public static string Year(int year) => $"{year}年";

        // -- the juncture
        public static string JunctureWhere(int year, int age) => $"{year}年 — {age}歳";
        /// C-1: an option says who it is about. The target is an engine field.
        public static string OptionTarget(string target) => $"→ {target}";
        public static string OptionWhy(string why) => $"（{why}）";
        /// Shown when a thread runs through an option but has not been earned.
        /// It says a thread is there — the engine proved that — and not whose.
        public const string ThreadHere = "この選択肢には、古い糸が通っている";
        public const string UnrecordedChoice = "この本に記録された選択ではない。別の答えは別の本になる。";

        // -- the sealed act
        public static string SealedAs(string label) => $"「{label}」と記した";
        public static string Planted(int n) =>
            n == 0 ? "この手は、まだ何も置かなかった"
                   : n == 1 ? "この手は、ひとつのものを置いた"
                            : $"この手は、{n}つのものを置いた";
        public const string LetPass = "その季節は過ぎるにまかせた";
        /// C-6: the world's own act, not the reader's. Never captioned as a choice.
        public const string WorldActed = "世界が自ら動いた";

        // -- death and the years
        public static string Died(int ordinal, int age) => $"{Epithet(ordinal)} — {age}年の生";
        public static string Pending(int n) =>
            n == 0 ? "名を待つものは、なかった" : $"{n}つのものが、まだ名を待っている";
        public static string YearsFalling(int span) => $"{span}年が降り積もる";
        public static string YearsSilent(int span) => $"{span}年、世界は静かだった";
        public static string YearsMoved(int n) => $"その歳月、世界は{n}度動いた";

        // -- the return
        public const string ReturnEyebrow = "戻ってきた世界";
        /// D-03: counts what gained a name without saying whose it was.
        public static string Hardened(int n) =>
            n == 1 ? "その歳月、ひとつのものが名を得た"
                   : $"その歳月、{n}つのものが名を得た";
        public const string MarkUnattributed = "誰のものかは、まだわからない";
        public static string MarkOwner(int ordinal) => $"{Epithet(ordinal)}が置いたもの";
        public static string ChangedTimes(int n) =>
            n == 1 ? "一度" : $"{n}度";

        // -- investigation
        public const string InvestigateHint = "この帰結を調べる";
        public static string TraceOf(string eventPhrase, int year) => $"{eventPhrase} — {year}年";
        public static string TraceHop(int walked, int total) => $"{walked} / {total} 手前";
        public const string TraceOriginHidden = "その先は、まだ掘り出していない";
        public const string TraceAtOrigin = "ここが始まりだった";
        /// C-6: an autonomous origin, narrated as history.
        public static string OriginAutonomous(int ordinal, int year) =>
            $"{year}年、{Epithet(ordinal)}の生が、自らこう動いた";
        /// C-2: a confirmed connection to an act the reader themselves sealed.
        public static string OriginSealed(int ordinal, int year) =>
            $"{year}年、{Epithet(ordinal)}が、こう記した";
        /// The graph says this consequence has other contributing origins, so
        /// the page is obliged to say so rather than imply sole causality.
        public static string SharedCause(int others) =>
            others == 1 ? "この帰結には、ほかにもう一つの源がある"
                        : $"この帰結には、ほかに{others}つの源がある";
        public const string Posthumous = "あなたが見ることのなかった帰結";

        // -- the recognition climax
        public static string RecognisedName(string name) => $"{name}";
        public static string RecognisedBy(int ordinal, string talent) =>
            $"——{Epithet(ordinal)}、{talent}であった者。";
        public static string RecognisedYear(int year) => $"{year}年に置かれた";
        /// When the engine cannot prove the founding act was the player's own
        /// sealed choice, the page says so instead of borrowing the world's
        /// phrase and calling it a memory (C-2).
        public const string NoSealedWording = "その手が何と記したかは、この本に残っていない";

        // -- the ending
        public const string EndingEyebrow = "本が閉じる";
        public static string EndingLine(int year, string ending) => $"{year}年 — {ending}";
        public static string LivesLived(int n) => $"{n}の生";
        public static string LegacyLiving(bool living) => living ? "今も続いている" : "絶えた";

        // -- accessibility / state labels read by assistive tech
        public static readonly Dictionary<Phase, string> PhaseLabel = new Dictionary<Phase, string>
        {
            { Core.Phase.Shelf, "書棚" },
            { Core.Phase.Life, "生のはじまり" },
            { Core.Phase.Juncture, "岐路" },
            { Core.Phase.Sealed, "記した" },
            { Core.Phase.Death, "死" },
            { Core.Phase.Years, "歳月" },
            { Core.Phase.Aftermath, "戻ってきた世界" },
            { Core.Phase.Closing, "本の終わり" },
            { Core.Phase.Trace, "調査" },
        };
    }
}
