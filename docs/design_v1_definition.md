# Chronicle Forge v1 — Design Definition (v1.1)

Status: **Adopted.** This is the top-level document for all specification
decisions through the 2026-08-16 release. Extracted verbatim from
[`design_v1_direction.md`](design_v1_direction.md) §3 so the Source-of-Truth set
is three standalone files: this definition, the direction review, and
[`v1_ux_spec.md`](v1_ux_spec.md). If this file and the direction review ever
disagree, this file wins.

---

## 1. Core Fantasy

You are the one soul that keeps being reborn into a single world. Each short life
leaves marks; centuries harden those marks into history; and you return to read
that history and feel the shiver of recognizing it: **"the hand that wrote this
was mine, and I had forgotten."**

## 2. Core Experience

**The moment the player finds — unaided — their own past hand in the world's
history: "I did this."**

Everything else in the game is either preparation for this moment or its
afterglow.

## 3. Emotional Arc

1. **Small, but seated** (opening): the world is vast and your life is short —
   but you know what you are (the returning soul) and when you matter (fateful
   moments). Uncertainty about *power*, never about *role*.
2. **The first jolt** (first rebirth): you die, return, and the world has
   changed — because of you. Powerlessness inverts.
3. **Déjà vu** (mid lives): a name you shouldn't know, known. "Wait — that was
   me." Awe mixed with homesickness.
4. **Authorship** (later lives): from reacting to planting. You go to your death
   on purpose, having chosen what you want to find later. Death turns from loss
   into sowing.
5. **Acceptance and quiet pride** (world's end): the finished chronicle reads as
   your diary. Pride, and a little grief that it is over.
6. **The itch** (after the ending): "a different world could hold a different
   me."

Target in one line: **powerlessness → causal surprise → intent → quiet pride**,
as a staged inversion.

## 4. North Star

**Does this decision strengthen the experience of discovering, by yourself and
across felt time, the marks your own past lives left on the world?**

If not — however attractive — cut it.

## 5. Success Criteria (v1 minimum, design-only)

1. A first-time player, **within their first session and ≤30 minutes**, at least
   once recognizes unaided: *"that was my past life's doing."*
2. After a world ends, the player can explain in their own words, for at least
   one major historical event, **which life and which choice of theirs caused
   it**.
3. Death is never experienced as game over — the death→rebirth transition reads
   as *"the harvest of what I planted begins,"* not as loss.
4. The player starts a second world **to leave a different mark**, and can name
   that intended mark before starting.

All four or the design has failed, regardless of what else shipped.

## 6. Out of Scope (v1)

Combat/action depth · free-roam sandbox verbs · synchronous multiplayer ·
endless worlds · additional simulation depth · stat/skill progression ·
answer-pushing UI. (Presentation-level cuts: `design_v1_direction.md` §4 Won't
Have.)

## 7. Design Principles

1. **Never fabricate history.** Dramatize the telling, never the events.
   Everything the player discovers really happened, really connected.
2. **Discovery is induced, not delivered.** Leave room for a hypothesis before
   showing the answer.
3. **Few inputs, heavy inputs.** Invest in showing one choice's blast radius,
   not in adding choices.
4. **Death is punctuation, not punishment.** Death is the device that hardens
   marks into history and opens the next discovery.
5. **Time distance is emotional distance.** Always place felt time between
   leaving a mark and finding it. The moment this becomes an instant reward, the
   game is ordinary.
6. **The world does not flatter the player.** You are a thread in history, not
   its protagonist. A world that orbits the player cannot surprise them.
7. **Recognition: guaranteed once, rare thereafter.** The first "that was me" is
   engineered to happen early; every later one is scarce and precious.
8. **The same world is always the same world.** Reproducibility is not an
   engineering guarantee but the ground of play: discoveries can be pointed at,
   handed over, verified.
9. **A world must be finishable as a reading.** Design for the afterglow of a
   completed chronicle, not for length.
10. **The interface is the artifact.** The player should never feel they are
    using a UI *about* the world's history — they should feel they are holding
    the history itself. Presentation choices are judged by how diegetic they
    are.
11. **One page, one focus.** Every screen has a single focal object — a choice,
    a reveal, a mark, a map. Text is staged, never dumped. The historian's voice
    is a character (dry, factual, occasionally astonished) and is specified, not
    improvised.

## 8. One Sentence

**Chronicle Forge is the one world your soul keeps returning to — and its
history is a diary written in your own forgotten hand.**
