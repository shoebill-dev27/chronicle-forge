// Load the one fixture every concept reads.
//
// It lives in Resources so all three load the identical bytes by construction —
// a comparison between concepts is only worth anything if the world underneath
// them is the same world. The hash is checked on load for the same reason the
// book store checks it (CS-2): a fixture that is not the world these
// coordinates were minted in would render real-looking nonsense.

using System;
using ChronicleForge.Model;
using Newtonsoft.Json;
using UnityEngine;

namespace ChronicleForge.Core
{
    public static class FixtureLoader
    {
        public const string ResourcePath = "dvs_fixture";

        /// The engine build this client was transcribed against. A fixture from
        /// another engine is refused rather than half-read: the fields may have
        /// the same names and mean different things.
        public const string ExpectedEngineVersion = "0.1.0-p8-mvp";

        public static DvsFixture Load(string resourcePath = ResourcePath)
        {
            TextAsset asset = Resources.Load<TextAsset>(resourcePath);
            if (asset == null)
                throw new InvalidOperationException(
                    $"no fixture at Resources/{resourcePath}.json — run " +
                    "`python -m chronicle_forge.client.fixture` to export one");
            return Parse(asset.text);
        }

        /// Separated from Load so it is testable without an asset database.
        public static DvsFixture Parse(string json)
        {
            DvsFixture fixture;
            try
            {
                fixture = JsonConvert.DeserializeObject<DvsFixture>(json);
            }
            catch (JsonException exc)
            {
                throw new InvalidOperationException("fixture is not readable json", exc);
            }
            if (fixture?.Stream == null)
                throw new InvalidOperationException("fixture carries no beat stream");
            if (string.IsNullOrEmpty(fixture.CanonicalHash))
                throw new InvalidOperationException("fixture carries no world identity");
            if (fixture.EngineVersion != ExpectedEngineVersion)
                throw new InvalidOperationException(
                    $"fixture recorded under engine {fixture.EngineVersion}, " +
                    $"this client was transcribed against {ExpectedEngineVersion}");
            if (fixture.Stream.Beats.Count == 0)
                throw new InvalidOperationException("a fixture with no beats describes no world");
            return fixture;
        }
    }
}
