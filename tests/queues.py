"""Waiting queues as older versions left them on disk, now that nothing new waits on its own (backlog 28)."""

from jarvis import faces


def queue(gallery, entry_id, embeddings, crop=None):
    """Write views straight into an entry's Waiting, each with its own photo when crop is given."""
    with faces._GALLERY_LOCK:
        gallery.load()
        entry = gallery.get(entry_id)
        entry.setdefault("pending", []).extend(
            {"embedding": e, "view": gallery._store_view(crop)} for e in embeddings)
        gallery.save()
