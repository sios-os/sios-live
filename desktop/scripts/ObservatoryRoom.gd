## ObservatoryRoom.gd — The Observatory room controller.
##
## The Observatory shows the evidence ledger — the tamper-evident record
## of everything ANUBIS has done. This is the audit trail.
extends "res://scripts/RoomController.gd"

func _on_room_enter() -> void:
	_refresh()

func _refresh() -> void:
	_set_loading("Loading evidence ledger...")
	var r := _ipc_call("get_ledger_summary")
	if r.has("error"):
		_set_error(r["error"])
		return
	var ok: bool = r.get("integrity_ok", false)
	var text := "OBSERVATORY — Evidence Ledger\n"
	text += "================================\n\n"
	text += "Entries:     %d\n" % r.get("entries", 0)
	text += "Integrity:   %s\n" % ("VERIFIED" if ok else "BROKEN")
	text += "             %s\n" % r.get("integrity_msg", "")
	text += "Head hash:   %s...\n\n" % str(r.get("head", "")).substr(0, 32)
	if ok:
		text += "The chain is intact.\n"
		text += "Every action ANUBIS has taken is\n"
		text += "recorded and cannot be altered\n"
		text += "without detection.\n"
	else:
		text += "WARNING: Chain integrity broken!\n"
		text += "The ledger may have been tampered.\n"
	_set_content(text)
