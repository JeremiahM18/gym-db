-- Dev-only seed data for manual testing
-- This file is safe to delete or replace at any time

INSERT INTO gyms (id, name, normalized_name, location)
VALUES
(
    'gym_iron_nashville',
    'Iron Nashville',
    'iron_nashville',
    ST_MakePoint(-86.7816, 36.1627)::geography
),
(
    'gym_east_strength',
    'East Strength',
    'east_strength',
    ST_MakePoint(-86.7468, 36.1762)::geography
),
(
    'gym_midtown_fitness',
    'Midtown Fitness',
    'midtown_fitness',
    ST_MakePoint(-86.8003, 36.1510)::geography
)