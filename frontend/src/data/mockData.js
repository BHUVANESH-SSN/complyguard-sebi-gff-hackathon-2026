export const CIRCULAR = {
  name: "SEBI Master Circular for Stock Brokers (Demo Edition)",
  intermediary: "Stock Broker",
  pages: 2,
  issuedBy: "SEBI",
  file: "/sebi_demo_circular.pdf",
};

// Obligations pre-loaded to show a realistic post-extraction state.
// status: "met" | "pending" | "overdue"
export const INITIAL_OBLIGATIONS = [
  {
    id: 1,
    obligationText:
      "Maintain a segregated bank account for client funds, separate from the broker's own funds, and reconcile balances daily.",
    deadline: "2026-06-30",
    evidenceType: "Bank reconciliation statement",
    sourceChunk:
      "“...every stock broker shall keep the money of clients in a separate account distinct from its own account and shall not use such money for any purpose other than the purpose for which it has been provided by the client, and shall reconcile the client bank and securities balances on a daily basis...” — Ch. 4, §4.2",
    status: "met",
  },
  {
    id: 2,
    obligationText:
      "Report client margin obligations to the exchange on a T+1 basis using the prescribed margin trading system format.",
    deadline: "2026-06-20",
    evidenceType: "Exchange upload acknowledgement",
    sourceChunk:
      "“...stock brokers shall report the margins collected from clients to the Clearing Corporations on a T+1 basis, failing which a penalty shall be levied as per the framework specified in Annexure 3...” — Ch. 6, §6.5",
    status: "overdue",
  },
  {
    id: 3,
    obligationText:
      "Designate a Compliance Officer responsible for monitoring regulatory compliance and redressal of investor grievances.",
    deadline: null,
    evidenceType: "Board resolution / appointment letter",
    sourceChunk:
      "“...every stock broker shall appoint a Compliance Officer who shall be responsible for monitoring the compliance of the Act, rules, regulations, notifications, guidelines and circulars issued by the Board...” — Ch. 2, §2.1",
    status: "met",
  },
  {
    id: 4,
    obligationText:
      "Resolve investor grievances received through SCORES within 21 calendar days of receipt.",
    deadline: "2026-07-05",
    evidenceType: "SCORES resolution log",
    sourceChunk:
      "“...the stock broker shall resolve the grievance and submit an Action Taken Report on SCORES within 21 calendar days from the date of receipt of the grievance...” — Ch. 9, §9.3",
    status: "pending",
  },
  {
    id: 5,
    obligationText:
      "Conduct a cyber security and cyber resilience audit at least once a year and submit the report to the exchange.",
    deadline: "2026-09-30",
    evidenceType: "Audit report + exchange submission receipt",
    sourceChunk:
      "“...stock brokers shall conduct comprehensive cyber security and cyber resilience audit at least once in a financial year and submit the report to the stock exchange within one month of completion of the audit...” — Ch. 11, §11.4",
    status: "pending",
  },
  {
    id: 6,
    obligationText:
      "Disclose all algorithmic trading strategies deployed on behalf of clients and obtain exchange approval before deployment.",
    deadline: "2026-08-15",
    evidenceType: "Exchange approval certificate",
    sourceChunk:
      "“...no stock broker shall use or deploy any algorithmic trading strategy without prior approval from the stock exchange, and shall maintain a log of all such approved strategies...” — Ch. 7, §7.2",
    status: "pending",
  },
  {
    id: 7,
    obligationText:
      "Complete Know Your Client (KYC) re-verification for all active clients at least once every two years.",
    deadline: "2026-05-31",
    evidenceType: "KYC re-verification register",
    sourceChunk:
      "“...stock brokers shall undertake periodic review and updation of KYC records of clients at least once every two years for high risk clients and once every ten years for low risk clients...” — Ch. 3, §3.6",
    status: "overdue",
  },
];

export const INITIAL_EVIDENCE = [
  {
    id: 1,
    obligationId: 1,
    description:
      "Daily reconciliation report for June 2026, signed off by Finance Head. Zero variance across 30/30 trading days.",
    submittedAt: "2026-06-29T10:12:00Z",
  },
  {
    id: 2,
    obligationId: 3,
    description:
      "Board resolution dated 2026-01-15 appointing Ms. R. Sharma as Compliance Officer; NISM certification attached.",
    submittedAt: "2026-01-16T09:00:00Z",
  },
];

export const INITIAL_AUDIT_LOG = [
  {
    id: 1,
    action: "Circular ingested",
    detail: `"${CIRCULAR.name}" uploaded and parsed (${CIRCULAR.pages} pages).`,
    timestamp: "2026-06-01T08:00:00Z",
  },
  {
    id: 2,
    action: "Obligations extracted",
    detail: "7 obligations extracted for intermediary: Stock Broker.",
    timestamp: "2026-06-01T08:02:14Z",
  },
  {
    id: 3,
    action: "Evidence added",
    detail: "Evidence attached to obligation #1 (segregated client funds).",
    timestamp: "2026-06-29T10:12:00Z",
  },
  {
    id: 4,
    action: "Evidence added",
    detail: "Evidence attached to obligation #3 (Compliance Officer appointment).",
    timestamp: "2026-01-16T09:00:00Z",
  },
  {
    id: 5,
    action: "Gap check run",
    detail: "2 obligations flagged overdue: #2 (margin reporting), #7 (KYC re-verification).",
    timestamp: "2026-07-02T06:00:00Z",
  },
];

export const HOW_IT_WORKS = [
  {
    step: "1. Ingest",
    title: "Upload the circular",
    text: "A SEBI circular PDF is parsed into text and split into overlapping chunks.",
  },
  {
    step: "2. Retrieve",
    title: "Embed + search",
    text: "Chunks are embedded and stored in a vector database so relevant text can be retrieved on demand.",
  },
  {
    step: "3. Extract",
    title: "Structured extraction",
    text: "An LLM reads the retrieved chunks and returns validated, structured obligations — not free text.",
  },
  {
    step: "4. Track",
    title: "Checklist + gaps",
    text: "Each obligation becomes a trackable item. Missing evidence or a passed deadline is flagged as a gap automatically.",
  },
];
