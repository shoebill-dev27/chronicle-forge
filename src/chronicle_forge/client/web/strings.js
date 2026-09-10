/* The page's own words — the ONE inventory of copy the client writes itself.
 *
 * Everything the engine supplies (place names, legacy names, option labels,
 * kinds, event phrases, eras, talents) is printed exactly as the stream returns
 * it and never appears here. What is here is the book's furniture and the two
 * or three diegetic sentences the page composes from stream fields.
 *
 * It lives in its own file because `book.js` and `time.js` both need it, and a
 * closed voice table copied into two files is a table that drifts. Loaded first
 * (see index.html), so both readers see the same words.
 *
 * D-3 §7 — the epithet table is CLOSED. A former self is named `最初のあなた /
 * N度目のあなた` and by no other phrasing; the older `第Nの生のあなた` form was
 * never in the table and is gone. */

"use strict";

(function () {
  // D-3 §7. Kanji numerals to the tenth life (the table's own forms); beyond
  // that the rule still holds and only the numeral changes.
  const NUM = ["", "", "二", "三", "四", "五", "六", "七", "八", "九", "十"];

  function epithet(ordinal) {
    const n = Number(ordinal);
    if (!n || n < 1) return "あなた";
    if (n === 1) return "最初のあなた";
    return (NUM[n] || String(n)) + "度目のあなた";
  }

  window.CF_VOICE = {
    epithet,

    strings: {
      // --- non-diegetic UI copy (verbs, ribbon, tooltip). D-3 §8 JP drafts,
      // owner-ratification pending.
      newBook: "新しい世界",
      turnPage: "めくる",
      flipBack: "前に戻る",
      seal: "記す",
      holdTooltip: "長く押す",
      statusWeaving: "紡いでいる……",
      statusPreview: "見本刷り — この世界は実在しない",
      statusReady: "本はここに",
      statusBridgeError: "本文が読み出せない",
      bridgeErrorLine: "この頁は読み出せなかった。",
      specimen: "見本",
      statusRemembered: "思い出した",
      statusSealed: "封じた",
      statusYears: "歳月が過ぎる……",
      statusWriting: "書き取っている……",

      // --- the S-02 reveal (D-3 §7). The year is a stream field and is
      // optional: a mark whose seed carries no planted year still gets a Hand,
      // just without a date it cannot honestly give.
      handBloom: (year) =>
        year == null
          ? "……この手は、これを置いた。"
          : `……この手は、${year}年にこれを置いた。`,
      handConfirm: (ordinal, talent) =>
        `——${epithet(ordinal)}、${talent}であった者。`,

      // --- the Time Surface captions (time.js). Real numbers only.
      surfaceDeath: (ordinal, age) => `${epithet(ordinal)} — ${age}年`,
      surfaceFalling: (span) => `${span}年が降り積もる`,
      surfaceHeld: "時が息をひそめる",
      surfaceSealed: (ordinal, year) =>
        year == null
          ? `${epithet(ordinal)}が置いたもの`
          : `${epithet(ordinal)}が置いたもの — ${year}年に`,
      // A hardened mark whose origin is NOT yet confirmed. Every hardened mark
      // belongs to a life older than the last, and D-03 reserves those for the
      // player to find, so this counts what gained a name without saying whose
      // it was. The mark itself still appears — it is real, and marks never lie.
      surfaceHardened: (n) =>
        n === 1 ? "その歳月、ひとつのものが名を得た" : `その歳月、${n}つのものが名を得た`,
      surfaceEcho: (n) => `その歳月、世界はあなたが遺したものの上で ${n} 度動いた`,
      surfaceSilent: (span) => `${span}年、世界は静かだった`,

      // --- PLACEHOLDER (English) — diegetic page copy with no ratified JP
      // draft. Every one of these is composed from stream fields; the words
      // around the fields are the only part this file owns. They belong in
      // D-3's ratified inventory (see design_v1_i1b_beat_stream.md §7-3).
      shelfEyebrow: "The shelf",
      shelfTitle: "An unwritten world",
      openingEyebrow: "A life opens",
      openingLine: (place, talent, era) =>
        talent ? `A life opens in ${place} — a ${talent}, in ${era}.` : `A life opens in ${place}.`,
      rebornLine: (place, talent, era) =>
        `You are born again into ${place} — a ${talent}, in ${era}.`,
      // "in a Imperial Age" was ungrammatical for every vowel-initial ending
      // class the engine emits; the definite article is correct for all of them.
      closingLine: (years, lives, ending) =>
        `${years} years, ${lives} lives. It closed in the ${ending}.`,
      inkSets: "The ink sets.",
      shelfInvite: (place) => `A book waits: ${place}.`,
      shelfSpine: (place, years) => `${place} · ${years} years`,

      // --- P-05 the entry / P-07 the act entering it. `actLine` is the act the
      // player sealed, in the engine's own label; `passLine` is the season let
      // pass, which the world answered instead. `plantCue` is S-03's single
      // permitted line (UX §P-07: no reward language, no numbers, and never
      // what the echo will become).
      entryEyebrow: "The entry",
      actLine: (year, label) => `Year ${year} — ${label}.`,
      passLine: (year) => `Year ${year} — you let the season pass.`,
      plantCue: "This will echo.",

      // --- P-13 the archive, P-12 the closing, P-14 the trace.
      // Non-diegetic controls (D-3 §8, exempt from the A-1 imperative audit
      // because they name an operation the reader performs, not the historian
      // addressing them).
      archiveEyebrow: "これらの頁は、もう書かれている",
      archivePrev: "前へ",
      archiveNext: "次へ",
      nowPage: "今の頁へ",
      investigate: "調べる",
      whatBefore: "その前には？",
      backToClosing: "戻る",
      reread: "歴史を読み返す",
      toShelf: "本棚へ",
      closingEyebrow: "年代記は閉じた",
      traceEyebrow: "これはどこから来たのか",

      // The archive's read-only note: the page a reader is looking at is spent,
      // and saying so is kinder than a dead control.
      archiveSpent: "この頁はもう記されている。",

      // A trace step. Both halves are engine words; the year is the event's own.
      traceStep: (year, phrase) => `${year}年 — ${phrase}。`,
      // The origin card. `sealed` decides which of the two forms is honest:
      // the player's own words, or the world's phrase for something their life
      // did without being asked (C-6 — never "the choice you made").
      traceOriginSealed: (ordinal, year, act) =>
        `——${epithet(ordinal)}が、${year}年に「${act}」を選んだ。`,
      // C-6: their life did this, they did not choose it. 行った / 選んだ carries
      // the distinction, and the trailing clause leaves no room to read it as a
      // decision. Never "the choice you made".
      traceOriginAuto: (ordinal, year, act) =>
        `——${epithet(ordinal)}は、${year}年に${act}を行った。選んだのではない。`,
      // Multi-cause honesty: the earliest act is ONE contributing origin.
      traceOthers: (n) =>
        `この出来事には、ほかに ${n} つの始まりがある。これはそのひとつ。`,
      traceDirect: "この出来事は、その行いから直に生まれた。",
      // The ending, when the world holds no traceable act of the player's. Said
      // plainly rather than papered over with an invented invitation.
      closingNoThread: "この世界には、あなたの手にたどり着く糸が残らなかった。",

      // --- C-1: the option's context line (baseline UX-R6 §5.2).
      //
      // Everything here is a *frame* around engine fields: the role word
      // renders `option.kind`, the target is `option.target` printed exactly as
      // the world spelled it, and the condition renders `option.why`. The
      // action itself is the engine's label and is never touched.
      //
      // CONTENT GAP (W-1, deliberately not filled): the world knows a target's
      // name and kind and how much tension stands on it, and nothing else. It
      // has no stake, no want, no relationship and no cost to state, so the
      // line cannot say what is *at issue* — only who this is about and how
      // pressing it is. Inventing the missing half is the one thing the client
      // may not do, so the line stops where the data stops.
      kindWord: {
        Person: "人",
        Faction: "派閥",
        Place: "地",
        Legacy: "遺されたもの",
        Wildcard: "兆し",
        Chance: "機",
      },
      // The tension signals, in words. Ω ("your past pulls here") is absent by
      // construction — the stream sends `null` for it, because naming the
      // player's own past on a decision surface is a Confirm, not a hint (D-01).
      whyWord: {
        "tension rising": "いま張りつめている",
        "long neglected": "長く顧みられていない",
        "an ally awaits": "味方が待っている",
      },
      optionContext(kind, target, why) {
        const role = this.kindWord[kind] || this.kindWord.Chance;
        const head = target ? `${role}〈${target}〉` : role;
        const cond = why ? this.whyWord[why] : null;
        return cond ? `${head} — ${cond}。` : `${head}。`;
      },

      // --- P-10 the rebirth digest. `digestLine` joins two engine strings —
      // the act (the label the player sealed it under, or the world's own
      // phrase for an act it took alone) and what the world did with it. The
      // dash is the only word this file owns here. No count and no year: UX
      // §P-10 hides everything numeric from the digest's lines (the running
      // head is furniture and carries the year, as on every other page).
      digestEyebrow: "The world you return to",
      digestLine: (act, consequence) => `${act} — ${consequence}.`,
    },
  };
})();
