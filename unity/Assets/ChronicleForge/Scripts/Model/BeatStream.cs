// The beats, and the envelope they arrive in.
//
// `beats` is a discriminated union in Python — every entry carries a "t" field
// naming its kind. Newtonsoft cannot pick a subclass from that on its own, so
// BeatConverter reads "t" and constructs the right type. The alternative (one
// wide struct with every field of every beat) would make "did this beat have a
// recognition?" unanswerable, and that question is the whole discovery loop.

using System;
using System.Collections.Generic;
using Newtonsoft.Json;
using Newtonsoft.Json.Linq;

namespace ChronicleForge.Model
{
    public abstract class Beat
    {
        [JsonProperty("t")] public string Kind;
    }

    public sealed class Rebirth : Beat
    {
        [JsonProperty("life")] public int LifeOrdinal;
        [JsonProperty("year")] public int Year;
        [JsonProperty("talent")] public string Talent;
        [JsonProperty("era")] public string Era;
    }

    public sealed class Juncture : Beat
    {
        [JsonProperty("life")] public int LifeOrdinal;
        [JsonProperty("year")] public int Year;
        [JsonProperty("age")] public int Age;
        [JsonProperty("reason")] public string Reason;
        /// The engine's own framing phrase. Printed, never paraphrased.
        [JsonProperty("header")] public string Header;
        [JsonProperty("era")] public string Era;
        [JsonProperty("options")] public List<Option> Options = new List<Option>();
        [JsonProperty("recognition")] public Recognition Recognition;
    }

    public sealed class Outcome : Beat
    {
        [JsonProperty("life")] public int LifeOrdinal;
        [JsonProperty("year")] public int Year;
        [JsonProperty("age")] public int Age;
        /// The displayed number sealed; 0 when the season was let pass.
        [JsonProperty("option")] public int OptionNumber;
        [JsonProperty("label")] public string Label;
        [JsonProperty("kind")] public string Kind_;
        /// Causal seeds this act set in motion. A life that planted nothing must
        /// not be told that it did.
        [JsonProperty("planted")] public int Planted;
    }

    public sealed class Death : Beat
    {
        [JsonProperty("life")] public int LifeOrdinal;
        [JsonProperty("year")] public int Year;
        [JsonProperty("age")] public int Age;
        [JsonProperty("talent")] public string Talent;
        [JsonProperty("title")] public string Title;
        [JsonProperty("named")] public List<string> Named = new List<string>();
        [JsonProperty("pending")] public int Pending;
        [JsonProperty("seed_years")] public List<int> SeedYears = new List<int>();
    }

    public sealed class Years : Beat
    {
        [JsonProperty("after_life")] public int AfterLife;
        [JsonProperty("from_year")] public int FromYear;
        [JsonProperty("to_year")] public int ToYear;
        [JsonProperty("span")] public int Span;
        [JsonProperty("world_ended")] public bool WorldEnded;
        [JsonProperty("events")] public List<WorldEvent> Events = new List<WorldEvent>();
    }

    public sealed class Aftermath : Beat
    {
        [JsonProperty("after_life")] public int AfterLife;
        [JsonProperty("year")] public int Year;
        [JsonProperty("echoes")] public List<WorldEvent> Echoes = new List<WorldEvent>();
        [JsonProperty("hardened")] public List<Mark> Hardened = new List<Mark>();
        /// P-10's digest: at most three lines, already cut on the Python side.
        [JsonProperty("changes")] public List<Change> Changes = new List<Change>();
    }

    public sealed class Closing : Beat
    {
        [JsonProperty("year")] public int Year;
        [JsonProperty("lives")] public int Lives;
        [JsonProperty("ending")] public string Ending;
        [JsonProperty("legacies")] public List<Legacy> Legacies = new List<Legacy>();
        /// The threads the finished book can honestly offer (C-3). Nothing here
        /// is shown until the reader inspects: reading confirms nothing.
        [JsonProperty("cases")] public List<CausePath> Cases = new List<CausePath>();
    }

    public sealed class BeatConverter : JsonConverter
    {
        public override bool CanWrite => false;
        public override bool CanConvert(Type t) => t == typeof(Beat);

        public override object ReadJson(JsonReader r, Type t, object existing, JsonSerializer s)
        {
            JObject o = JObject.Load(r);
            string kind = (string)o["t"];
            Beat beat = kind switch
            {
                "rebirth" => new Rebirth(),
                "juncture" => new Juncture(),
                "outcome" => new Outcome(),
                "death" => new Death(),
                "years" => new Years(),
                "aftermath" => new Aftermath(),
                "closing" => new Closing(),
                // Fail loud. A beat kind this build does not know is a stream
                // from a newer engine, and guessing at it would draw a page out
                // of fields whose meaning has changed.
                _ => throw new JsonSerializationException($"unknown beat kind '{kind}'"),
            };
            s.Populate(o.CreateReader(), beat);
            return beat;
        }

        public override void WriteJson(JsonWriter w, object v, JsonSerializer s) =>
            throw new NotSupportedException("the fixture is read-only");
    }

    public sealed class WorldBeats
    {
        [JsonProperty("seed")] public int Seed;
        [JsonProperty("place")] public string Place;
        [JsonProperty("max_year")] public int MaxYear;
        [JsonProperty("end_year")] public int EndYear;
        [JsonProperty("ending")] public string Ending;
        [JsonProperty("lives")] public List<Life> Lives = new List<Life>();

        [JsonProperty("beats")]
        [JsonConverter(typeof(BeatListConverter))]
        public List<Beat> Beats = new List<Beat>();
    }

    /// Applies BeatConverter to each element of the list.
    public sealed class BeatListConverter : JsonConverter
    {
        public override bool CanWrite => false;
        public override bool CanConvert(Type t) => t == typeof(List<Beat>);

        public override object ReadJson(JsonReader r, Type t, object existing, JsonSerializer s)
        {
            var list = new List<Beat>();
            var one = new BeatConverter();
            foreach (JObject o in JArray.Load(r))
            {
                using JsonReader sub = o.CreateReader();
                sub.Read();
                list.Add((Beat)one.ReadJson(sub, typeof(Beat), null, s));
            }
            return list;
        }

        public override void WriteJson(JsonWriter w, object v, JsonSerializer s) =>
            throw new NotSupportedException("the fixture is read-only");
    }

    public sealed class Discovery
    {
        /// Every coordinate that starts hidden. The gate is over these refs.
        [JsonProperty("locked")] public List<string> Locked = new List<string>();
    }

    public sealed class DvsFixture
    {
        [JsonProperty("fixture_version")] public string FixtureVersion;
        [JsonProperty("engine_version")] public string EngineVersion;
        /// The identity of this exact world as grown under these inputs.
        [JsonProperty("canonical_hash")] public string CanonicalHash;
        [JsonProperty("inputs")] public List<string> Inputs = new List<string>();
        [JsonProperty("stream")] public WorldBeats Stream;
        [JsonProperty("discovery")] public Discovery Discovery;
    }
}
