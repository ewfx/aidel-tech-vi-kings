export type TaskStatusState = 'pending' | 'processing' | 'complete' | 'failed';

export interface TaskStatus {
  entityExtraction: TaskStatusState;
  organizationEnrichment: TaskStatusState;
  peopleEnrichment: TaskStatusState;
  riskAssessment: TaskStatusState;
}

export interface Organization {
  name: string;
  role: 'sender' | 'recipient' | 'intermediary';
  jurisdiction?: string;
  entity_type?: string;
}

export interface Person {
  name: string;
  role: string;
  country?: string;
}

export interface TransactionDetails {
  amount: string;
  currency: string;
  purpose?: string;
  date: string;
}

export interface EntitiesExtracted {
  transaction_id: string;
  organizations: Organization[];
  people: Person[];
  transaction: TransactionDetails;
  jurisdictions: string[];
}

export interface OrganizationResult {
  opencorporates: {
    status: string;
    data?: any;
  };
  sanctions: {
    status: string;
    data?: any[];
  };
  wikidata: {
    status: string;
    data?: any;
    associated_people?: Person[];
  };
  news: {
    status: string;
    data?: any[];
  };
}

export interface PersonResult {
  pep: {
    status: string;
    data?: any[];
  };
  sanctions: {
    status: string;
    data?: any[];
  };
  news: {
    status: string;
    data?: any[];
  };
}

export interface TaskResult {
  [key: string]: any;
}

export interface RiskAssessment {
  transaction_id: string;
  extracted_entities: string[];
  entity_types: string[];
  risk_score: number;
  supporting_evidence: string[];
  confidence_score: number;
  reason: string;
  raw_data?: {
    transaction_text: string;
    extracted_entities: EntitiesExtracted;
    organizations: Record<string, OrganizationResult>;
    people: Record<string, PersonResult>;
    wikidata_people?: Record<string, PersonResult>;
  };
}

export interface Transaction {
  sender: {
    name: string;
    account: string;
    address: string;
    notes?: string;
  };
  receiver: {
    name: string;
    account: string;
    address: string;
    tax_id?: string;
  };
  amount: string;
  currency: string;
  transaction_type: string;
  reference?: string;
  additional_notes?: string[];
}

export interface AirflowStatus {
  dag_id: string;
  run_id: string;
  status: string;
}

export type ApiResponse = AirflowStatus | RiskAssessment;