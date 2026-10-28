"""Corrected compaction fixtures for the adapter-contract retest (2026-10-27).

Eight semantic cases plus the official Billing control. The construction rules
the previous fixture violated are enforced here:

- a recent-copy pair always carries the inputs of its own read, so the newer
  observation is internally consistent (the N09-N12 defect);
- every candidate output exceeds the fast-jev 420-character truncation floor,
  so drop_result really truncates, and required facts are placed inside or
  beyond the first 300 characters by design;
- recovery availability is declared per case, hashed, restated in the
  transcript note and re-emitted in the adapter state;
- the private oracle is machine-checkable: validate_specs asserts placement,
  uniqueness and internal consistency before anything is frozen.
"""
from __future__ import annotations

import hashlib
from collections import Counter

BODY = {
    "en": ("Collector status: capture completed normally; line boundaries follow the original source. "
           "The record belongs to the requested operation and the collector added no interpretation.\n"
           "Transport metadata: UTF-8 text; no binary attachment; sequence counter 006; local fixture clock.\n"
           "Diagnostic notes: parser accepted the input, transport closed cleanly, and no retry was issued. "
           "End of collector metadata.\n"),
    "it": ("Stato raccolta: acquisizione completata; i confini delle righe seguono la sorgente originale. "
           "Il registro appartiene all'operazione richiesta e il raccoglitore non aggiunge interpretazioni.\n"
           "Metadati: testo UTF-8; nessun allegato binario; contatore 006; orologio locale della fixture.\n"
           "Note diagnostiche: input accettato, trasporto chiuso correttamente, nessun tentativo ripetuto. "
           "Fine dei metadati di raccolta.\n"),
}

NEUTRAL = {
    "en": "No further observations have been recorded; the requested task is still open.",
    "it": "Non sono registrate altre osservazioni; il compito richiesto resta aperto.",
}

RECOVERY_NOTE = {
    "en": "Read-only recovery remains available: {path}; SHA256={sha}. One additional read of this immutable snapshot is permitted.",
    "it": "Recupero in sola lettura disponibile: {path}; SHA256={sha}. È consentita una lettura aggiuntiva di questa istantanea immutabile.",
}


def _message(role, text="", calls=None, results=None):
    item = {"role": role, "text": text, "toolUses": calls or []}
    if results is not None:
        item["toolResults"] = results
    return item


def _pair(tool, inputs, text, use_id, error=False):
    return [
        _message("assistant", calls=[{"tool_use_id": use_id, "tool": tool, "input": inputs}]),
        _message("user", results=[{"tool_use_id": use_id, "text": text, "isError": error}]),
    ]


def _output(detail, language, tail):
    body = BODY[language]
    result = (body + detail) if tail else (detail + "\n" + body)
    if not 421 <= len(result) <= 820:
        raise ValueError(f"candidate output outside fixture budget: {len(result)}")
    return result


def build_specs():
    """Return the eight retest cases with their private oracles."""
    rows = []

    def add(case_id, language, family, goal, tool, inputs, detail, required, expected,
            *, tail, recovery_path=None, recent=None, error=False, rationale=""):
        output = _output(detail, language, tail)
        messages = [_message("user", goal), *_pair(tool, inputs, output, "candidate", error=error)]
        messages.extend(_message("assistant", NEUTRAL[language]) for _ in range(6))
        recent_entry = None
        if recent is not None:
            recent_tool, recent_inputs, recent_detail = recent
            recent_output = _output(recent_detail, language, tail)
            messages.extend(_pair(recent_tool, recent_inputs, recent_output, "recent-copy"))
            recent_entry = {"tool": recent_tool, "inputs": recent_inputs, "detail": recent_detail,
                            "output": recent_output, "placement": "tail" if tail else "head"}
        recovery_entry = None
        if recovery_path is not None:
            digest = hashlib.sha256(output.encode("utf-8")).hexdigest()
            note = RECOVERY_NOTE[language].format(path=recovery_path, sha=digest)
            messages.append(_message("user", note))
            recovery_entry = {"path": recovery_path, "content": output, "sha256": digest, "note": note}
        rows.append({
            "id": case_id, "language": language, "family": family, "goal": goal,
            "messages": messages,
            "candidate": {"tool": tool, "input": inputs, "output": output, "is_error": error},
            "recent": recent_entry,
            "recovery": recovery_entry,
            "oracle": {"expected_action": expected, "required_facts": list(required), "rationale": rationale},
        })

    add("T01", "en", "prefix_only",
        "Quote the rejection code and the shard recorded for upload UQ-201. "
        "The probe has expired and no second copy of its output exists.",
        "ReadProbe", {"probe": "UQ-201"},
        "upload=UQ-201; rejection=QUOTA_WINDOW_CLOSED; shard=west-14",
        ("QUOTA_WINDOW_CLOSED", "west-14"), "drop_result", tail=False,
        rationale="Both required facts sit inside the first 300 characters that a dropped output keeps; "
                  "removing the whole pair would lose them and no recovery source exists.")

    add("T02", "it", "prefix_only",
        "Riporta il codice di guasto e il nodo registrati per la prova temporanea ZP-413. "
        "Il contenitore è stato eliminato e non esistono altre copie.",
        "LeggiTraccia", {"prova": "ZP-413"},
        "prova=ZP-413; guasto=SCHEMA_REV_MISMATCH; nodo=edge-27",
        ("SCHEMA_REV_MISMATCH", "edge-27"), "drop_result", tail=False,
        rationale="I fatti richiesti stanno nei primi 300 caratteri conservati; eliminare l'intera coppia "
                  "li perderebbe senza recupero.")

    add("T03", "en", "beyond_prefix",
        "Report whether migration MIG-401 was applied and quote the recorded blocker. "
        "The preflight environment is finished and nothing can be re-run.",
        "CheckMigration", {"migration": "MIG-401"},
        "migration=MIG-401; applied=false; blocker=FOREIGN_KEY_CYCLE",
        ("applied=false", "FOREIGN_KEY_CYCLE"), "keep", tail=True, error=True,
        rationale="The recorded outcome and blocker are beyond the 300-character prefix and cannot be "
                  "recovered or re-run; only the full output preserves them.")

    add("T04", "it", "beyond_prefix",
        "Riporta la lettura e il lotto del campione consumato LX-506. "
        "Il campione è esaurito e la lettura non è ripetibile.",
        "LeggiCampione", {"campione": "LX-506"},
        "campione=LX-506; lotto=PK-506; controllo=0.6821",
        ("lotto=PK-506", "controllo=0.6821"), "keep", tail=True,
        rationale="L'esito e il lotto stanno oltre il prefisso conservato e non sono recuperabili; "
                  "solo l'output completo li conserva.")

    add("T05", "en", "protected_newer",
        "Report the free slot count from the latest inventory S24 only; the earlier S23 inventory is "
        "obsolete and no further read is possible.",
        "ReadSnapshot", {"capture": "inventory-S23"},
        "inventory=S23; free_slots=4",
        ("free_slots=19",), "drop_call", tail=False,
        recent=("ReadSnapshot", {"capture": "inventory-S24"}, "inventory=S24; free_slots=19"),
        rationale="The pinned newer read carries the current fact with its own correct input; the older "
                  "candidate is obsolete, so the whole pair can be removed.")

    add("T06", "it", "protected_identical",
        "Riporta workers dall'istantanea immutabile D13. Le due letture registrate contengono gli stessi "
        "byte e non è possibile leggere oltre.",
        "Leggi", {"file_path": "snapshot/D13/worker.ini"},
        "workers=11; snapshot=D13",
        ("workers=11",), "drop_call", tail=False,
        recent=("Leggi", {"file_path": "snapshot/D13/worker.ini"}, "workers=11; snapshot=D13"),
        rationale="La lettura fissata è identica byte per byte al candidato; la coppia non aggiunge nulla "
                  "di unico e può essere rimossa per intero.")

    add("T07", "en", "recovery_available",
        "Report connect_timeout from immutable snapshot R41. The exact snapshot remains readable by path "
        "and hash; one additional read is permitted.",
        "Read", {"file_path": "snapshot/R41/client.ini"},
        "connect_timeout=29; snapshot=R41",
        ("connect_timeout=29",), "drop_call", tail=True,
        recovery_path="snapshot/R41/client.ini",
        rationale="The fact lies beyond the prefix, but the pinned immutable source restores the exact "
                  "output by path and hash; the smallest sufficient retention removes the pair.")

    add("T08", "it", "recovery_available",
        "Riporta limite_righe dall'istantanea immutabile R43. Il file esatto è recuperabile tramite "
        "percorso e hash; è consentita una lettura aggiuntiva.",
        "Leggi", {"file_path": "snapshot/R43/limiti.ini"},
        "limite_righe=275; snapshot=R43",
        ("limite_righe=275",), "drop_call", tail=True,
        recovery_path="snapshot/R43/limiti.ini",
        rationale="Il fatto sta oltre il prefisso, ma la sorgente immutabile lo ripristina esattamente; "
                  "la ritenzione minima sufficiente elimina la coppia.")

    return rows


def _outside_candidate(messages):
    parts = []
    for message in messages:
        parts.append(message["text"])
        for result in message.get("toolResults", []):
            if result["tool_use_id"] != "candidate":
                parts.append(result["text"])
    return "\n".join(parts)


def validate_specs(specs):
    if len(specs) != 8 or len({spec["id"] for spec in specs}) != 8:
        raise ValueError("Expected eight distinct cases")
    if Counter(spec["language"] for spec in specs) != {"en": 4, "it": 4}:
        raise ValueError("Language balance broken")
    if Counter(spec["oracle"]["expected_action"] for spec in specs) != {"drop_call": 4, "drop_result": 2, "keep": 2}:
        raise ValueError("Action balance broken")
    for spec in specs:
        output = spec["candidate"]["output"]
        if len(output) <= 420:
            raise ValueError(f"{spec['id']}: candidate output must exceed the fast-jev truncation floor")
        required = spec["oracle"]["required_facts"]
        if not required:
            raise ValueError(f"{spec['id']}: no required facts declared")
        if spec["family"] != "protected_newer":
            for token in required:
                if token not in output:
                    raise ValueError(f"{spec['id']}: required fact missing from the candidate output: {token}")
        results = [result for message in spec["messages"] for result in message.get("toolResults", [])
                   if result["tool_use_id"] == "candidate"]
        if len(results) != 1 or results[0]["text"] != output:
            raise ValueError(f"{spec['id']}: candidate result is malformed")
        recent = spec["recent"]
        if recent is not None:
            calls = [call for message in spec["messages"] for call in message["toolUses"]
                     if call["tool_use_id"] == "recent-copy"]
            recent_results = [result for message in spec["messages"] for result in message.get("toolResults", [])
                              if result["tool_use_id"] == "recent-copy"]
            if len(calls) != 1 or len(recent_results) != 1:
                raise ValueError(f"{spec['id']}: recent pair malformed")
            if calls[0]["input"] != recent["inputs"] or recent_results[0]["text"] != recent["output"]:
                raise ValueError(f"{spec['id']}: recent copy does not carry its own input and output")

        family = spec["family"]
        outside = _outside_candidate(spec["messages"])
        if family in {"prefix_only", "beyond_prefix", "recovery_available"}:
            for token in required:
                if token in outside:
                    raise ValueError(f"{spec['id']}: fact leaks outside the candidate result: {token}")
        if family == "prefix_only":
            if not all(token in output[:300] for token in required):
                raise ValueError(f"{spec['id']}: prefix_only fact outside the retained prefix")
        elif family == "beyond_prefix":
            if any(token in output[:300] for token in required):
                raise ValueError(f"{spec['id']}: beyond_prefix fact inside the retained prefix")
        elif family == "protected_newer":
            if recent is None or not all(token in recent["output"] for token in required):
                raise ValueError(f"{spec['id']}: newer protected read lacks the required fact")
            for token in required:
                if token in output:
                    raise ValueError(f"{spec['id']}: obsolete candidate must not carry the current fact")
            if recent["inputs"] == spec["candidate"]["input"]:
                raise ValueError(f"{spec['id']}: superseded read reuses the old input")
        elif family == "protected_identical":
            if recent is None or recent["output"] != output or recent["inputs"] != spec["candidate"]["input"]:
                raise ValueError(f"{spec['id']}: duplicate read must be byte-identical")
        elif family == "recovery_available":
            recovery = spec["recovery"]
            if recovery is None or recovery["content"] != output:
                raise ValueError(f"{spec['id']}: recovery content must be the full candidate output")
            if hashlib.sha256(recovery["content"].encode("utf-8")).hexdigest() != recovery["sha256"]:
                raise ValueError(f"{spec['id']}: recovery hash mismatch")
            if not all(token in recovery["content"] for token in required):
                raise ValueError(f"{spec['id']}: recovery source cannot restore a required fact")
            if not any(message["text"] == recovery["note"] for message in spec["messages"]):
                raise ValueError(f"{spec['id']}: recovery note missing from the transcript")
        else:
            raise ValueError(f"{spec['id']}: unknown family {family}")
    return specs
