# Task 7 — A1 capacity retry runner on the Micro

Status: doing — runner written and simulated; console setup + install on the Micro pending
Est: 75m
Spec: SPEC.md §11 · D-008, D-009

What: A small loop on the E2.1.Micro that keeps trying to launch the A1 until Oracle has capacity, upgrades a 1/6 instance to 2/12 if that's what it got, then stops itself — and you get an email at each milestone.

Approach: OCI CLI on the Micro, authenticated as the instance itself (instance principal: a dynamic group plus a narrowly scoped policy, so no API key sits on the box). Launch parameters taken from the console's "Save as stack" or the instance form: compartment, availability domain, subnet OCID, Ubuntu 24.04 aarch64 image OCID, SSH public key. Runs as a systemd service. Email comes from an OCI Events rule (instance launch completed) → Notifications topic → email subscription, so it fires however the A1 gets created.

Read first:

- OCI CLI reference: `oci compute instance launch` (`--shape-config`, `--assign-public-ip`, `--user-data-file`, `--boot-volume-size-in-gbs`)
- OCI docs: Calling services from an instance (instance principals) and dynamic groups
- OCI docs: Events service + Notifications (email subscriptions)
- Oracle's sample policy "Let users launch compute instances" — base the scoped policy on it

Watch out for:

- Before every attempt, check whether an A1 already exists, and exit after success. A second A1 would exceed the free allowance, and at trial end Oracle disables all A1 instances (Task 3).
- Retry every 60–120 s with jitter. Back off on 429 TooManyRequests. Stop (don't loop) on LimitExceeded, auth, or validation errors.
- Pass `--user-data-file` with `infra/cloud-init.sh`, so the A1 configures itself on first boot.
- Shape strategy (D-009). Phase 1, acquire: each attempt asks for 2/12; on "Out of capacity", immediately ask for 1/6 in the same attempt. Phase 2, upgrade (only if phase 1 got 1/6): retry the resize to 2/12 on the same schedule until it succeeds. Why: freed capacity arrives in bursts (a deleted 4/24 VM frees room for 2/12, so asking big first grabs it), while 1/6 fits the smaller leftover gaps on crowded hosts. Asking for both costs one extra API call per attempt.
- Phase 2: check on a scratch run whether a resize rejected for capacity leaves the VM running. If a failed resize reboots or stops it, limit phase-2 attempts to a nightly window, since the VM may be serving by then.
- The quota policy makes mistakes harmless: a 2/12 launch is refused while a 1/6 A1 exists (3 cores > 2), and a disk past 200 GB is refused. Still check for an existing A1 before launching.
- Boot volume ≤ 100 GB while the Micro exists (200 GB total free storage).
- Policy scope: only what launching needs (instances, boot volume, use of the subnet/VNIC, reading images) — not tenancy admin.
- The Micro has 1 GB RAM: the CLI and the loop only, nothing else.
- Confirm the subscription link Oracle emails you, or no notification ever arrives.

Done when: the service runs and logs each attempt; a test notification email arrives; an A1 exists at 2 OCPU / 12 GB (directly, or 1/6 then resized); the service has stopped and disabled itself; then the Micro is terminated with its boot volume deleted.

---

Filled in while working

Files touched:

- infra/a1_runner.py, infra/test_a1_runner.py
- infra/a1-runner.service, infra/a1-runner.env.example, infra/install-a1-runner.sh

Decisions made here:

- Python + the `oci` SDK instead of a bash loop around the OCI CLI: errors arrive as typed `ServiceError(status, code, message)` instead of parsed stderr, and it's the project's language.
- The runner sends its own emails (publishes to the Notifications topic) instead of an Events rule. It emails only on A1 acquired (1/6 or 2/12), A1 found stopped and restarted, and runner stopped on an error. Capacity misses go to the log only. One less console resource.
- Compartment, availability domain, subnet and SSH key are read from the Micro itself (metadata endpoint + its VNIC), so the A1 lands in the same subnet with the same key, and the env file only holds TOPIC_OCID, INSTANCE_NAME, BOOT_VOLUME_GB, RESIZE_HOURS.
- Image is looked up each start (newest Canonical Ubuntu 24.04 for A1.Flex, Minimal skipped), so there's no image OCID to go stale.
- Phase 2 resizes only inside RESIZE_HOURS (IST), because a flex resize reboots the A1. If the A1 is found STOPPED, it's started again and you get an email.
- Exit codes: 0 done; 2 fatal (quota, auth, bad request; `RestartPreventExitStatus=2` keeps systemd from looping); anything else restarts after 60 s. On success it just exits; the Micro is terminated soon after, so no self-disable logic.
- Runs under systemd `DynamicUser=yes`: no login user owns it, and the instance principal comes from the metadata endpoint, not a file.
- Pure decision functions (`classify`, `decide`, `in_window`) are unit-tested; the full loop was simulated against fake OCI clients (capacity fallback, window wait, resize, stopped → start, 2/12 → exit 0; quota → exit 2).

Gotchas:

- First live run: TOPIC_OCID held the Micro's instance OCID, so publish failed with 400 InvalidParameter. Because that happened at setup it exited 1, and systemd would have restarted it every 60 s with no email. Fixed: the runner checks for an `ocid1.onstopic.` prefix before anything else, and any setup error exits 2 (no restart).
- Quota policy allowed 0 A1 cores: `zero compute-core quotas` also zeroes `standard-a1-core-regional-count`, and a launch must fit under both the per-AD and the regional count. Fix: also `set compute-core quota standard-a1-core-regional-count to 2 in tenancy`.
- After the first reboot, the 1/6 fallback got 429 TooManyRequests every round because it was sent within a second of the 2/12 attempt, so it was never really tried. A 30 s gap didn't help either (Oracle seems to allow about one LaunchInstance every couple of minutes per user). Fix: one launch per round, alternating 2/12 and 1/6. This replaces D-009's "both sizes in the same attempt"; each size is still tried every ~3–4 min.
- The python3-venv install prints needrestart's "Pending kernel upgrade" and then sits silent for minutes during `pip install oci` on the Micro. That's normal; reboot after the service is enabled.
- 24 h on 2026-10-06: 587 capacity misses, 154 throttled (429, ~17%) at 60-120 s rounds. Oracle documents no numeric or daily API limit, only "too many requests in a short time" + retry with backoff. Round gap is now `RETRY_SECONDS` in the env file (90-150): fewer 429s and their back-off, about the same number of real attempts.
