"""
backend/app/agents/translator.py
Deterministic translation of ClauseIR objects into First-Order Predicate Logic (FOPL) WFFs.
Contains zero LLM calls. Purely algorithmic mapping with strict provenance tagging.
"""

from __future__ import annotations
from typing import List, Optional, Tuple

from backend.app.models.clause_ir import (
    ClauseIR, ActionOntology, Modality, Party
)


class ClauseTranslator:
    """Deterministic converter from ClauseIR to First-Order Predicate Logic."""

    @classmethod
    def translate_to_fopl(cls, clause: ClauseIR) -> Optional[Tuple[str, str]]:
        """
        Translates a ClauseIR instance into a tuple of:
          (FOPL formula string, provenance explanation)
        Returns None if the action is not part of the formally reasoned ontology.
        """
        action = clause.action
        modality = clause.modality
        party = "tenant" if clause.party == Party.TENANT else ("landlord" if clause.party == Party.LANDLORD else "both")

        # 1. Termination Actions
        if action == ActionOntology.TERMINATE:
            notice_days = clause.params.notice_days or 30
            if modality == Modality.PERMISSION or modality == Modality.RIGHT:
                formula = f"Perm({party}, Terminate({notice_days}))"
                expl = f"Clause permits {party} to terminate with {notice_days} days notice."
                return formula, expl
            elif modality == Modality.PROHIBITION:
                formula = f"forall n: (LessThan(n, {notice_days}) -> Forb({party}, Terminate(n)))"
                expl = f"Clause prohibits {party} from terminating with less than {notice_days} days notice."
                return formula, expl

        # 2. Companion Pets Actions
        if action == ActionOntology.KEEP_PETS:
            if modality == Modality.PERMISSION or modality == Modality.RIGHT:
                formula = f"Perm({party}, KeepPets)"
                expl = f"Clause permits {party} to keep domestic pets."
                return formula, expl
            elif modality == Modality.PROHIBITION:
                formula = f"Forb({party}, KeepPets)"
                expl = f"Clause strictly forbids {party} from keeping pets."
                return formula, expl

        # 3. Entry and Inspection
        if action == ActionOntology.ENTER_PREMISES:
            is_unrestricted = clause.params.extra.get("unrestricted", False) or "without notice" in clause.text.lower()
            if is_unrestricted:
                formula = f"Perm({party}, EnterPremises(unrestricted))"
                expl = f"Clause permits {party} to enter premises at any time without notice."
                return formula, expl
            else:
                formula = f"Obl({party}, EnterPremises(notice_24h))"
                expl = f"Clause obligates {party} to serve prior notice before entry."
                return formula, expl

        # 4. Utilities Disconnection
        if action == ActionOntology.CUT_UTILITIES:
            formula = f"Perm({party}, CutUtilities)"
            expl = f"Clause purports to permit {party} to disconnect utilities as a remedy."
            return formula, expl

        # 5. Subletting
        if action == ActionOntology.SUBLET:
            if modality == Modality.PROHIBITION:
                formula = f"Forb({party}, Sublet)"
                expl = f"Clause forbids {party} from subletting the premises."
                return formula, expl
            elif modality == Modality.PERMISSION:
                formula = f"Perm({party}, Sublet)"
                expl = f"Clause permits {party} to sublet."
                return formula, expl

        # 6. Basic Rent and Deposit
        if action == ActionOntology.PAY_RENT:
            formula = "Obl(tenant, PayRent)"
            expl = "Tenant is obligated to pay monthly rent."
            return formula, expl

        if action == ActionOntology.PAY_DEPOSIT:
            formula = "Obl(tenant, PayDeposit)"
            expl = "Tenant is obligated to pay security deposit."
            return formula, expl

        return None

