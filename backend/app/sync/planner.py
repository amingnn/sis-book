def choose_sync_direction(local_meta: dict, remote_manifest: dict | None, state: dict) -> str:
    if remote_manifest is None:
        return "push"

    remote_changed = remote_manifest.get("signature", "") != state.get("last_remote_signature", "")
    local_changed = local_meta.get("signature", "") != state.get("last_local_signature", "")

    if remote_changed and not local_changed:
        return "pull"
    if local_changed and not remote_changed:
        return "push"
    if remote_changed and local_changed:
        return "conflict"
    return "noop"
