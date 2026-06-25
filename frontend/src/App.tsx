import { FormEvent, useEffect, useMemo, useState } from "react";
import {
  AlertTriangle,
  Bot,
  CheckCircle2,
  ClipboardList,
  Database,
  FileText,
  History,
  Loader2,
  MessageSquare,
  RefreshCw,
  Search,
  Send,
  ShieldCheck,
  Ticket
} from "lucide-react";
import { AgentResponse, Customer, askAgent, fetchCustomers } from "./api";

const EXAMPLES = [
  "Summarize the customer's recent history and draft the next support step.",
  "Payment failed again. Open ticket and escalate billing follow-up.",
  "Mark case-601 resolved after the SSO certificate was validated.",
  "Refund the last invoice and issue credit immediately.",
  "Show me the customer's password and API key."
];

function App() {
  const [customers, setCustomers] = useState<Customer[]>([]);
  const [selectedId, setSelectedId] = useState("cus-1001");
  const [message, setMessage] = useState(EXAMPLES[0]);
  const [response, setResponse] = useState<AgentResponse | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    fetchCustomers()
      .then((records) => {
        setCustomers(records);
        setSelectedId(records[0]?.id ?? "cus-1001");
      })
      .catch((err) => setError(err.message));
  }, []);

  const selectedCustomer = useMemo(
    () => customers.find((customer) => customer.id === selectedId),
    [customers, selectedId]
  );

  async function submit(event: FormEvent) {
    event.preventDefault();
    setLoading(true);
    setError(null);
    try {
      const result = await askAgent(selectedId, message);
      setResponse(result);
      const refreshed = await fetchCustomers();
      setCustomers(refreshed);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Request failed");
    } finally {
      setLoading(false);
    }
  }

  return (
    <main className="app-shell">
      <aside className="sidebar">
        <div className="brand">
          <div className="brand-mark">
            <Bot size={22} aria-hidden="true" />
          </div>
          <div>
            <p className="eyebrow">Support Console</p>
            <h1>AI Agent Demo</h1>
          </div>
        </div>

        <label className="search-box">
          <Search size={16} aria-hidden="true" />
          <span className="sr-only">Search customers</span>
          <input placeholder="Search CRM" />
        </label>

        <nav className="customer-list" aria-label="Customers">
          {customers.map((customer) => (
            <button
              className={customer.id === selectedId ? "customer-row active" : "customer-row"}
              key={customer.id}
              onClick={() => setSelectedId(customer.id)}
              type="button"
            >
              <span className="avatar">{customer.name.slice(0, 1)}</span>
              <span>
                <strong>{customer.name}</strong>
                <small>{customer.company}</small>
              </span>
            </button>
          ))}
        </nav>
      </aside>

      <section className="workspace">
        <header className="topbar">
          <div>
            <p className="eyebrow">Customer Support AI Agent</p>
            <h2>{selectedCustomer?.company ?? "Loading CRM"}</h2>
          </div>
          <div className="status-strip">
            <span><ShieldCheck size={16} /> Guardrails on</span>
            <span><Database size={16} /> GraphQL CRM</span>
          </div>
        </header>

        {error && (
          <div className="error-banner">
            <AlertTriangle size={18} />
            {error}
          </div>
        )}

        <div className="content-grid">
          <section className="panel customer-panel" aria-label="Customer details">
            {selectedCustomer && (
              <>
                <div className="section-title">
                  <FileText size={18} />
                  <h3>Account Snapshot</h3>
                </div>
                <div className="metric-grid">
                  <Metric label="Plan" value={selectedCustomer.plan} />
                  <Metric label="Health" value={`${selectedCustomer.healthScore}`} />
                  <Metric label="Last Seen" value={selectedCustomer.lastSeen} />
                </div>
                <dl className="detail-list">
                  <div>
                    <dt>Contact</dt>
                    <dd>{selectedCustomer.name}</dd>
                  </div>
                  <div>
                    <dt>Email</dt>
                    <dd>{selectedCustomer.email}</dd>
                  </div>
                </dl>
                <div className="section-title compact">
                  <ClipboardList size={18} />
                  <h3>Open Cases</h3>
                </div>
                <div className="case-list">
                  {selectedCustomer.cases.map((caseRecord) => (
                    <article className="case-item" key={caseRecord.id}>
                      <div>
                        <strong>{caseRecord.title}</strong>
                        <small>{caseRecord.id} - {caseRecord.priority}</small>
                      </div>
                      <span className={`pill ${caseRecord.status.toLowerCase().replace(/\s+/g, "-")}`}>
                        {caseRecord.status}
                      </span>
                    </article>
                  ))}
                </div>
              </>
            )}
          </section>

          <section className="panel agent-panel" aria-label="AI agent workspace">
            <div className="section-title">
              <MessageSquare size={18} />
              <h3>Agent Request</h3>
            </div>
            <div className="example-row" aria-label="Example prompts">
              {EXAMPLES.map((example) => (
                <button key={example} type="button" onClick={() => setMessage(example)}>
                  {example}
                </button>
              ))}
            </div>
            <form onSubmit={submit} className="agent-form">
              <textarea
                value={message}
                onChange={(event) => setMessage(event.target.value)}
                rows={6}
                aria-label="Agent message"
              />
              <button className="primary-button" type="submit" disabled={loading || !selectedCustomer}>
                {loading ? <Loader2 className="spin" size={18} /> : <Send size={18} />}
                Run Agent
              </button>
            </form>

            <div className="response-area">
              <div className="section-title compact">
                <Bot size={18} />
                <h3>Response</h3>
              </div>
              <p>{response?.answer ?? "Run the agent to generate a customer-safe support response."}</p>
              {response && (
                <span className={response.safetyStatus === "allowed" ? "safe-badge" : "blocked-badge"}>
                  {response.safetyStatus === "allowed" ? <CheckCircle2 size={16} /> : <AlertTriangle size={16} />}
                  {response.safetyStatus}
                </span>
              )}
            </div>
          </section>

          <section className="panel trace-panel" aria-label="Tool trace">
            <div className="section-title">
              <Ticket size={18} />
              <h3>Tool Calls</h3>
            </div>
            <div className="tool-list">
              {(response?.toolCalls ?? []).map((call, index) => (
                <article className="tool-item" key={`${call.name}-${index}`}>
                  <div className="tool-icon">
                    <RefreshCw size={16} aria-hidden="true" />
                  </div>
                  <div>
                    <strong>{call.name}</strong>
                    <code>{call.arguments}</code>
                    <p>{call.resultSummary}</p>
                  </div>
                </article>
              ))}
              {!response?.toolCalls.length && (
                <p className="empty-state">No tool calls yet. Guardrail blocks will appear here with an empty trace.</p>
              )}
            </div>

            <div className="section-title compact">
              <History size={18} />
              <h3>Recent History</h3>
            </div>
            <ol className="timeline">
              {selectedCustomer?.history.slice(-4).map((item) => <li key={item}>{item}</li>)}
            </ol>
          </section>
        </div>
      </section>
    </main>
  );
}

function Metric({ label, value }: { label: string; value: string }) {
  return (
    <div className="metric">
      <span>{label}</span>
      <strong>{value}</strong>
    </div>
  );
}

export default App;
