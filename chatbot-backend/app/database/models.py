"""Data models representing database tables."""

from dataclasses import dataclass
from datetime import datetime
from datetime import datetime, timedelta
from typing import Optional, List, Dict, Any

@dataclass
class Project:
    """Represents a construction project."""
    
    id: int
    name: str
    description: Optional[str] = None
    status: str = "New"
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None
    completion_percentage: float = 0.0
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Project':
        """Create a Project instance from a dictionary."""
        return cls(
            id=data.get('id'),
            name=data.get('name'),
            description=data.get('description'),
            status=data.get('status', 'New'),
            start_date=data.get('start_date'),
            end_date=data.get('end_date'),
            completion_percentage=data.get('completion_percentage', 0.0),
            created_at=data.get('created_at'),
            updated_at=data.get('updated_at')
        )

@dataclass
class Budget:
    """Represents a project budget."""
    
    id: int
    project_id: int
    total_budget: float
    spent: float = 0.0
    remaining: Optional[float] = None
    currency: str = "USD"
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    
    def __post_init__(self):
        """Calculate remaining budget if not provided."""
        if self.remaining is None:
            self.remaining = self.total_budget - self.spent
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Budget':
        """Create a Budget instance from a dictionary."""
        return cls(
            id=data.get('id'),
            project_id=data.get('project_id'),
            total_budget=data.get('total_budget', 0.0),
            spent=data.get('spent', 0.0),
            remaining=data.get('remaining'),
            currency=data.get('currency', 'USD'),
            created_at=data.get('created_at'),
            updated_at=data.get('updated_at')
        )

@dataclass
class Task:
    """Represents a project task."""
    
    id: int
    project_id: int
    title: str
    description: Optional[str] = None
    status: str = "Not Started"
    due_date: Optional[datetime] = None
    assigned_to: Optional[int] = None
    priority: str = "Medium"
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Task':
        """Create a Task instance from a dictionary."""
        return cls(
            id=data.get('id'),
            project_id=data.get('project_id'),
            title=data.get('title'),
            description=data.get('description'),
            status=data.get('status', 'Not Started'),
            due_date=data.get('due_date'),
            assigned_to=data.get('assigned_to'),
            priority=data.get('priority', 'Medium'),
            created_at=data.get('created_at'),
            updated_at=data.get('updated_at')
        )

@dataclass
class Milestone:
    """Represents a project milestone."""
    
    id: int
    project_id: int
    title: str
    description: Optional[str] = None
    target_date: Optional[datetime] = None
    status: str = "Not Started"
    completion_date: Optional[datetime] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Milestone':
        """Create a Milestone instance from a dictionary."""
        return cls(
            id=data.get('id'),
            project_id=data.get('project_id'),
            title=data.get('title'),
            description=data.get('description'),
            target_date=data.get('target_date'),
            status=data.get('status', 'Not Started'),
            completion_date=data.get('completion_date'),
            created_at=data.get('created_at'),
            updated_at=data.get('updated_at')
        )

@dataclass
class User:
    """Represents a user in the system."""
    
    id: int
    name: str
    email: str
    role: str
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'User':
        """Create a User instance from a dictionary."""
        return cls(
            id=data.get('id'),
            name=data.get('name'),
            email=data.get('email'),
            role=data.get('role'),
            created_at=data.get('created_at'),
            updated_at=data.get('updated_at')
        )

@dataclass
class Issue:
    """Represents a project issue."""
    
    id: int
    project_id: int
    title: str
    description: Optional[str] = None
    status: str = "Open"
    priority: str = "Medium"
    reported_date: Optional[datetime] = None
    resolved_date: Optional[datetime] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Issue':
        """Create an Issue instance from a dictionary."""
        return cls(
            id=data.get('id'),
            project_id=data.get('project_id'),
            title=data.get('title'),
            description=data.get('description'),
            status=data.get('status', 'Open'),
            priority=data.get('priority', 'Medium'),
            reported_date=data.get('reported_date'),
            resolved_date=data.get('resolved_date'),
            created_at=data.get('created_at'),
            updated_at=data.get('updated_at')
        )

@dataclass
class Document:
    """Represents a project document."""
    
    id: int
    project_id: int
    name: str
    type: str
    url: str
    uploaded_at: Optional[datetime] = None
    uploaded_by: Optional[int] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Document':
        """Create a Document instance from a dictionary."""
        return cls(
            id=data.get('id'),
            project_id=data.get('project_id'),
            name=data.get('name'),
            type=data.get('type'),
            url=data.get('url'),
            uploaded_at=data.get('uploaded_at'),
            uploaded_by=data.get('uploaded_by'),
            created_at=data.get('created_at'),
            updated_at=data.get('updated_at')
        )

# 1. Selection Management Models

@dataclass
class SelectionCategory:
    """Represents a category for selection items."""
    
    id: int
    name: str
    description: Optional[str] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'SelectionCategory':
        """Create a SelectionCategory instance from a dictionary."""
        return cls(
            id=data.get('id'),
            name=data.get('name'),
            description=data.get('description'),
            created_at=data.get('created_at'),
            updated_at=data.get('updated_at')
        )

@dataclass
class SelectionItem:
    """Represents a selection item that needs to be chosen for a project."""
    
    id: int
    project_id: int
    category_id: int
    title: str
    description: Optional[str] = None
    required_date: Optional[datetime] = None
    decision_date: Optional[datetime] = None
    assigned_to: Optional[int] = None
    status: str = "Open"  # Open, In Progress, Completed, Delayed
    priority: str = "Medium"  # Low, Medium, High
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    
    @property
    def is_overdue(self) -> bool:
        """Check if selection is overdue."""
        if self.required_date and self.status != "Completed":
            return datetime.now() > self.required_date
        return False
    
    @property
    def days_overdue(self) -> Optional[int]:
        """Calculate days overdue if selection is overdue."""
        if self.is_overdue:
            delta = datetime.now() - self.required_date
            return delta.days
        return None
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'SelectionItem':
        """Create a SelectionItem instance from a dictionary."""
        return cls(
            id=data.get('id'),
            project_id=data.get('project_id'),
            category_id=data.get('category_id'),
            title=data.get('title'),
            description=data.get('description'),
            required_date=data.get('required_date'),
            decision_date=data.get('decision_date'),
            assigned_to=data.get('assigned_to'),
            status=data.get('status', 'Open'),
            priority=data.get('priority', 'Medium'),
            created_at=data.get('created_at'),
            updated_at=data.get('updated_at')
        )

# 2. Project Phase Tracking Models

@dataclass
class ProjectPhase:
    """Represents a high-level phase in a construction project."""
    
    id: int
    name: str
    description: Optional[str] = None
    sequence_number: int = 0
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'ProjectPhase':
        """Create a ProjectPhase instance from a dictionary."""
        return cls(
            id=data.get('id'),
            name=data.get('name'),
            description=data.get('description'),
            sequence_number=data.get('sequence_number', 0),
            created_at=data.get('created_at'),
            updated_at=data.get('updated_at')
        )

@dataclass
class ProjectStage:
    """Represents a stage within a project phase."""
    
    id: int
    phase_id: int
    name: str
    description: Optional[str] = None
    sequence_number: int = 0
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'ProjectStage':
        """Create a ProjectStage instance from a dictionary."""
        return cls(
            id=data.get('id'),
            phase_id=data.get('phase_id'),
            name=data.get('name'),
            description=data.get('description'),
            sequence_number=data.get('sequence_number', 0),
            created_at=data.get('created_at'),
            updated_at=data.get('updated_at')
        )

@dataclass
class PhaseTask:
    """Represents a required task within a project stage."""
    
    id: int
    stage_id: int
    title: str
    description: Optional[str] = None
    sequence_number: int = 0
    is_required: bool = True
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'PhaseTask':
        """Create a PhaseTask instance from a dictionary."""
        return cls(
            id=data.get('id'),
            stage_id=data.get('stage_id'),
            title=data.get('title'),
            description=data.get('description'),
            sequence_number=data.get('sequence_number', 0),
            is_required=data.get('is_required', True),
            created_at=data.get('created_at'),
            updated_at=data.get('updated_at')
        )

@dataclass
class ProjectPhaseAssignment:
    """Represents the assignment of a project to a specific phase and stage."""
    
    id: int
    project_id: int
    phase_id: int
    stage_id: int
    start_date: Optional[datetime] = None
    target_completion_date: Optional[datetime] = None
    actual_completion_date: Optional[datetime] = None
    completion_percentage: float = 0.0
    status: str = "Not Started"  # Not Started, In Progress, Completed
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'ProjectPhaseAssignment':
        """Create a ProjectPhaseAssignment instance from a dictionary."""
        return cls(
            id=data.get('id'),
            project_id=data.get('project_id'),
            phase_id=data.get('phase_id'),
            stage_id=data.get('stage_id'),
            start_date=data.get('start_date'),
            target_completion_date=data.get('target_completion_date'),
            actual_completion_date=data.get('actual_completion_date'),
            completion_percentage=data.get('completion_percentage', 0.0),
            status=data.get('status', 'Not Started'),
            created_at=data.get('created_at'),
            updated_at=data.get('updated_at')
        )

@dataclass
class PhaseTaskAssignment:
    """Represents the assignment of a phase task to a project."""
    
    id: int
    project_id: int
    phase_task_id: int
    assigned_to: Optional[int] = None
    start_date: Optional[datetime] = None
    due_date: Optional[datetime] = None
    completion_date: Optional[datetime] = None
    status: str = "Not Started"  # Not Started, In Progress, Completed
    notes: Optional[str] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'PhaseTaskAssignment':
        """Create a PhaseTaskAssignment instance from a dictionary."""
        return cls(
            id=data.get('id'),
            project_id=data.get('project_id'),
            phase_task_id=data.get('phase_task_id'),
            assigned_to=data.get('assigned_to'),
            start_date=data.get('start_date'),
            due_date=data.get('due_date'),
            completion_date=data.get('completion_date'),
            status=data.get('status', 'Not Started'),
            notes=data.get('notes'),
            created_at=data.get('created_at'),
            updated_at=data.get('updated_at')
        )

# 3. Walkthrough Management Models

@dataclass
class WalkthroughType:
    """Represents a type of walkthrough (PD, Client, etc.)."""
    
    id: int
    name: str
    description: Optional[str] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'WalkthroughType':
        """Create a WalkthroughType instance from a dictionary."""
        return cls(
            id=data.get('id'),
            name=data.get('name'),
            description=data.get('description'),
            created_at=data.get('created_at'),
            updated_at=data.get('updated_at')
        )

@dataclass
class Walkthrough:
    """Represents a walkthrough for a project."""
    
    id: int
    project_id: int
    walkthrough_type_id: int
    scheduled_date: Optional[datetime] = None
    actual_date: Optional[datetime] = None
    required_by_date: Optional[datetime] = None
    status: str = "Not Scheduled"  # Not Scheduled, Scheduled, Completed, Cancelled
    completed_by: Optional[int] = None
    notes: Optional[str] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    
    @property
    def needs_scheduling(self) -> bool:
        """Check if walkthrough needs scheduling."""
        return self.status == "Not Scheduled"
    
    @property
    def is_completed(self) -> bool:
        """Check if walkthrough is completed."""
        return self.status == "Completed" and self.actual_date is not None
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Walkthrough':
        """Create a Walkthrough instance from a dictionary."""
        return cls(
            id=data.get('id'),
            project_id=data.get('project_id'),
            walkthrough_type_id=data.get('walkthrough_type_id'),
            scheduled_date=data.get('scheduled_date'),
            actual_date=data.get('actual_date'),
            required_by_date=data.get('required_by_date'),
            status=data.get('status', 'Not Scheduled'),
            completed_by=data.get('completed_by'),
            notes=data.get('notes'),
            created_at=data.get('created_at'),
            updated_at=data.get('updated_at')
        )

@dataclass
class WalkthroughItem:
    """Represents an item to be checked during a walkthrough."""
    
    id: int
    walkthrough_id: int
    title: str
    description: Optional[str] = None
    status: str = "Not Checked"  # Not Checked, Checked, Issue Found
    issue_description: Optional[str] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'WalkthroughItem':
        """Create a WalkthroughItem instance from a dictionary."""
        return cls(
            id=data.get('id'),
            walkthrough_id=data.get('walkthrough_id'),
            title=data.get('title'),
            description=data.get('description'),
            status=data.get('status', 'Not Checked'),
            issue_description=data.get('issue_description'),
            created_at=data.get('created_at'),
            updated_at=data.get('updated_at')
        )

# 4. Procurement Tracking Models

@dataclass
class Trade:
    """Represents a trade category for procurement."""
    
    id: int
    name: str
    description: Optional[str] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Trade':
        """Create a Trade instance from a dictionary."""
        return cls(
            id=data.get('id'),
            name=data.get('name'),
            description=data.get('description'),
            created_at=data.get('created_at'),
            updated_at=data.get('updated_at')
        )

@dataclass
class Vendor:
    """Represents a vendor or contractor."""
    
    id: int
    name: str
    contact_name: Optional[str] = None
    contact_email: Optional[str] = None
    contact_phone: Optional[str] = None
    address: Optional[str] = None
    trade_id: Optional[int] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Vendor':
        """Create a Vendor instance from a dictionary."""
        return cls(
            id=data.get('id'),
            name=data.get('name'),
            contact_name=data.get('contact_name'),
            contact_email=data.get('contact_email'),
            contact_phone=data.get('contact_phone'),
            address=data.get('address'),
            trade_id=data.get('trade_id'),
            created_at=data.get('created_at'),
            updated_at=data.get('updated_at')
        )

@dataclass
class BidPackage:
    """Represents a bid package for procurement."""
    
    id: int
    project_id: int
    title: str
    description: Optional[str] = None
    trade_id: int
    estimated_value: Optional[float] = None
    issue_date: Optional[datetime] = None
    due_date: Optional[datetime] = None
    status: str = "Not Issued"  # Not Issued, Issued, Under Review, Awarded, Cancelled
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'BidPackage':
        """Create a BidPackage instance from a dictionary."""
        return cls(
            id=data.get('id'),
            project_id=data.get('project_id'),
            title=data.get('title'),
            description=data.get('description'),
            trade_id=data.get('trade_id'),
            estimated_value=data.get('estimated_value'),
            issue_date=data.get('issue_date'),
            due_date=data.get('due_date'),
            status=data.get('status', 'Not Issued'),
            created_at=data.get('created_at'),
            updated_at=data.get('updated_at')
        )

@dataclass
class PurchaseOrder:
    """Represents a purchase order for a vendor."""
    
    id: int
    project_id: int
    bid_package_id: Optional[int] = None
    vendor_id: int
    po_number: str
    amount: float
    description: Optional[str] = None
    issue_date: Optional[datetime] = None
    trade_id: Optional[int] = None
    status: str = "Draft"  # Draft, Issued, Fulfilled, Cancelled
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'PurchaseOrder':
        """Create a PurchaseOrder instance from a dictionary."""
        return cls(
            id=data.get('id'),
            project_id=data.get('project_id'),
            bid_package_id=data.get('bid_package_id'),
            vendor_id=data.get('vendor_id'),
            po_number=data.get('po_number'),
            amount=data.get('amount'),
            description=data.get('description'),
            issue_date=data.get('issue_date'),
            trade_id=data.get('trade_id'),
            status=data.get('status', 'Draft'),
            created_at=data.get('created_at'),
            updated_at=data.get('updated_at')
        )

# 5. Financial Milestone Tracking Models (Enhancing the existing Milestone class)

@dataclass
class PaymentMilestone:
    """Represents a payment milestone for a project."""
    
    id: int
    project_id: int
    title: str
    description: Optional[str] = None
    sequence_number: int
    amount: float
    percentage: float
    target_date: Optional[datetime] = None
    status: str = "Not Started"  # Not Started, In Progress, Ready for Billing, Invoiced, Paid
    invoice_number: Optional[str] = None
    invoice_date: Optional[datetime] = None
    payment_date: Optional[datetime] = None
    notes: Optional[str] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    
    @property
    def is_billable(self) -> bool:
        """Check if milestone is ready for billing."""
        return self.status == "Ready for Billing"
    
    @property
    def is_paid(self) -> bool:
        """Check if milestone has been paid."""
        return self.status == "Paid" and self.payment_date is not None
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'PaymentMilestone':
        """Create a PaymentMilestone instance from a dictionary."""
        return cls(
            id=data.get('id'),
            project_id=data.get('project_id'),
            title=data.get('title'),
            description=data.get('description'),
            sequence_number=data.get('sequence_number'),
            amount=data.get('amount'),
            percentage=data.get('percentage'),
            target_date=data.get('target_date'),
            status=data.get('status', 'Not Started'),
            invoice_number=data.get('invoice_number'),
            invoice_date=data.get('invoice_date'),
            payment_date=data.get('payment_date'),
            notes=data.get('notes'),
            created_at=data.get('created_at'),
            updated_at=data.get('updated_at')
        )

@dataclass
class Invoice:
    """Represents an invoice for a project."""
    
    id: int
    project_id: int
    invoice_number: str
    amount: float
    issue_date: datetime
    due_date: Optional[datetime] = None
    payment_date: Optional[datetime] = None
    status: str = "Issued"  # Draft, Issued, Paid, Cancelled
    notes: Optional[str] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Invoice':
        """Create an Invoice instance from a dictionary."""
        return cls(
            id=data.get('id'),
            project_id=data.get('project_id'),
            invoice_number=data.get('invoice_number'),
            amount=data.get('amount'),
            issue_date=data.get('issue_date'),
            due_date=data.get('due_date'),
            payment_date=data.get('payment_date'),
            status=data.get('status', 'Issued'),
            notes=data.get('notes'),
            created_at=data.get('created_at'),
            updated_at=data.get('updated_at')
        )