-- Dev-only seed data for manual testing
-- Mirrors the shipped Nashville default dataset so fresh Docker boots open
-- with a credible 10-mile product state.

BEGIN;

INSERT INTO gyms (id, name, normalized_name, location)
VALUES
(
    'c2e0b5b79dcb5fad',
    'Irontribe',
    'irontribe',
    ST_SetSRID(ST_MakePoint(-86.8026025, 36.0313359), 4326)::geography
),
(
    '482059a81c081947',
    'Maryland Farms YMCA',
    'maryland_farms_ymca',
    ST_SetSRID(ST_MakePoint(-86.797395, 36.032016), 4326)::geography
),
(
    '834d79fb999429e2',
    'Crossfit',
    'crossfit',
    ST_SetSRID(ST_MakePoint(-86.8536331, 36.1524177), 4326)::geography
),
(
    '0e2430676d5394a4',
    'Planet Fitness',
    'planet_fitness',
    ST_SetSRID(ST_MakePoint(-86.8606197, 36.1502416), 4326)::geography
),
(
    '6a0846002f21a555',
    'Anytime Fitness',
    'anytime_fitness',
    ST_SetSRID(ST_MakePoint(-86.6847291, 36.1703201), 4326)::geography
),
(
    'a7512ff862676458',
    'Orangetheory Fitness',
    'orangetheory_fitness',
    ST_SetSRID(ST_MakePoint(-86.7934916, 36.1520644), 4326)::geography
),
(
    '6877cbcf0ee96232',
    'Steadfast South',
    'steadfast_south',
    ST_SetSRID(ST_MakePoint(-86.7529354, 36.1272205), 4326)::geography
),
(
    'b0c4f02a504fe745',
    'Planet Fitness',
    'planet_fitness',
    ST_SetSRID(ST_MakePoint(-86.7144739, 36.1267985), 4326)::geography
),
(
    'ff442cf722899c08',
    'Donelson Hot Yoga',
    'donelson_hot_yoga',
    ST_SetSRID(ST_MakePoint(-86.6804878, 36.1696659), 4326)::geography
),
(
    '5c4e0e63046c2116',
    'Chestnut Hill Yoga',
    'chestnut_hill_yoga',
    ST_SetSRID(ST_MakePoint(-86.76633, 36.1465593), 4326)::geography
),
(
    'e738916f7db2df5f',
    'Cross Fit Forte',
    'cross_fit_forte',
    ST_SetSRID(ST_MakePoint(-86.7703615, 36.1487305), 4326)::geography
),
(
    '5a0d4bafed8fe41c',
    'H Dub Athletics',
    'h_dub_athletics',
    ST_SetSRID(ST_MakePoint(-86.7667197, 36.147362), 4326)::geography
),
(
    '74f6878a07627bd3',
    'Urban Strength Gym',
    'urban_strength_gym',
    ST_SetSRID(ST_MakePoint(-86.7667864, 36.1474714), 4326)::geography
),
(
    '142d9becccf7895b',
    'Orangetheory Fitness',
    'orangetheory_fitness',
    ST_SetSRID(ST_MakePoint(-86.7847875, 36.1613964), 4326)::geography
),
(
    '1ebc04bbe2917be1',
    'Legacy Fitness Center',
    'legacy_fitness_center',
    ST_SetSRID(ST_MakePoint(-86.6231675, 36.1948691), 4326)::geography
),
(
    '35d25697c850ffba',
    'Heron Pointe Gym',
    'heron_pointe_gym',
    ST_SetSRID(ST_MakePoint(-86.6298171, 36.1182022), 4326)::geography
),
(
    '1d9f20c67149bf8f',
    'Climb West',
    'climb_west',
    ST_SetSRID(ST_MakePoint(-86.8280456, 36.1530445), 4326)::geography
),
(
    'afac5feef65d7ac8',
    'Hot Yoga of East Nashville',
    'hot_yoga_of_east_nashville',
    ST_SetSRID(ST_MakePoint(-86.7583513, 36.1758081), 4326)::geography
),
(
    '3cbd7d45f96603b8',
    'Climb Nashville East',
    'climb_nashville_east',
    ST_SetSRID(ST_MakePoint(-86.7355516, 36.1816982), 4326)::geography
),
(
    '979501015f94edf4',
    'Climb Nashville Kraft',
    'climb_nashville_kraft',
    ST_SetSRID(ST_MakePoint(-86.757443, 36.1088619), 4326)::geography
),
(
    'cea8c79f95a0b4fb',
    'Quantify Fitness',
    'quantify_fitness',
    ST_SetSRID(ST_MakePoint(-86.7504803, 36.1744054), 4326)::geography
),
(
    '34867d6d0548f743',
    'Iconix Fitness',
    'iconix_fitness',
    ST_SetSRID(ST_MakePoint(-86.7853087, 36.1608124), 4326)::geography
),
(
    'b8a84e80576203ca',
    'YMCA Donelson-Hermitage',
    'ymca_donelson_hermitage',
    ST_SetSRID(ST_MakePoint(-86.6486517, 36.1718555), 4326)::geography
),
(
    '94fac49c1b87971f',
    'Dalewood Baptist Church - Christian Life Center',
    'dalewood_baptist_church_christian_life_center',
    ST_SetSRID(ST_MakePoint(-86.7159848, 36.2080299), 4326)::geography
),
(
    'cbcdacab5db27031',
    'CrossFit Donelson',
    'crossfit_donelson',
    ST_SetSRID(ST_MakePoint(-86.6731142, 36.1715509), 4326)::geography
),
(
    '258f152395daca99',
    'Planet Fitness',
    'planet_fitness',
    ST_SetSRID(ST_MakePoint(-86.6293155, 36.1908753), 4326)::geography
)
ON CONFLICT (id) DO UPDATE
SET
    name = EXCLUDED.name,
    normalized_name = EXCLUDED.normalized_name,
    location = EXCLUDED.location;

COMMIT;
