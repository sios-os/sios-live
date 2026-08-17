"""Autonomous funding execution — connects approved prospects to
document generation, email submission, and governed application.

This module bridges the gap between "approved prospect" and "submitted
application." When the Creator approves a prospect, ANUBIS can:

1. Generate a full application document (grant proposal, project bid,
   bounty submission) using the cloud teacher or local model.
2. Save it as a file on disk for Creator review.
3. Draft an email with the application attached (or body included).
4. Submit the email via the email system — but ONLY with explicit
   Creator approval (approval_token).

Safety:
- ANUBIS never submits without Creator approval.
- ANUBIS never signs contracts or represents itself as a legal entity.
- All generated documents are saved for review before submission.
- All actions are logged to the evidence ledger.
- The Creator can review, edit, approve, or reject at each stage.
- Financial details (bank accounts, tax IDs) are never auto-filled.
"""
from __future__ import annotations

import hashlib
import json
import time
from dataclasses import dataclass, field, asdict
from pathlib import Path
from typing import Any


# Application stages
STAGE_DRAFTING = "drafting"        # ANUBIS is generating the document
STAGE_REVIEW = "review"            # Document generated, awaiting Creator review
STAGE_APPROVED = "approved"        # Creator approved the document
STAGE_SUBMITTING = "submitting"    # ANUBIS is submitting via email
STAGE_SUBMITTED = "submitted"      # Application submitted
STAGE_REJECTED = "rejected"        # Creator rejected the document
STAGE_FAILED = "failed"            # Submission failed


@dataclass
class FundingApplication:
    """A funding application generated from an approved prospect."""
    id: str
    prospect_id: str
    title: str = ""
    opportunity_type: str = ""  # grant, contract, bounty
    document_path: str = ""
    document_content: str = ""
    email_to: str = ""
    email_subject: str = ""
    email_body: str = ""
    stage: str = STAGE_DRAFTING
    created_at: float = 0.0
    updated_at: float = 0.0
    submitted_at: float = 0.0
    error: str = ""
    notes: str = ""

    def to_dict(self) -> dict[str, Any]:
        d = asdict(self)
        # Don't expose full document content in status dumps
        d["document_content_length"] = len(self.document_content)
        del d["document_content"]
        return d

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "FundingApplication":
        return cls(**{k: v for k, v in data.items() if k in cls.__dataclass_fields__})


class FundingExecutor:
    """Executes funding applications from approved prospects.

    Pipeline:
    1. prospect approved → generate application document
    2. document saved → Creator reviews
    3. Creator approves → draft email
    4. Creator approves email → submit via email system
    5. submission logged → prospect marked as submitted

    All steps require Creator approval except step 1 (drafting).
    """

    ACTOR = "anubis.funding_executor"

    def __init__(
        self,
        root: str | Path,
        *,
        prospects: Any | None = None,
        email_system: Any | None = None,
        computer_control: Any | None = None,
        cloud_model: Any | None = None,
        ledger: Any | None = None,
        on_speak: Any | None = None,
    ) -> None:
        self.root = Path(root)
        self.prospects = prospects
        self.email_system = email_system
        self.computer_control = computer_control
        self.cloud_model = cloud_model
        self.ledger = ledger
        self.on_speak = on_speak

        self._state_dir = self.root / "memory" / "funding"
        self._state_dir.mkdir(parents=True, exist_ok=True)
        self._apps_file = self._state_dir / "applications.json"
        self._docs_dir = self._state_dir / "documents"
        self._docs_dir.mkdir(parents=True, exist_ok=True)

        self._applications: dict[str, FundingApplication] = {}
        self._load()

    def _load(self) -> None:
        if not self._apps_file.exists():
            return
        try:
            data = json.loads(self._apps_file.read_text(encoding="utf-8"))
            for item in data.get("applications", []):
                app = FundingApplication.from_dict(item)
                self._applications[app.id] = app
        except (json.JSONDecodeError, OSError):
            pass

    def _save(self) -> None:
        data = {
            "applications": [a.to_dict() for a in self._applications.values()],
            "count": len(self._applications),
            "updated_at": time.time(),
        }
        self._apps_file.write_text(
            json.dumps(data, indent=2, ensure_ascii=False) + "\n",
            encoding="utf-8",
        )

    def _log(self, action: str, data: dict[str, Any] | None = None) -> None:
        if self.ledger:
            try:
                self.ledger.append(self.ACTOR, action, data or {})
            except Exception:
                pass

    def _speak(self, text: str) -> None:
        if self.on_speak:
            try:
                self.on_speak(text)
            except Exception:
                pass

    def _generate_id(self, prospect_id: str) -> str:
        raw = f"app:{prospect_id}:{time.time()}"
        return "funding_" + hashlib.sha256(raw.encode()).hexdigest()[:12]

    # ===========================================================
    # STAGE 1: Generate application document
    # ===========================================================

    def generate_application(
        self,
        prospect_id: str,
        *,
        extra_instructions: str = "",
    ) -> dict[str, Any]:
        """Generate a funding application document from an approved prospect.

        This uses the cloud model (or local model) to draft the application
        based on the prospect details. The document is saved to disk for
        Creator review.

        Args:
            prospect_id: The approved prospect ID
            extra_instructions: Additional instructions for the draft

        Returns:
            Dict with application ID and document path
        """
        if not self.prospects:
            return {"ok": False, "error": "prospects system not connected"}

        prospect = self.prospects.store.get(prospect_id)
        if not prospect:
            return {"ok": False, "error": "prospect not found"}

        if prospect.status != "approved":
            return {"ok": False, "error": f"prospect status is '{prospect.status}', must be 'approved'"}

        # Create application record
        app_id = self._generate_id(prospect_id)
        app = FundingApplication(
            id=app_id,
            prospect_id=prospect_id,
            title=prospect.title,
            opportunity_type=prospect.opportunity_type,
            stage=STAGE_DRAFTING,
            created_at=time.time(),
            updated_at=time.time(),
        )
        self._applications[app_id] = app
        self._save()

        self._log("application.generation_started", {
            "application_id": app_id,
            "prospect_id": prospect_id,
            "title": prospect.title,
        })
        self._speak(f"Generating funding application for {prospect.title}")

        # Build the prompt for the model
        prompt = self._build_application_prompt(prospect, extra_instructions)

        # Generate the document content
        document_content = self._generate_document_content(prompt, prospect)

        if not document_content:
            app.stage = STAGE_FAILED
            app.error = "Failed to generate document content"
            app.updated_at = time.time()
            self._save()
            self._log("application.generation_failed", {
                "application_id": app_id,
                "error": app.error,
            })
            return {"ok": False, "error": app.error, "application_id": app_id}

        # Save document to disk
        safe_title = "".join(c for c in prospect.title if c.isalnum() or c in " -_")[:60]
        doc_filename = f"{safe_title}_{app_id[:8]}.txt"
        doc_path = self._docs_dir / doc_filename
        doc_path.write_text(document_content, encoding="utf-8")

        app.document_path = str(doc_path)
        app.document_content = document_content
        app.stage = STAGE_REVIEW
        app.updated_at = time.time()
        self._save()

        self._log("application.document_generated", {
            "application_id": app_id,
            "document_path": str(doc_path),
            "content_length": len(document_content),
        })
        self._speak(f"Application document generated and saved for review")

        return {
            "ok": True,
            "application_id": app_id,
            "document_path": str(doc_path),
            "stage": STAGE_REVIEW,
            "message": "Document generated. Creator must review and approve before submission.",
        }

    def _build_application_prompt(self, prospect: Any, extra: str) -> str:
        """Build a prompt for the model to generate the application."""
        prompt_parts = [
            f"You are ANUBIS, an AI assistant helping to draft a funding application.",
            f"",
            f"OPPORTUNITY DETAILS:",
            f"Title: {prospect.title}",
            f"Source: {prospect.source}",
            f"Type: {prospect.opportunity_type}",
            f"Description: {prospect.description}",
            f"Eligibility: {prospect.eligibility}",
            f"Deadline: {prospect.deadline}",
            f"",
            f"ESTIMATES:",
            f"Effort: {prospect.estimated_effort_hours} hours",
            f"Cost: {prospect.estimated_cost} {prospect.currency}",
            f"Expected return: {prospect.estimated_return} {prospect.currency}",
            f"",
            f"RISKS: {', '.join(prospect.risks) if prospect.risks else 'None identified'}",
            f"EVIDENCE: {', '.join(prospect.evidence) if prospect.evidence else 'None'}",
            f"",
            f"INSTRUCTIONS:",
            f"1. Write a professional, complete application document.",
            f"2. Include: executive summary, objectives, methodology, timeline, budget, qualifications.",
            f"3. Do NOT include bank account numbers, tax IDs, or personal financial details.",
            f"4. Do NOT sign anything — leave signature blocks for the Creator.",
            f"5. Use formal business English.",
            f"6. Be honest about capabilities — do not overstate.",
            f"7. Leave placeholders like [CREATOR_NAME] for personal details.",
        ]
        if extra:
            prompt_parts.append(f"")
            prompt_parts.append(f"ADDITIONAL INSTRUCTIONS: {extra}")

        return "\n".join(prompt_parts)

    def _generate_document_content(self, prompt: str, prospect: Any) -> str:
        """Generate document content using cloud model or local model."""
        # Try cloud model first
        if self.cloud_model:
            try:
                resp = self.cloud_model.chat(prompt, creator_approved=True)
                if resp and hasattr(resp, "text") and resp.text:
                    return resp.text
                if isinstance(resp, dict) and resp.get("text"):
                    return resp["text"]
                if isinstance(resp, str):
                    return resp
            except Exception:
                pass

        # Fallback: generate a structured template
        return self._generate_template(prospect)

    def _generate_template(self, prospect: Any) -> str:
        """Generate a structured application template as fallback."""
        return f"""FUNDING APPLICATION

To: {prospect.source}
Re: {prospect.title}
Date: {time.strftime('%Y-%m-%d')}
Deadline: {prospect.deadline}

=========================================================

EXECUTIVE SUMMARY

[Provide a brief summary of the proposed project and funding request.]

PROJECT TITLE: {prospect.title}

FUNDING REQUESTED: {prospect.estimated_return} {prospect.currency}

=========================================================

1. OBJECTIVES

[Describe the specific objectives of this project.]

- Objective 1: [To be filled]
- Objective 2: [To be filled]
- Objective 3: [To be filled]

=========================================================

2. BACKGROUND AND RATIONALE

[Explain why this project is needed and what problem it solves.]

Opportunity Source: {prospect.source}
Opportunity Type: {prospect.opportunity_type}

=========================================================

3. METHODOLOGY

[Describe the approach and methods that will be used.]

Phase 1: [Description]
Phase 2: [Description]
Phase 3: [Description]

=========================================================

4. TIMELINE

[Provide a project timeline with milestones.]

- Month 1: [Milestone]
- Month 2: [Milestone]
- Month 3: [Milestone]

=========================================================

5. BUDGET

Estimated Effort: {prospect.estimated_effort_hours} hours
Estimated Cost: {prospect.estimated_cost} {prospect.currency}
Funding Requested: {prospect.estimated_return} {prospect.currency}

[Itemized budget to be completed by Creator]

=========================================================

6. QUALIFICATIONS

[Describe relevant qualifications and experience.]

Entity: Anpucrown Technologies
Contact: [CREATOR_NAME]
Email: [CREATOR_EMAIL]

=========================================================

7. RISKS AND MITIGATION

Identified Risks:
{chr(10).join(f'- {r}' for r in prospect.risks) if prospect.risks else '- None identified'}

[Mitigation strategies to be completed]

=========================================================

8. EVIDENCE AND CITATIONS

{chr(10).join(f'- {e}' for e in prospect.evidence) if prospect.evidence else '[To be provided]'}

{chr(10).join(f'- {c}' for c in prospect.citations) if prospect.citations else ''}

=========================================================

SIGNATURE

[CREATOR_NAME]
Anpucrown Technologies
Date: _______________

=========================================================

NOTE: This document was generated by ANUBIS as a draft template.
The Creator must review, complete, and approve before submission.
Personal and financial details must be filled in by the Creator only.
"""

    # ===========================================================
    # STAGE 2: Review document
    # ===========================================================

    def get_application(self, app_id: str) -> dict[str, Any]:
        """Get application details for review."""
        app = self._applications.get(app_id)
        if not app:
            return {"ok": False, "error": "application not found"}
        return {"ok": True, "application": app.to_dict()}

    def get_document(self, app_id: str) -> dict[str, Any]:
        """Get the full document content for review."""
        app = self._applications.get(app_id)
        if not app:
            return {"ok": False, "error": "application not found"}
        return {
            "ok": True,
            "application_id": app_id,
            "document_path": app.document_path,
            "content": app.document_content,
            "stage": app.stage,
        }

    def list_applications(self, stage: str = "") -> dict[str, Any]:
        """List applications, optionally filtered by stage."""
        apps = list(self._applications.values())
        if stage:
            apps = [a for a in apps if a.stage == stage]
        return {
            "applications": [a.to_dict() for a in apps],
            "count": len(apps),
        }

    # ===========================================================
    # STAGE 3: Approve document for submission
    # ===========================================================

    def approve_document(self, app_id: str, *, email_to: str = "", email_subject: str = "") -> dict[str, Any]:
        """Creator approves the document for email submission.

        Args:
            app_id: Application ID
            email_to: Recipient email (if different from prospect source)
            email_subject: Email subject line
        """
        app = self._applications.get(app_id)
        if not app:
            return {"ok": False, "error": "application not found"}

        if app.stage != STAGE_REVIEW:
            return {"ok": False, "error": f"application stage is '{app.stage}', must be 'review'"}

        app.stage = STAGE_APPROVED
        app.updated_at = time.time()

        # Set email details
        if email_to:
            app.email_to = email_to
        if email_subject:
            app.email_subject = email_subject

        # Auto-generate email body if not set
        if not app.email_body:
            app.email_body = self._generate_email_body(app)

        # Auto-generate subject if not set
        if not app.email_subject:
            app.email_subject = f"Funding Application: {app.title}"

        self._save()
        self._log("application.document_approved", {
            "application_id": app_id,
            "email_to": app.email_to,
        })
        self._speak(f"Application approved for submission")

        return {
            "ok": True,
            "application_id": app_id,
            "stage": STAGE_APPROVED,
            "email_to": app.email_to,
            "email_subject": app.email_subject,
            "email_body_preview": app.email_body[:200],
            "message": "Document approved. Use submit_application to send via email.",
        }

    def reject_document(self, app_id: str, *, reason: str = "") -> dict[str, Any]:
        """Creator rejects the document."""
        app = self._applications.get(app_id)
        if not app:
            return {"ok": False, "error": "application not found"}

        app.stage = STAGE_REJECTED
        app.notes = reason
        app.updated_at = time.time()
        self._save()
        self._log("application.document_rejected", {
            "application_id": app_id,
            "reason": reason,
        })
        return {"ok": True, "application_id": app_id, "stage": STAGE_REJECTED}

    def update_email(self, app_id: str, *, email_to: str = "", email_subject: str = "", email_body: str = "") -> dict[str, Any]:
        """Update email details before submission."""
        app = self._applications.get(app_id)
        if not app:
            return {"ok": False, "error": "application not found"}

        if email_to:
            app.email_to = email_to
        if email_subject:
            app.email_subject = email_subject
        if email_body:
            app.email_body = email_body
        app.updated_at = time.time()
        self._save()

        return {"ok": True, "application_id": app_id, "message": "Email details updated"}

    def _generate_email_body(self, app: FundingApplication) -> str:
        """Generate a cover email body for the application."""
        return f"""Dear Review Committee,

Please find below our application for the following opportunity:

Title: {app.title}
Application ID: {app.id}

The full application document is included below for your review. We
believe this project aligns well with the opportunity requirements and
we are confident in our ability to deliver the proposed outcomes.

We are available to answer any questions or provide additional
information as needed.

Thank you for your consideration.

Sincerely,

[CREATOR_NAME]
Anpucrown Technologies
anubis@anpucrowntechnologies.com

---

{app.document_content}
"""

    # ===========================================================
    # STAGE 4: Submit application via email
    # ===========================================================

    def submit_application(self, app_id: str, *, approval_token: str = "") -> dict[str, Any]:
        """Submit the application via email.

        Requires Creator approval token.
        """
        if approval_token != "creator-approved":
            return {"ok": False, "error": "Creator approval required for submission"}

        app = self._applications.get(app_id)
        if not app:
            return {"ok": False, "error": "application not found"}

        if app.stage != STAGE_APPROVED:
            return {"ok": False, "error": f"application stage is '{app.stage}', must be 'approved'"}

        if not self.email_system:
            return {"ok": False, "error": "email system not connected"}

        if not app.email_to:
            return {"ok": False, "error": "no recipient email address set"}

        app.stage = STAGE_SUBMITTING
        app.updated_at = time.time()
        self._save()

        self._log("application.submitting", {
            "application_id": app_id,
            "email_to": app.email_to,
        })
        self._speak(f"Submitting application for {app.title}")

        # Send the email
        try:
            result = self.email_system.send_email(
                app.email_to,
                app.email_subject,
                app.email_body,
            )
        except Exception as e:
            app.stage = STAGE_FAILED
            app.error = str(e)
            app.updated_at = time.time()
            self._save()
            self._log("application.submission_failed", {
                "application_id": app_id,
                "error": str(e),
            })
            return {"ok": False, "error": str(e), "application_id": app_id}

        if isinstance(result, dict) and result.get("success"):
            app.stage = STAGE_SUBMITTED
            app.submitted_at = time.time()
            app.updated_at = time.time()
            self._save()

            # Update prospect status
            if self.prospects:
                try:
                    self.prospects.store.update(app.prospect_id, {"status": "submitted"})
                except Exception:
                    pass

            self._log("application.submitted", {
                "application_id": app_id,
                "prospect_id": app.prospect_id,
                "email_to": app.email_to,
                "submitted_at": app.submitted_at,
            })
            self._speak(f"Application submitted successfully")

            return {
                "ok": True,
                "application_id": app_id,
                "stage": STAGE_SUBMITTED,
                "submitted_at": app.submitted_at,
                "message": "Application submitted via email.",
            }
        else:
            error = result.get("error", "unknown") if isinstance(result, dict) else str(result)
            app.stage = STAGE_FAILED
            app.error = error
            app.updated_at = time.time()
            self._save()
            self._log("application.submission_failed", {
                "application_id": app_id,
                "error": error,
            })
            return {"ok": False, "error": error, "application_id": app_id}

    # ===========================================================
    # STATUS
    # ===========================================================

    def get_status(self) -> dict[str, Any]:
        """Get funding executor status."""
        apps = list(self._applications.values())
        return {
            "prospects_connected": self.prospects is not None,
            "email_connected": self.email_system is not None,
            "computer_control_connected": self.computer_control is not None,
            "cloud_model_connected": self.cloud_model is not None,
            "total_applications": len(apps),
            "drafting": sum(1 for a in apps if a.stage == STAGE_DRAFTING),
            "review": sum(1 for a in apps if a.stage == STAGE_REVIEW),
            "approved": sum(1 for a in apps if a.stage == STAGE_APPROVED),
            "submitted": sum(1 for a in apps if a.stage == STAGE_SUBMITTED),
            "rejected": sum(1 for a in apps if a.stage == STAGE_REJECTED),
            "failed": sum(1 for a in apps if a.stage == STAGE_FAILED),
            "documents_dir": str(self._docs_dir),
        }

    def list_pending_reviews(self) -> dict[str, Any]:
        """List applications awaiting Creator review."""
        apps = [a for a in self._applications.values() if a.stage == STAGE_REVIEW]
        return {
            "applications": [a.to_dict() for a in apps],
            "count": len(apps),
        }

    def list_pending_submission(self) -> dict[str, Any]:
        """List applications approved but not yet submitted."""
        apps = [a for a in self._applications.values() if a.stage == STAGE_APPROVED]
        return {
            "applications": [a.to_dict() for a in apps],
            "count": len(apps),
        }
