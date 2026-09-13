// The Python beat stream, as C# types.
//
// Every field here exists in src/chronicle_forge/play/beats.py. Nothing is
// added, renamed or inferred: the Unity client is a second READER of the world
// the engine already built, and a field it invented would be a fact no engine
// run can vouch for. When beats.py changes, this file changes with it — it is
// a transcription, not a design.
//
// Optional Python fields (Optional[int] / Optional[str]) are int?/string here,
// so "the engine could not prove this" stays distinguishable from "zero" and
// from "empty". That distinction is load-bearing: Recognition.sealed_act == null
// means the founding act was NOT the player's own sealed choice, and a surface
// that read null as "" would silently caption autonomous history as a memory.

using System.Collections.Generic;
using Newtonsoft.Json;

namespace ChronicleForge.Model
{
    public sealed class Life
    {
        [JsonProperty("ordinal")] public int Ordinal;
        [JsonProperty("talent")] public string Talent;
        [JsonProperty("birth_year")] public int BirthYear;
        [JsonProperty("death_year")] public int DeathYear;
    }

    public sealed class WorldEvent
    {
        [JsonProperty("year")] public int Year;
        [JsonProperty("scale")] public string Scale;
        [JsonProperty("phrase")] public string Phrase;
        // Life ordinals whose own seeds directly caused this. Present in the
        // stream, and NOT free to draw: see DiscoveryGate.
        [JsonProperty("owners")] public List<int> Owners = new List<int>();
    }

    public sealed class Option
    {
        [JsonProperty("n")] public int N;
        [JsonProperty("label")] public string Label;
        [JsonProperty("kind")] public string Kind;
        /// The person, faction, place or legacy the act is aimed at (C-1).
        [JsonProperty("target")] public string Target;
        /// The dominant tension signal in words — null when that signal is the
        /// player's own past, which D-01 forbids a juncture from naming.
        [JsonProperty("why")] public string Why;
        [JsonProperty("heritage_id")] public string HeritageId;
    }

    public sealed class Recognition
    {
        [JsonProperty("option")] public int Option;
        [JsonProperty("name")] public string Name;
        [JsonProperty("founder_life")] public int FounderLife;
        [JsonProperty("founder_talent")] public string FounderTalent;
        [JsonProperty("planted_year")] public int? PlantedYear;
        [JsonProperty("reach")] public int Reach;
        /// C-2: the exact wording the founding life was sealed under. null when
        /// the engine cannot prove the player chose it.
        [JsonProperty("sealed_act")] public string SealedAct;
    }

    public sealed class Change
    {
        [JsonProperty("act")] public string Act;
        /// True only when this act was the player's own sealed choice (C-6).
        [JsonProperty("sealed")] public bool Sealed;
        [JsonProperty("consequence")] public string Consequence;
        [JsonProperty("times")] public int Times;
        [JsonProperty("first_year")] public int FirstYear;
    }

    public sealed class Mark
    {
        [JsonProperty("ref")] public string Ref;
        [JsonProperty("name")] public string Name;
        /// D-03: present in the payload, forbidden on the surface until the
        /// reader has confirmed this mark's Ref. Read it through DiscoveryGate.
        [JsonProperty("founder_life")] public int FounderLife;
        [JsonProperty("planted_year")] public int? PlantedYear;
        [JsonProperty("reach")] public int Reach;
        [JsonProperty("longevity")] public int Longevity;
    }

    public sealed class Legacy
    {
        [JsonProperty("name")] public string Name;
        [JsonProperty("founder_life")] public string FounderLife;
        [JsonProperty("action")] public string Action;
        [JsonProperty("living")] public bool Living;
    }

    public sealed class CauseStep
    {
        [JsonProperty("year")] public int Year;
        [JsonProperty("phrase")] public string Phrase;
    }

    public sealed class CausePath
    {
        [JsonProperty("ref")] public string Ref;
        [JsonProperty("event")] public string Event;
        [JsonProperty("year")] public int Year;
        /// The events lying BETWEEN this consequence and its origin, effect-first.
        /// The two ends are not in the list: the consequence is (Event, Year) and
        /// the origin is (OriginAct, OriginYear). Empty means the origin caused
        /// this directly. Every adjacent pair is one edge the graph really holds.
        [JsonProperty("steps")] public List<CauseStep> Steps = new List<CauseStep>();
        [JsonProperty("origin_life")] public int OriginLife;
        [JsonProperty("origin_year")] public int OriginYear;
        [JsonProperty("origin_act")] public string OriginAct;
        /// C-6: false means the life did this on its own. Narrate as history,
        /// never as "the choice you made".
        [JsonProperty("origin_sealed")] public bool OriginSealed;
        /// Non-zero means this consequence has other contributing origins, and
        /// the surface is obliged to say so rather than imply sole causality.
        [JsonProperty("other_origins")] public int OtherOrigins;
        [JsonProperty("posthumous")] public bool Posthumous;
    }
}
