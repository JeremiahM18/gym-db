import { expect, test } from "@playwright/test";

type MockGym = {
  id: string;
  name: string;
  norm_name: string;
  lat: number;
  lon: number;
  confidence_score: number;
  osm_refs: Array<Record<string, number | string>>;
  tags: Record<string, string>;
  inference: Record<
    string,
    {
      value: boolean | number | string;
      confidence: number;
      reasons: string[];
      source: string;
    }
  >;
  inference_meta: {
    engine: string;
    version: string;
    generated_at: string;
    deterministic_hash: string;
    field_confidence: Record<string, number>;
    contradictions: Record<string, string[]>;
  };
  source_provenance: {
    primary: string;
    confirmed_by: string[];
    match_status: string;
    external_refs: Record<string, Record<string, string | number>>;
  };
  inference_summary: Record<string, string>;
};

function buildGym(overrides: Partial<MockGym> = {}): MockGym {
  const id = overrides.id ?? "gym-downtown-strength";
  const name = overrides.name ?? "Downtown Strength";

  return {
    id,
    name,
    norm_name: overrides.norm_name ?? name.toLowerCase().replaceAll(" ", "_"),
    lat: overrides.lat ?? 36.1627,
    lon: overrides.lon ?? -86.7816,
    confidence_score: overrides.confidence_score ?? 0.91,
    osm_refs: overrides.osm_refs ?? [{ type: "node", id: 101 }],
    tags: overrides.tags ?? {
      name,
      website: "https://example.com",
      phone: "615-555-0101",
      "addr:city": "Nashville",
      "addr:state": "TN",
      "addr:street": "Broadway",
      "addr:housenumber": "100",
      opening_hours: "24/7",
    },
    inference: overrides.inference ?? {
      specialty: {
        value: "powerlifting",
        confidence: 0.93,
        reasons: ["platform and rack density"],
        source: "rule",
      },
      tier: {
        value: "premium",
        confidence: 0.88,
        reasons: ["amenity coverage"],
        source: "rule",
      },
      lifter_friendly: {
        value: true,
        confidence: 0.91,
        reasons: ["barbell equipment detected"],
        source: "rule",
      },
      is_24_7: {
        value: true,
        confidence: 0.97,
        reasons: ["opening_hours=24/7"],
        source: "rule",
      },
    },
    inference_meta: overrides.inference_meta ?? {
      engine: "rule_based",
      version: "1.1.0",
      generated_at: "2026-04-16T00:00:00Z",
      deterministic_hash: `hash-${id}`,
      field_confidence: {
        specialty: 0.93,
        tier: 0.88,
      },
      contradictions: {},
    },
    source_provenance: overrides.source_provenance ?? {
      primary: "osm",
      confirmed_by: ["tomtom"],
      match_status: "matched",
      external_refs: {
        tomtom: {
          provider: "tomtom",
          external_id: `tt-${id}`,
          name,
          status: "matched",
          distance_m: 25,
        },
      },
    },
    inference_summary: overrides.inference_summary ?? {
      specialty: "powerlifting",
      tier: "premium",
      premium_score: "0.88",
    },
  };
}

const downtownStrength = buildGym();
const riverfrontBarbell = buildGym({
  id: "gym-riverfront-barbell",
  name: "Riverfront Barbell",
  lat: 36.167,
  lon: -86.779,
  confidence_score: 0.84,
  tags: {
    name: "Riverfront Barbell",
    website: "https://riverfront.example.com",
    phone: "615-555-0199",
    "addr:city": "Nashville",
    "addr:state": "TN",
    "addr:street": "Commerce St",
    "addr:housenumber": "401",
  },
  inference: {
    specialty: {
      value: "general_fitness",
      confidence: 0.61,
      reasons: ["mixed equipment profile"],
      source: "rule",
    },
    tier: {
      value: "mid",
      confidence: 0.58,
      reasons: ["moderate amenity coverage"],
      source: "rule",
    },
    lifter_friendly: {
      value: false,
      confidence: 0.63,
      reasons: ["limited barbell signals"],
      source: "rule",
    },
    is_24_7: {
      value: false,
      confidence: 0.55,
      reasons: ["hours not published"],
      source: "rule",
    },
  },
  inference_summary: {
    specialty: "general_fitness",
    tier: "mid",
    premium_score: "0.41",
  },
});

const gymsById = new Map(
  [downtownStrength, riverfrontBarbell].map((gym) => [gym.id, gym]),
);

test.beforeEach(async ({ page }) => {
  await page.route("**/v2/geocode**", async (route) => {
    await route.fulfill({
      status: 200,
      contentType: "application/json",
      body: JSON.stringify({
        api_version: "2.0.0",
        query: "Nashville, TN",
        count: 1,
        results: [
          {
            id: "place-1",
            name: "Nashville, TN",
            lat: 36.1627,
            lon: -86.7816,
            address: "Nashville, TN",
            city: "Nashville",
            country_code: "US",
          },
        ],
      }),
    });
  });

  await page.route("**/healthz", async (route) => {
    await route.fulfill({ status: 200, body: "{}" });
  });

  await page.route("**/readyz", async (route) => {
    await route.fulfill({
      status: 200,
      contentType: "application/json",
      body: JSON.stringify({
        status: "ok",
        ruleset_version: "1.1.0",
      }),
    });
  });

  await page.route("**/v2/gyms/*", async (route) => {
    const url = new URL(route.request().url());
    const gymId = url.pathname.split("/").pop() ?? "";
    const gym = gymsById.get(gymId) ?? downtownStrength;

    await route.fulfill({
      status: 200,
      contentType: "application/json",
      body: JSON.stringify({
        api_version: "2.0.0",
        gym,
      }),
    });
  });

  await page.route("**/v2/gyms**", async (route) => {
    const url = new URL(route.request().url());
    if (url.pathname !== "/v2/gyms") {
      await route.fallback();
      return;
    }
    const specialty = url.searchParams.get("specialty");
    const hasNearby = url.searchParams.has("lat");

    const results = hasNearby
      ? [riverfrontBarbell]
      : specialty === "powerlifting"
        ? [downtownStrength]
        : [downtownStrength, riverfrontBarbell];

    await route.fulfill({
      status: 200,
      contentType: "application/json",
      body: JSON.stringify({
        api_version: "2.0.0",
        region: "tn_nashville",
        count: results.length,
        has_more: false,
        results,
      }),
    });
  });
});

test("loads the catalog and selected gym details", async ({ page }) => {
  await page.goto("/");

  await expect(
    page.getByRole("heading", {
      name: /Find gyms, inspect inference/i,
    }),
  ).toBeVisible();
  await expect(page.getByText("API live: yes")).toBeVisible();
  await expect(page.getByRole("button", { name: /Downtown Strength/i })).toBeVisible();
  await expect(page.getByRole("heading", { name: "Selected Gym" })).toBeVisible();
  await expect(
    page.getByRole("heading", { level: 3, name: "Downtown Strength" }),
  ).toBeVisible();
});

test("refreshes the catalog with a server-backed specialty filter", async ({ page }) => {
  await page.goto("/");

  await page.getByLabel("Specialty").selectOption("powerlifting");
  await page.getByRole("button", { name: "Refresh catalog" }).click();

  await expect(page.getByRole("button", { name: /Downtown Strength/i })).toBeVisible();
  await expect(page.getByRole("button", { name: /Riverfront Barbell/i })).toHaveCount(0);
  await expect(page.getByText("Lead specialty").locator("..")).toContainText(
    "Powerlifting",
  );
});

test("runs nearby search and switches the browser into nearby mode", async ({ page }) => {
  await page.goto("/");

  await page.getByRole("button", { name: "Run nearby search" }).click();

  await expect(page.getByRole("button", { name: /^Nearby$/ })).toBeEnabled();
  await expect(page.getByRole("button", { name: /Riverfront Barbell/i })).toBeVisible();
  await expect(
    page.getByRole("heading", { level: 3, name: "Riverfront Barbell" }),
  ).toBeVisible();
  await expect(page.getByText("Open in Maps").first()).toBeVisible();
  await expect(page.getByText(/Resolved search origin:/i)).toContainText("Nashville, TN");
});
