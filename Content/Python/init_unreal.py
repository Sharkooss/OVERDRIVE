"""OVERDRIVE - passerelle Python temporaire pour l'editeur.

POURQUOI : aucun des 52 toolsets du serveur unreal-mcp ne sait creer ni editer un
UserDefinedEnum / UserDefinedStruct (Docs/08_DATA_SCHEMAS.md §1-2). UE execute
automatiquement Content/Python/init_unreal.py au demarrage de l'editeur : on s'en
sert pour ouvrir un canal d'execution sans avoir a redemarrer a chaque essai.

FONCTIONNEMENT : un callback post-tick surveille Saved/py_inbox/. Tout .py depose
la est execute une fois, sa sortie part dans Saved/py_outbox/<nom>.txt, puis le
fichier source est supprime.

TEMPORAIRE - a supprimer en fin de J1. Outillage editeur uniquement : aucune
logique de jeu, jamais cook, jamais reference par du contenu.
"""
import io
import os
import traceback
import contextlib

import unreal

SAVED = unreal.Paths.project_saved_dir()
INBOX = os.path.join(SAVED, "py_inbox")
OUTBOX = os.path.join(SAVED, "py_outbox")

for folder in (INBOX, OUTBOX):
    if not os.path.isdir(folder):
        os.makedirs(folder)


def _run_one(path):
    name = os.path.basename(path)
    buffer = io.StringIO()
    # Le fichier est lu PUIS supprime AVANT l'execution : delete_asset/create_asset
    # font tourner la boucle Slate, donc _tick se redeclenche pendant l'exec. Si le
    # fichier est encore la, il est reexecute -> recursion infinie qui gele l'editeur.
    try:
        with open(path, "r", encoding="utf-8") as handle:
            code = handle.read()
    except OSError:
        return
    try:
        os.remove(path)
    except OSError:
        pass
    try:
        with contextlib.redirect_stdout(buffer), contextlib.redirect_stderr(buffer):
            exec(compile(code, name, "exec"), {"__name__": "__od_inbox__"})
    except Exception:
        buffer.write("\n%s" % traceback.format_exc())
    out = os.path.join(OUTBOX, name.replace(".py", "") + ".txt")
    with open(out, "w", encoding="utf-8") as handle:
        handle.write(buffer.getvalue() or "(aucune sortie)")


# Deuxieme filet : garde de reentrance, au cas ou un script pompe la boucle Slate.
_BUSY = {"on": False}


def _tick(_delta):
    if _BUSY["on"]:
        return
    try:
        pending = sorted(f for f in os.listdir(INBOX) if f.endswith(".py"))
    except OSError:
        return
    if not pending:
        return
    _BUSY["on"] = True
    try:
        for name in pending:
            _run_one(os.path.join(INBOX, name))
    finally:
        _BUSY["on"] = False


_HANDLE = unreal.register_slate_post_tick_callback(_tick)
unreal.log("OVERDRIVE: passerelle Python active, depose tes scripts dans Saved/py_inbox/")
