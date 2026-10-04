"""A1 capacity retry runner (sprint-1/task_7, D-008, D-009). Runs on the E2.1.Micro.

Loop: no A1 → launch, alternating 2/12 and 1/6 per round ·
A1 at 1/6 → resize to 2/12 inside RESIZE_HOURS · A1 running at 2/12 → exit.
Emails (OCI Notifications topic) only when an A1 is acquired or resized, or when the runner
stops on an error; capacity misses only go to the log.

Auth is the Micro's instance principal (no API key on disk). Compartment, availability domain,
subnet and SSH key are read from the Micro itself, so the A1 lands next to it with the same key.
Config (env, /etc/a1-runner.env): TOPIC_OCID, INSTANCE_NAME, BOOT_VOLUME_GB, RESIZE_HOURS.

Exit codes: 0 done · 2 fatal (systemd won't restart; you get an email) · 1 crash (systemd restarts).
"""

import base64
import json
import os
import random
import sys
import time
import urllib.request
from datetime import datetime
from pathlib import Path

SHAPE = "VM.Standard.A1.Flex"
SIZES = [(2, 12), (1, 6)]  # D-009: big one first, then the gap-filler; alternated per round
CLOUD_INIT = Path(__file__).with_name("cloud-init.sh")
GONE = {"TERMINATED", "TERMINATING"}


def log(msg: str) -> None:
    print(f"{datetime.now():%Y-%m-%d %H:%M:%S} {msg}", flush=True)


# --- pure decisions (tested in test_a1_runner.py) ---


def classify(status: int, code: str, message: str) -> str:
    """capacity | throttled | transient | fatal"""
    if "capacity" in message.lower():
        return "capacity"
    if status == 429:
        return "throttled"
    if status >= 500 or status == 409:
        return "transient"
    # 400 LimitExceeded/QuotaExceeded/InvalidParameter, 401, 404 NotAuthorizedOrNotFound
    return "fatal"


def in_window(hour: int, window: str) -> bool:
    start, end = map(int, window.split("-"))
    return start <= hour < end if start <= end else hour >= start or hour < end


def decide(a1s: list, hour: int, window: str) -> str:
    """launch | wait | start | resize | done | fatal"""
    if not a1s:
        return "launch"
    if len(a1s) > 1:
        return "fatal"
    a1 = a1s[0]
    if a1.lifecycle_state == "STOPPED":
        return "start"
    if a1.lifecycle_state != "RUNNING":
        return "wait"
    if a1.shape_config.ocpus >= 2:
        return "done"
    return "resize" if in_window(hour, window) else "wait"


# --- OCI side ---


def metadata(path: str):
    req = urllib.request.Request(
        f"http://169.254.169.254/opc/v2/{path}", headers={"Authorization": "Bearer Oracle"}
    )
    with urllib.request.urlopen(req, timeout=5) as r:
        return json.load(r)


def main() -> int:
    import oci  # imported here so the pure functions above are testable without the SDK

    topic, name = os.environ["TOPIC_OCID"], os.environ["INSTANCE_NAME"]
    boot_gb, window = int(os.environ["BOOT_VOLUME_GB"]), os.environ["RESIZE_HOURS"]

    if not topic.startswith("ocid1.onstopic."):
        log(f"TOPIC_OCID must be a topic OCID (ocid1.onstopic...), got {topic[:30]}...")
        return 2

    signer = oci.auth.signers.InstancePrincipalsSecurityTokenSigner()
    compute = oci.core.ComputeClient({}, signer=signer)
    network = oci.core.VirtualNetworkClient({}, signer=signer)
    ons = oci.ons.NotificationDataPlaneClient({}, signer=signer)

    def notify(title: str, body: str = "") -> None:
        log(f"NOTIFY {title} {body}")
        details = oci.ons.models.MessageDetails(title=f"[ask-ragu] {title}", body=body or title)
        ons.publish_message(topic, details)

    def fatal(title: str, err: Exception | str) -> int:
        notify(f"A1 runner stopped: {title}", str(err))
        return 2

    # Setup errors are config/policy mistakes: stop (exit 2) instead of a silent restart loop,
    # since the email path itself may be what's broken.
    try:
        me = metadata("instance/")
        compartment, ad = me["compartmentId"], me["availabilityDomain"]
        ssh_key = me["metadata"]["ssh_authorized_keys"]
        subnet = network.get_vnic(metadata("vnics/")[0]["vnicId"]).data.subnet_id
        images = compute.list_images(
            compartment,
            operating_system="Canonical Ubuntu",
            operating_system_version="24.04",
            shape=SHAPE,
            sort_by="TIMECREATED",
            sort_order="DESC",
        ).data
        image = next(i for i in images if "Minimal" not in i.display_name)
        user_data = base64.b64encode(CLOUD_INIT.read_bytes()).decode()
        log(f"image {image.display_name}, ad {ad}, boot {boot_gb} GB, resize window {window}")
    except oci.exceptions.ServiceError as e:
        log(f"setup failed — fix config/policy, then restart: {e.status} {e.code} {e.message}")
        return 2

    def launch(ocpus: int, mem: int) -> None:
        compute.launch_instance(
            oci.core.models.LaunchInstanceDetails(
                compartment_id=compartment,
                availability_domain=ad,
                display_name=name,
                shape=SHAPE,
                shape_config=oci.core.models.LaunchInstanceShapeConfigDetails(
                    ocpus=ocpus, memory_in_gbs=mem
                ),
                source_details=oci.core.models.InstanceSourceViaImageDetails(
                    image_id=image.id, boot_volume_size_in_gbs=boot_gb
                ),
                create_vnic_details=oci.core.models.CreateVnicDetails(
                    subnet_id=subnet, assign_public_ip=True
                ),
                metadata={"ssh_authorized_keys": ssh_key, "user_data": user_data},
            )
        )

    announced: set[tuple[str, float]] = set()
    pause = 0  # extra back-off after 429s
    attempt = 0
    while True:
        try:
            a1s = [
                i
                for i in oci.pagination.list_call_get_all_results(
                    compute.list_instances, compartment
                ).data
                if i.shape == SHAPE and i.lifecycle_state not in GONE
            ]
            action = decide(a1s, datetime.now().hour, window)
            a1 = a1s[0] if a1s else None

            if a1 and a1.lifecycle_state == "RUNNING":
                ocpus, mem = a1.shape_config.ocpus, a1.shape_config.memory_in_gbs
                if (a1.id, ocpus) not in announced:
                    announced.add((a1.id, ocpus))
                    if ocpus >= 2:
                        title = f"A1 acquired at {ocpus:g} OCPU / {mem:g} GB — you're done"
                    else:
                        title = f"A1 acquired at {ocpus:g} OCPU / {mem:g} GB — resize to 2/12 next"
                    notify(title, f"{a1.id}\nNext: Sprint 1 Tasks 4-6 (D-008).")

            if action == "done":
                log("A1 is at 2/12 — nothing left to do")
                return 0
            if action == "fatal":
                return fatal("more than one A1 exists", ", ".join(i.id for i in a1s))
            if action == "launch":
                # One launch per round, alternating sizes: a second launch in the same
                # round is reliably 429 TooManyRequests.
                ocpus, mem = SIZES[attempt % len(SIZES)]
                attempt += 1
                try:
                    launch(ocpus, mem)
                    log(f"launch accepted at {ocpus}/{mem}")
                except oci.exceptions.ServiceError as e:
                    if classify(e.status, e.code, e.message) != "capacity":
                        raise
                    log(f"out of capacity at {ocpus}/{mem}")
            elif action == "resize":
                compute.update_instance(
                    a1.id,
                    oci.core.models.UpdateInstanceDetails(
                        shape_config=oci.core.models.UpdateInstanceShapeConfigDetails(
                            ocpus=2, memory_in_gbs=12
                        )
                    ),
                )
                log("resize to 2/12 accepted")
            elif action == "start":
                compute.instance_action(a1.id, "START")
                notify("A1 was STOPPED (failed resize?) — started it again", a1.id)
            else:
                log(f"waiting ({a1.lifecycle_state}, {a1.shape_config.ocpus:g} OCPU)")
            pause = 0
        except oci.exceptions.ServiceError as e:
            kind = classify(e.status, e.code, e.message)
            log(f"{kind}: {e.status} {e.code} {e.message}")
            if kind == "fatal":
                return fatal(f"{e.status} {e.code}", e.message)
            if kind == "throttled":
                pause = min(pause * 2 or 120, 900)
        except (oci.exceptions.RequestException, OSError) as e:
            log(f"network: {e}")

        time.sleep(random.uniform(60, 120) + pause)


if __name__ == "__main__":
    sys.exit(main())
