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
    },
  };
})();
