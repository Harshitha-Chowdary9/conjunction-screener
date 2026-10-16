# Study guide: talking about this project

Questions you might get about this repo, with short answers.

**What is a TLE?**
A two-line element set: the standard public format for a satellite's orbit,
published by the US Space Command and mirrored by CelesTrak. It encodes the
classical orbital elements plus drag terms in two 69-character lines.

**What is SGP4?**
The propagator designed to go with TLEs. Given a TLE and a time, it returns
the satellite's position and velocity in the TEME inertial frame. It models
Earth's oblateness and atmospheric drag. The `sgp4` Python package is the
reference implementation.

**How does the screening work?**
Propagate both objects on a time grid (60 s steps over 24 h), compute the
separation at each step, flag local minima below a threshold, then refine
each candidate between its neighbouring grid points with a golden-section
search for sub-second timing.

**Why golden-section search?**
The distance function is smooth and unimodal near a minimum, so a
derivative-free bracketing method converges reliably without gradients.

**What would a real system add?**
Covariance and probability of collision (Monte Carlo or analytical),
much larger catalogs with spatial indexing (e.g. k-d trees) instead of
all-pairs, better force models, and alert workflows. This project keeps
only the geometry, on purpose.

**What are the limits of TLE data?**
Kilometre-level position errors, they go stale within days, and they carry
no uncertainty estimate, which is why real conjunction assessment uses
better data (e.g. operator ephemerides, tracking sensors).
