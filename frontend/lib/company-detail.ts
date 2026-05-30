import type { AlertRecord, Company, EventRecord, RawDocument, ThesisNote } from "./api";

export type CompanyDetail = {
  company: Company;
  documents: RawDocument[];
  events: EventRecord[];
  alerts: AlertRecord[];
  thesisNotes: ThesisNote[];
  counts: {
    documents: number;
    events: number;
    alerts: number;
    thesisNotes: number;
  };
};

export function buildCompanyDetail(
  company: Company,
  documents: RawDocument[],
  events: EventRecord[],
  alerts: AlertRecord[],
  thesisNotes: ThesisNote[]
): CompanyDetail {
  const companyId = company.id;
  const linkedDocuments = documents.filter((document) => document.company_id === companyId);
  const linkedEvents = events.filter((event) => event.company_id === companyId);
  const linkedAlerts = alerts.filter((alert) => alert.company_id === companyId);
  const linkedThesisNotes = thesisNotes.filter((note) => note.company_id === companyId);

  return {
    company,
    documents: linkedDocuments,
    events: linkedEvents,
    alerts: linkedAlerts,
    thesisNotes: linkedThesisNotes,
    counts: {
      documents: linkedDocuments.length,
      events: linkedEvents.length,
      alerts: linkedAlerts.length,
      thesisNotes: linkedThesisNotes.length
    }
  };
}
